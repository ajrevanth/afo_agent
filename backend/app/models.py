"""
Pydantic request/response models for the FastAPI layer.
SQLAlchemy ORM models live in helpers/schema.py.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, model_validator, field_validator

from helpers.schema import DocumentType, DocumentStatus


# ── response schemas ──────────────────────────────────────────────────────────

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
    email_id: Optional[str] = None
    filename: Optional[str] = None
    status: DocumentStatus
    document_type: DocumentType
    fund_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    due_date: Optional[datetime] = None
    extra_metadata: Optional[dict] = None
    agent_reasoning: Optional[str] = None
    state_history: Optional[list] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Computed for frontend compatibility
    state: Optional[str] = None
    metadata: Optional[dict] = None

    model_config = {"from_attributes": True}

    @field_validator("metadata", mode="before")
    @classmethod
    def coerce_metadata(cls, v):
        """Discard SQLAlchemy's class-level MetaData() object — only accept dicts."""
        return v if isinstance(v, dict) else None

    @model_validator(mode="after")
    def populate_computed(self):
        self.state = self.status.value if self.status else None
        if self.metadata is None:
            md: dict = {}
            if self.fund_name is not None:
                md["fund_name"] = self.fund_name
            if self.amount is not None:
                md["amount"] = self.amount
            if self.currency is not None:
                md["currency"] = self.currency
            if self.due_date is not None:
                md["due_date"] = self.due_date.date().isoformat()
            self.metadata = md if md else None
        return self


class EmailOut(BaseModel):
    id: str
    gmail_message_id: Optional[str] = None
    sender_email: str
    subject: Optional[str] = None
    body: Optional[str] = None
    attachments: list = []
    agent_queued: bool = False
    received_at: datetime
    documents: list[DocumentOut] = []

    model_config = {"from_attributes": True}


# ── request schemas ───────────────────────────────────────────────────────────

class ReviewPayload(BaseModel):
    action: str              # "approve" | "reject"
    reviewer_name: str
    note: Optional[str] = None
    overrides: Optional[dict] = None


class DashboardStats(BaseModel):
    total: int
    by_state: dict
    by_type: dict
    approved: int
    failed_today: int
    pending_review_count: int
    urgent_count: int
