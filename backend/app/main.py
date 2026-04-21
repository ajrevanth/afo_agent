import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db, init_db
from app.models import (
    DocumentOut, EmailOut, ReviewPayload, DashboardStats,
)
from app.agent import initialize_graph, resume_agent_run, shutdown_graph
from app.gmail import get_oauth_url, exchange_code
from app.email_worker import email_worker
from app.agent_worker import agent_worker, _run_agent_for_doc, _push_history
from app.settings import settings
from helpers.schema import DocumentORM, DocumentStatus, DocumentType, EmailORM, GmailTokenORM

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    await initialize_graph()
    asyncio.create_task(email_worker.run())
    asyncio.create_task(agent_worker.run())
    yield
    await shutdown_graph()


app = FastAPI(title="AFO Agent API", version="2.0.0", lifespan=lifespan)

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ───────────────────────────────────────────────────────────────────

def extract_text_from_file(path: Path, filename: str) -> str:
    if filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(str(path)).pages)
        except Exception:
            return f"[PDF: {filename} — could not extract text]"
    if filename.endswith(".txt"):
        return path.read_text(errors="ignore")
    return f"[Attachment: {filename}]"


def is_urgent(due_date: datetime | None) -> bool:
    if not due_date:
        return False
    return (due_date.date() - date.today()).days <= 3


# ── stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    KNOWN_TYPES = [DocumentType.invoice, DocumentType.capital_call]

    total = db.query(func.count(DocumentORM.id)).filter(
        DocumentORM.document_type.in_(KNOWN_TYPES)
    ).scalar() or 0

    by_status_rows = (
        db.query(DocumentORM.status, func.count(DocumentORM.id))
        .filter(DocumentORM.document_type.in_(KNOWN_TYPES))
        .group_by(DocumentORM.status)
        .all()
    )
    by_state = {s.value: 0 for s in DocumentStatus}
    for status, count in by_status_rows:
        by_state[status.value] = count

    by_type_rows = (
        db.query(DocumentORM.document_type, func.count(DocumentORM.id))
        .filter(DocumentORM.document_type.in_(KNOWN_TYPES))
        .group_by(DocumentORM.document_type)
        .all()
    )
    by_type = {t.value: 0 for t in DocumentType}
    for dtype, count in by_type_rows:
        if dtype:
            by_type[dtype.value] = count

    today = date.today()
    approved = db.query(func.count(DocumentORM.id)).filter(
        DocumentORM.document_type.in_(KNOWN_TYPES),
        DocumentORM.status.in_([DocumentStatus.approved, DocumentStatus.completed]),
    ).scalar() or 0

    failed_today = db.query(func.count(DocumentORM.id)).filter(
        DocumentORM.document_type.in_(KNOWN_TYPES),
        DocumentORM.status == DocumentStatus.failed,
        func.date(DocumentORM.updated_at) == today,
    ).scalar() or 0

    pending_review_count = (
        by_state.get("pending_review", 0) + by_state.get("needs_attention", 0)
    )

    urgent_docs = db.query(DocumentORM).filter(
        DocumentORM.status == DocumentStatus.pending_review,
        DocumentORM.document_type == DocumentType.capital_call,
    ).all()
    urgent_count = sum(1 for d in urgent_docs if is_urgent(d.due_date))

    return DashboardStats(
        total=total,
        by_state=by_state,
        by_type=by_type,
        approved=approved,
        failed_today=failed_today,
        pending_review_count=pending_review_count,
        urgent_count=urgent_count,
    )


# ── documents ─────────────────────────────────────────────────────────────────

