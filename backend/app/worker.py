"""
Background polling worker for Gmail email ingestion.
Runs periodically to fetch new emails and create documents.
"""

import asyncio
import base64
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
import logging

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import DocumentORM, DocumentState, GmailTokenORM
from app.agent import start_agent_run
from app.gmail import build_service, fetch_new_messages
from app.settings import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

POLL_INTERVAL_SECONDS = settings.poll_interval_seconds


class GmailPollingWorker:
    def __init__(self, interval: int = POLL_INTERVAL_SECONDS):
        self.interval = interval
        self.running = False

    async def poll_once(self, db: Session) -> None:
        """
        Poll Gmail for new messages and create documents from them.
        """
        try:
            token_record = db.query(GmailTokenORM).first()
            if not token_record:
                logger.debug("No Gmail token configured, skipping poll")
                return

            since = token_record.last_poll_at or (datetime.utcnow() - timedelta(hours=1))

            service = build_service(
                access_token=token_record.access_token,
                refresh_token=token_record.refresh_token,
            )

            messages = await fetch_new_messages(service, since_timestamp=since)

            for msg in messages:
                existing = db.query(DocumentORM).filter(
                    DocumentORM.gmail_message_id == msg['id']
                ).first()
                if existing:
                    logger.debug(f"Message {msg['id']} already processed, skipping")
                    continue

                doc_id = str(uuid4())
                sender = msg['sender'].split('<')[-1].rstrip('>') if '<' in msg['sender'] else msg['sender']

                for attachment in msg.get('attachments', []):
                    attach_id = str(uuid4())
                    filename = attachment['name']
                    dest = UPLOAD_DIR / f"{attach_id}_{filename}"

                    try:
                        attach_data = attachment.get('data', '')
                        if attach_data:
                            data = base64.urlsafe_b64decode(attach_data)
                            dest.write_bytes(data)
                        else:
                            dest.write_text(msg['body'] or f"Email: {msg['subject']}")
                    except Exception as e:
                        logger.error(f"Error saving attachment {filename}: {e}")
                        continue

                    doc = DocumentORM(
                        id=doc_id,
                        thread_id=doc_id,
                        gmail_message_id=msg['id'],
                        filename=filename,
                        sender_email=sender,
                        subject=msg['subject'],
                        file_path=str(dest),
                        state=DocumentState.received,
                        state_history=[],
                    )
                    db.add(doc)
                    db.commit()
                    db.refresh(doc)

                    logger.info(f"Created document {doc_id} from email {msg['id']}")

                    try:
                        text = dest.read_text(errors='ignore')
                        await start_agent_run(doc_id, text)
                        logger.info(f"Started agent for document {doc_id}")
                    except Exception as e:
                        logger.error(f"Error starting agent for {doc_id}: {e}")

            token_record.last_poll_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.error(f"Poll error: {e}")

    async def run(self) -> None:
        """
        Run the polling loop continuously.
        """
        self.running = True
        logger.info(f"Gmail polling worker started (interval: {self.interval}s)")

        while self.running:
            try:
                db = SessionLocal()
                await self.poll_once(db)
                db.close()
            except Exception as e:
                logger.error(f"Unexpected error in polling loop: {e}")

            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        self.running = False
        logger.info("Gmail polling worker stopped")


worker = GmailPollingWorker()
