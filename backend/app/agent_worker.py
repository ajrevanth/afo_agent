"""
Agent dispatch worker.

Responsibility: poll the emails table for rows where agent_queued=False,
create a DocumentORM per attachment, and start a LangGraph thread for each.

After dispatching all documents for an email, sets email.agent_queued=True.
Documents in status=pending_review then wait for the human review API.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.database import SessionLocal
from app.agent import start_agent_run
from app.settings import settings
from helpers.schema import DocumentORM, DocumentStatus, DocumentType, EmailORM

logger = logging.getLogger(__name__)

AGENT_POLL_INTERVAL = settings.agent_poll_interval_seconds


def _extract_text(path: Path, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            pages = PdfReader(str(path)).pages
            text = "\n".join(p.extract_text() or "" for p in pages)
            logger.debug(f"_extract_text: pdf filename={filename!r} pages={len(pages)} chars={len(text)}")
            return text
        except Exception as exc:
            logger.warning(f"_extract_text: PDF extraction failed filename={filename!r} error={exc}")
            return ""
    try:
        text = path.read_text(errors="ignore")
        logger.debug(f"_extract_text: text filename={filename!r} chars={len(text)}")
        return text
    except Exception as exc:
        logger.warning(f"_extract_text: read failed filename={filename!r} error={exc}")
        return ""


class AgentDispatchWorker:
    def __init__(self, interval: int = AGENT_POLL_INTERVAL):
        self.interval = interval
        self.running = False

    async def poll_once(self) -> None:
        db = SessionLocal()
        try:
            # Grab emails not yet handed to the agent (batch of 10)
            pending = (
                db.query(EmailORM)
                .filter(EmailORM.agent_queued == False)
                .order_by(EmailORM.received_at)
                .limit(10)
                .all()
            )

            if pending:
                logger.info(f"poll_once: found {len(pending)} pending email(s) to dispatch")

            for email in pending:
                attachments = email.attachments or []

                if not attachments:
                    email.agent_queued = True
                    db.commit()
                    logger.info(f"poll_once: email_id={email.id} has no attachments, marking queued")
                    continue

                logger.info(f"poll_once: email_id={email.id} processing {len(attachments)} attachment(s)")

                for attach in attachments:
                    doc_id = str(uuid4())
                    file_path = Path(attach["path"]) if attach.get("path") else None

                    text = ""
                    if file_path and file_path.exists():
                        text = _extract_text(file_path, attach["name"])
                    elif file_path:
                        logger.warning(f"poll_once: attachment file not found path={file_path} email_id={email.id}")

                    doc = DocumentORM(
                        id=doc_id,
                        email_id=email.id,
                        thread_id=doc_id,
                        filename=attach["name"],
                        file_path=str(file_path) if file_path else None,
                        status=DocumentStatus.processing,
                        state_history=[{
                            "from_state": "received",
                            "to_state": "processing",
                            "actor": "agent_worker",
                            "timestamp": datetime.utcnow().isoformat(),
                        }],
                    )
                    db.add(doc)
                    db.commit()
                    db.refresh(doc)

                    logger.info(
                        f"poll_once: created doc_id={doc_id} email_id={email.id} "
                        f"filename={attach['name']!r} text_len={len(text)}"
                    )

                    # Run agent asynchronously — don't block the poll loop
                    asyncio.create_task(
                        _run_agent_for_doc(doc_id, text, email.id)
                    )

                email.agent_queued = True
                db.commit()
                logger.info(f"poll_once: email_id={email.id} marked agent_queued=True")

        except Exception as e:
            logger.error(f"poll_once: dispatch error: {e}", exc_info=True)
        finally:
            db.close()

    async def run(self) -> None:
        self.running = True
        logger.info(f"Agent dispatch worker started (interval: {self.interval}s)")
        while self.running:
            await self.poll_once()
            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        self.running = False


async def _run_agent_for_doc(doc_id: str, text: str, email_id: str) -> None:
    """Run LangGraph and update document status based on result."""
    db = SessionLocal()
    try:
        doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
        if not doc:
            logger.warning(f"_run_agent_for_doc: doc_id={doc_id} not found in DB, skipping")
            return

        if not text.strip():
            logger.warning(f"_run_agent_for_doc: doc_id={doc_id} has no extractable text → needs_attention")
            doc.status = DocumentStatus.needs_attention
            doc.error_message = "No extractable text in attachment."
            _push_history(doc, "processing", "needs_attention", "agent")
            doc.updated_at = datetime.utcnow()
            db.commit()
            return

        logger.info(f"_run_agent_for_doc: starting agent doc_id={doc_id} text_len={len(text)}")
        result = await start_agent_run(doc_id, text)

        if result.get("error"):
            logger.error(f"_run_agent_for_doc: agent error doc_id={doc_id} error={result['error']!r}")
            doc.status = DocumentStatus.failed
            doc.error_message = result["error"]
            _push_history(doc, "processing", "failed", "agent", result["error"])
        else:
            doc.document_type = result.get("document_type", "unknown")
            doc.agent_reasoning = result.get("reasoning", "")
            meta = result.get("metadata") or {}
            doc.fund_name = meta.get("fund_name")
            doc.amount = meta.get("amount")
            doc.currency = meta.get("currency")
            raw_due = meta.get("due_date")
            if raw_due:
                try:
                    from datetime import date
                    doc.due_date = datetime.fromisoformat(raw_due)
                except ValueError:
                    logger.warning(f"_run_agent_for_doc: invalid due_date format doc_id={doc_id} raw={raw_due!r}")
            doc.extra_metadata = meta
            if doc.document_type == DocumentType.unknown:
                doc.status = DocumentStatus.completed
                logger.info(f"_run_agent_for_doc: doc_id={doc_id} classified as unknown → completed")
                _push_history(doc, "processing", "completed", "AI Agent", "Document not recognized as invoice or capital call")
            else:
                doc.status = DocumentStatus.pending_review
                logger.info(
                    f"_run_agent_for_doc: doc_id={doc_id} document_type={doc.document_type} "
                    f"fund_name={doc.fund_name!r} amount={doc.amount} currency={doc.currency} "
                    f"due_date={raw_due} → pending_review"
                )
                _push_history(doc, "processing", "pending_review", "AI Agent", "Awaiting human review")

        doc.updated_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"_run_agent_for_doc: exception doc_id={doc_id} error={e}", exc_info=True)
        try:
            doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
            if doc:
                doc.status = DocumentStatus.failed
                doc.error_message = str(e)
                _push_history(doc, doc.status.value, "failed", "agent", str(e))
                doc.updated_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _push_history(doc: DocumentORM, from_s: str, to_s: str, actor: str, note: str = None):
    history = list(doc.state_history or [])
    history.append({
        "from_state": from_s,
        "to_state": to_s,
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
        "note": note,
    })
    doc.state_history = history


agent_worker = AgentDispatchWorker()
