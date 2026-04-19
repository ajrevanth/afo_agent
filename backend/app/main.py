import asyncio
import os
import shutil
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db, init_db
from app.models import (
    DocumentORM, DocumentState, DocumentType,
    DocumentOut, MockEmailPayload, ReviewPayload, DashboardStats, ExtractedMetadata,
)
from app.agent import run_agent

UPLOAD_DIR = Path("/tmp/afo_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AFO Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ── helpers ───────────────────────────────────────────────────────────────────

def extract_text_from_file(path: Path, filename: str) -> str:
    if filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception:
            return f"[PDF: {filename} — could not extract text]"
    if filename.endswith(".txt"):
        return path.read_text(errors="ignore")
    return f"[Attachment: {filename}]"


def push_history(doc: DocumentORM, from_state: str, to_state: str, actor: str, note: str | None = None):
    history = list(doc.state_history or [])
    history.append({
        "from_state": from_state,
        "to_state": to_state,
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
        "note": note,
    })
    doc.state_history = history


def is_urgent(due_date_str: str | None) -> bool:
    if not due_date_str:
        return False
    try:
        due = date.fromisoformat(due_date_str)
        return (due - date.today()).days <= 3
    except ValueError:
        return False


async def process_document(doc_id: str, file_path: Path, filename: str):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
        if not doc:
            return

        prev = doc.state.value
        doc.state = DocumentState.processing
        doc.updated_at = datetime.utcnow()
        push_history(doc, prev, "processing", "agent")
        db.commit()

        text = extract_text_from_file(file_path, filename)

        if not text.strip() or text.startswith("["):
            doc.state = DocumentState.needs_attention
            doc.agent_reasoning = "Could not extract readable text from the attachment. Manual review required."
            push_history(doc, "processing", "needs_attention", "agent", "No extractable text")
            doc.updated_at = datetime.utcnow()
            db.commit()
            return

        doc.state = DocumentState.classified
        push_history(doc, "processing", "classified", "agent")
        db.commit()

        result = await run_agent(doc_id, text)

        doc.document_type = DocumentType(result.get("document_type", "unknown"))
        doc.agent_reasoning = result.get("reasoning", "")
        doc.state = DocumentState.extracted
        push_history(doc, "classified", "extracted", "agent")
        db.commit()

        if result.get("metadata"):
            doc.metadata_ = result["metadata"]

        doc.state = DocumentState.pending_review
        push_history(doc, "extracted", "pending_review", "agent", "Awaiting human verification")
        doc.updated_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
        if doc:
            push_history(doc, doc.state.value, "failed", "agent", str(e))
            doc.state = DocumentState.failed
            doc.error_message = str(e)
            doc.updated_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/api/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(DocumentORM.id)).scalar() or 0

    by_state_rows = db.query(DocumentORM.state, func.count(DocumentORM.id)).group_by(DocumentORM.state).all()
    by_state = {s.value: 0 for s in DocumentState}
    for state, count in by_state_rows:
        by_state[state.value] = count

    by_type_rows = db.query(DocumentORM.document_type, func.count(DocumentORM.id)).group_by(DocumentORM.document_type).all()
    by_type = {t.value: 0 for t in DocumentType}
    for dtype, count in by_type_rows:
        if dtype:
            by_type[dtype.value] = count

    today = date.today()
    completed_today = db.query(func.count(DocumentORM.id)).filter(
        DocumentORM.state.in_([DocumentState.approved, DocumentState.completed]),
        func.date(DocumentORM.updated_at) == today,
    ).scalar() or 0

    failed_today = db.query(func.count(DocumentORM.id)).filter(
        DocumentORM.state == DocumentState.failed,
        func.date(DocumentORM.updated_at) == today,
    ).scalar() or 0

    pending_review_count = by_state.get("pending_review", 0) + by_state.get("needs_attention", 0)

    urgent_docs = db.query(DocumentORM).filter(
        DocumentORM.state == DocumentState.pending_review,
        DocumentORM.document_type == DocumentType.capital_call,
    ).all()
    urgent_count = sum(1 for d in urgent_docs if is_urgent(d.metadata_ and d.metadata_.get("due_date")))

    return DashboardStats(
        total=total,
        by_state=by_state,
        by_type=by_type,
        completed_today=completed_today,
        failed_today=failed_today,
        pending_review_count=pending_review_count,
        urgent_count=urgent_count,
    )


