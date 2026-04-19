from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
import uuid


class DocumentState(str, Enum):
    received = "received"
    processing = "processing"
    classified = "classified"
    extracted = "extracted"
    pending_review = "pending_review"   # waiting for human
    approved = "approved"               # human approved
    rejected = "rejected"               # human rejected
    completed = "completed"             # fully done
    failed = "failed"                   # agent error
    needs_attention = "needs_attention" # agent flagged, needs manual entry


class DocumentType(str, Enum):
    invoice = "invoice"
    capital_call = "capital_call"
    unknown = "unknown"


class Base(DeclarativeBase):
    pass


class DocumentORM(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    sender_email = Column(String)
    subject = Column(String)
    state = Column(SAEnum(DocumentState), default=DocumentState.received, nullable=False)
    document_type = Column(SAEnum(DocumentType))
    metadata_ = Column("metadata", JSONB)
    agent_reasoning = Column(Text)
    state_history = Column(JSONB, default=list)  # list of StateTransition dicts
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    review_note = Column(Text)
    error_message = Column(Text)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ExtractedMetadata(BaseModel):
    fund_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    due_date: Optional[str] = None
    confidence: Optional[float] = None


class StateTransition(BaseModel):
    from_state: str
    to_state: str
    actor: str
    timestamp: str
    note: Optional[str] = None


class DocumentOut(BaseModel):
    id: str
    filename: str
    sender_email: Optional[str] = None
    subject: Optional[str] = None
    state: DocumentState
    document_type: Optional[DocumentType] = None
    metadata: Optional[ExtractedMetadata] = None
    agent_reasoning: Optional[str] = None
    state_history: Optional[list] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MockEmailPayload(BaseModel):
    sender: str
    subject: str
    body: str
    attachment_name: str
    attachment_type: str


class ReviewPayload(BaseModel):
    action: str          # "approve" | "reject"
    reviewer_name: str
    note: Optional[str] = None
    overrides: Optional[dict] = None


class DashboardStats(BaseModel):
    total: int
    by_state: dict
    by_type: dict
    completed_today: int
    failed_today: int
    pending_review_count: int
    urgent_count: int