@app.get("/api/documents", response_model=list[DocumentOut])
def list_documents(
    status: Optional[str] = None,
    state: Optional[str] = None,
    document_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    KNOWN_TYPES = [DocumentType.invoice, DocumentType.capital_call]
    q = db.query(DocumentORM).filter(DocumentORM.document_type.in_(KNOWN_TYPES))
    effective_status = state or status
    if effective_status:
        q = q.filter(DocumentORM.status == effective_status)
    if document_type:
        q = q.filter(DocumentORM.document_type == document_type)
    if search:
        q = q.filter(DocumentORM.filename.ilike(f"%{search}%"))
    return q.order_by(DocumentORM.updated_at.desc()).limit(limit).all()


@app.get("/api/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Not found")
    return doc


@app.get("/api/documents/{doc_id}/file")
def get_document_file(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc or not doc.file_path:
        raise HTTPException(404, "File not found")
    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(404, "File not on disk")
    media = "application/pdf" if (doc.filename or "").endswith(".pdf") else "image/png"
    return FileResponse(
        str(path),
        media_type=media,
        filename=doc.filename,
        headers={"Content-Disposition": f"inline; filename={doc.filename}"},
    )


@app.post("/api/documents/{doc_id}/review", response_model=DocumentOut)
async def review_document(
    doc_id: str,
    payload: ReviewPayload,
    db: Session = Depends(get_db),
):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Not found")
    if doc.status not in (DocumentStatus.pending_review, DocumentStatus.needs_attention):
        raise HTTPException(400, f"Document is in status '{doc.status.value}', not reviewable")

    new_status = DocumentStatus.approved if payload.action == "approve" else DocumentStatus.rejected

    if payload.action == "approve" and payload.overrides:
        overrides = payload.overrides
        if overrides.get("fund_name"):
            doc.fund_name = overrides["fund_name"]
        if overrides.get("amount") is not None:
            doc.amount = overrides["amount"]
        if overrides.get("currency"):
            doc.currency = overrides["currency"]
        if overrides.get("due_date"):
            try:
                doc.due_date = datetime.fromisoformat(overrides["due_date"])
            except ValueError:
                pass

    _push_history(doc, doc.status.value, new_status.value, payload.reviewer_name, payload.note)
    doc.status = new_status
    doc.reviewed_by = payload.reviewer_name
    doc.reviewed_at = datetime.utcnow()
    doc.review_note = payload.note
    doc.updated_at = datetime.utcnow()
    db.commit()

    # Resume LangGraph so the checkpoint reflects the final human decision
    agent_result = await resume_agent_run(
        document_id=doc_id,
        human_decision=payload.action,
        note=payload.note or "",
        overrides=payload.overrides or {},
    )

    # After graph runs apply_review_node → END, transition approved → completed
    if payload.action == "approve" and not agent_result.get("error"):
        db.refresh(doc)
        _push_history(doc, "approved", "completed", "system", "Processing complete")
        doc.status = DocumentStatus.completed
        doc.updated_at = datetime.utcnow()
        db.commit()

    db.refresh(doc)
    return doc


@app.post("/api/documents/{doc_id}/retry", response_model=DocumentOut)
async def retry_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Not found")
    if doc.status not in (DocumentStatus.failed, DocumentStatus.needs_attention):
        raise HTTPException(400, "Only failed or needs_attention documents can be retried")

    _push_history(doc, doc.status.value, "processing", "system", "Manual retry")
    doc.status = DocumentStatus.processing
    doc.error_message = None
    doc.updated_at = datetime.utcnow()
    db.commit()

    text = extract_text_from_file(Path(doc.file_path), doc.filename) if doc.file_path else ""
    background_tasks.add_task(_run_agent_for_doc, doc_id, text, doc.email_id)
    return doc


# ── emails ────────────────────────────────────────────────────────────────────

@app.get("/api/emails", response_model=list[EmailOut])
def list_emails(
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(EmailORM)
        .order_by(EmailORM.received_at.desc())
        .limit(limit)
        .all()
    )


@app.get("/api/emails/{email_id}", response_model=EmailOut)
def get_email(email_id: str, db: Session = Depends(get_db)):
    email = db.query(EmailORM).filter(EmailORM.id == email_id).first()
    if not email:
        raise HTTPException(404, "Not found")
    return email


# ── Gmail OAuth ───────────────────────────────────────────────────────────────

@app.get("/api/gmail/auth")
def gmail_auth(redirect_uri: Optional[str] = None):
    return {"auth_url": get_oauth_url(redirect_uri or settings.gmail_redirect_uri)}


@app.get("/api/gmail/callback")
def gmail_callback(code: str, db: Session = Depends(get_db)):
    try:
        tokens = exchange_code(
            code=code,
            redirect_uri=settings.gmail_redirect_uri,
        )
        existing = db.query(GmailTokenORM).filter(
            GmailTokenORM.account_email == tokens["email"]
        ).first()
        if existing:
            existing.access_token = tokens["access_token"]
            existing.refresh_token = tokens["refresh_token"]
            existing.token_expiry = tokens["expiry"]
            existing.updated_at = datetime.utcnow()
        else:
            db.add(GmailTokenORM(
                account_email=tokens["email"],
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_expiry=tokens["expiry"],
            ))
        db.commit()
        return {"success": True, "email": tokens["email"]}
    except Exception as e:
        raise HTTPException(400, f"OAuth exchange failed: {e}")


@app.get("/api/gmail/status")
def gmail_status(db: Session = Depends(get_db)):
    token = db.query(GmailTokenORM).first()
    if not token:
        return {"connected": False}
    return {
        "connected": True,
        "email": token.account_email,
        "last_poll": token.last_poll_at.isoformat() if token.last_poll_at else None,
    }