@app.get("/api/documents", response_model=list[DocumentOut])
def list_documents(
    state: Optional[str] = None,
    document_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(DocumentORM)
    if state:
        q = q.filter(DocumentORM.state == state)
    if document_type:
        q = q.filter(DocumentORM.document_type == document_type)
    if search:
        q = q.filter(
            DocumentORM.filename.ilike(f"%{search}%") |
            DocumentORM.sender_email.ilike(f"%{search}%")
        )
    return [_to_out(d) for d in q.order_by(DocumentORM.updated_at.desc()).limit(limit).all()]


@app.get("/api/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Not found")
    return _to_out(doc)


@app.get("/api/documents/{doc_id}/file")
def get_document_file(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc or not doc.file_path:
        raise HTTPException(404, "File not found")
    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(404, "File not on disk")
    media = "application/pdf" if doc.filename.endswith(".pdf") else "image/png"
    return FileResponse(str(path), media_type=media, filename=doc.filename)


@app.post("/api/documents/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    doc_id = str(uuid.uuid4())
    dest = UPLOAD_DIR / f"{doc_id}_{file.filename}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = DocumentORM(id=doc_id, filename=file.filename, file_path=str(dest), state_history=[])
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document, doc_id, dest, file.filename)
    return _to_out(doc)


@app.post("/api/documents/mock-email", response_model=DocumentOut)
async def mock_email(
    payload: MockEmailPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    doc_id = str(uuid.uuid4())
    fake_path = UPLOAD_DIR / f"{doc_id}_{payload.attachment_name}.txt"
    fake_path.write_text(f"Subject: {payload.subject}\n\n{payload.body}")

    doc = DocumentORM(
        id=doc_id,
        filename=payload.attachment_name,
        sender_email=payload.sender,
        subject=payload.subject,
        file_path=str(fake_path),
        state_history=[],
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document, doc_id, fake_path, payload.attachment_name)
    return _to_out(doc)


@app.post("/api/documents/{doc_id}/review", response_model=DocumentOut)
def review_document(
    doc_id: str,
    payload: ReviewPayload,
    db: Session = Depends(get_db),
):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Not found")
    if doc.state not in (DocumentState.pending_review, DocumentState.needs_attention):
        raise HTTPException(400, f"Document is in state '{doc.state.value}', not reviewable")

    new_state = DocumentState.approved if payload.action == "approve" else DocumentState.rejected

    if payload.action == "approve" and payload.overrides:
        existing = dict(doc.metadata_ or {})
        existing.update({k: v for k, v in payload.overrides.items() if v is not None})
        doc.metadata_ = existing

    push_history(doc, doc.state.value, new_state.value, payload.reviewer_name, payload.note)
    doc.state = new_state
    doc.reviewed_by = payload.reviewer_name
    doc.reviewed_at = datetime.utcnow()
    doc.review_note = payload.note
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return _to_out(doc)


@app.post("/api/documents/{doc_id}/retry", response_model=DocumentOut)
async def retry_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    doc = db.query(DocumentORM).filter(DocumentORM.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Not found")
    if doc.state not in (DocumentState.failed, DocumentState.needs_attention):
        raise HTTPException(400, "Only failed or needs_attention documents can be retried")

    push_history(doc, doc.state.value, "received", "system", "Manual retry triggered")
    doc.state = DocumentState.received
    doc.error_message = None
    doc.updated_at = datetime.utcnow()
    db.commit()

    background_tasks.add_task(process_document, doc_id, Path(doc.file_path), doc.filename)
    return _to_out(doc)


# ── serialization ─────────────────────────────────────────────────────────────

def _to_out(doc: DocumentORM) -> DocumentOut:
    metadata = ExtractedMetadata(**doc.metadata_) if doc.metadata_ else None
    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        sender_email=doc.sender_email,
        subject=doc.subject,
        state=doc.state,
        document_type=doc.document_type,
        metadata=metadata,
        agent_reasoning=doc.agent_reasoning,
        state_history=doc.state_history or [],
        reviewed_by=doc.reviewed_by,
        reviewed_at=doc.reviewed_at,
        review_note=doc.review_note,
        error_message=doc.error_message,
        created_at=doc.created_at or datetime.utcnow(),
        updated_at=doc.updated_at or datetime.utcnow(),
    )
