"""
Email ingest worker.

Responsibility: poll Gmail, create EmailORM rows. Nothing else.
The agent_worker picks up from there.

Poll interval: POLL_INTERVAL_SECONDS (default 60).
"""

import asyncio
import base64
import logging
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.database import SessionLocal
from app.gmail import build_service, fetch_new_messages
from app.settings import settings
from helpers.schema import EmailORM, GmailTokenORM

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

POLL_INTERVAL = settings.poll_interval_seconds


class EmailIngestWorker:
    def __init__(self, interval: int = POLL_INTERVAL):
        self.interval = interval
        self.running = False

    async def poll_once(self) -> None:
        db = SessionLocal()
        try:
            token = db.query(GmailTokenORM).first()
            if not token:
                logger.debug("No Gmail token configured — skipping email poll")
                return

            since = token.last_poll_at or (datetime.utcnow() - timedelta(hours=1))
            logger.info(f"poll_once: fetching emails since={since.isoformat()} account={token.account_email!r}")
            service = build_service(
                access_token=token.access_token,
                refresh_token=token.refresh_token,
            )

            messages = await fetch_new_messages(service, since_timestamp=since)
            logger.info(f"poll_once: received {len(messages)} message(s) from Gmail")

            new_count = 0
            skipped_count = 0
            for msg in messages:
                # Idempotency: skip if already ingested
                if db.query(EmailORM).filter(EmailORM.gmail_message_id == msg["id"]).first():
                    skipped_count += 1
                    continue

                # Save attachments to disk and record their paths
                attachments_meta = []
                for attach in msg.get("attachments", []):
                    attach_id = str(uuid4())
                    filename = attach["name"]
                    dest = UPLOAD_DIR / f"{attach_id}_{filename}"
                    try:
                        raw = attach.get("data", "")
                        dest.write_bytes(base64.urlsafe_b64decode(raw) if raw else b"")
                    except Exception as e:
                        logger.error(f"Failed to save attachment {filename}: {e}")
                        continue
                    attachments_meta.append({
                        "name": filename,
                        "path": str(dest),
                        "mime": attach.get("mime", "application/octet-stream"),
                    })

                sender = (
                    msg["sender"].split("<")[-1].rstrip(">")
                    if "<" in msg["sender"]
                    else msg["sender"]
                )

                email_row = EmailORM(
                    gmail_message_id=msg["id"],
                    sender_email=sender,
                    subject=msg.get("subject", "(no subject)"),
                    body=msg.get("body", ""),
                    attachments=attachments_meta,
                    agent_queued=False,
                    received_at=datetime.utcnow(),
                )
                db.add(email_row)
                new_count += 1
                logger.info(
                    f"poll_once: ingested msg_id={msg['id']} sender={sender!r} "
                    f"subject={msg.get('subject', '')!r} attachments={len(attachments_meta)}"
                )

            db.commit()
            logger.info(f"poll_once: done — new={new_count} skipped={skipped_count}")

            token.last_poll_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.error(f"poll_once: email poll error: {e}", exc_info=True)
        finally:
            db.close()

    async def run(self) -> None:
        self.running = True
        logger.info(f"Email ingest worker started (interval: {self.interval}s)")
        while self.running:
            await self.poll_once()
            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        self.running = False


email_worker = EmailIngestWorker()
