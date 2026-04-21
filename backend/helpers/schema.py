"""
SQLAlchemy schema for the AFO agent application.

Tables:
    - emails                : inbound emails (sender, subject, body, attachments)
    - documents             : parsed document records per attachment, linked to email
    - langgraph_checkpoints : managed by langgraph-checkpoint-postgres (not defined here)
    - users                 : application users (username, email, password hash)
    - gmail_tokens          : OAuth tokens for Gmail access
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ── enums ─────────────────────────────────────────────────────────────────────


class DocumentType(str, Enum):
    invoice = "invoice"
    capital_call = "capital_call"
    unknown = "unknown"


class DocumentStatus(str, Enum):
    received = "received"
    processing = "processing"
    classified = "classified"
    extracted = "extracted"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"
    failed = "failed"
    needs_attention = "needs_attention"


# ── email ─────────────────────────────────────────────────────────────────────


class EmailORM(Base):
    """
    One row per inbound email from Gmail.

    agent_queued: False until the agent worker picks it up and creates DocumentORM rows.
                  Set to True after the agent worker dispatches all attachments.
    """
    __tablename__ = "emails"

    id = Column(String, primary_key=True, default=_uuid)
    gmail_message_id = Column(String, unique=True, index=True)  # Gmail msg ID for dedup
    sender_email = Column(String, nullable=False, index=True)
    subject = Column(String)
    body = Column(Text)
    # list of dicts: [{"name": ..., "path": ..., "mime": ..., "size": ...}]
    attachments = Column(JSONB, default=list, nullable=False)
    agent_queued = Column(Boolean, default=False, nullable=False, index=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    documents = relationship("DocumentORM", back_populates="email", cascade="all, delete-orphan")


# ── document ──────────────────────────────────────────────────────────────────


class   DocumentORM(Base):
    """
    One row per attachment on an email.
    Linked to EmailORM via email_id (many documents : one email).
    thread_id maps to a LangGraph checkpoint thread for HITL state persistence.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    email_id = Column(String, ForeignKey("emails.id", ondelete="SET NULL"), nullable=True, index=True)
    thread_id = Column(String, unique=True, index=True)  # LangGraph checkpoint thread_id (= doc id)

    # extracted fields (populated after agent runs)
    document_type = Column(SAEnum(DocumentType), default=DocumentType.unknown, nullable=False, index=True)
    fund_name = Column(String, index=True)
    amount = Column(Float)
    currency = Column(String(3))
    due_date = Column(DateTime)

    status = Column(SAEnum(DocumentStatus), default=DocumentStatus.received, nullable=False, index=True)

    filename = Column(String)
    file_path = Column(String)  # local path or cloud URL to the raw attachment
    agent_reasoning = Column(Text)
    extra_metadata = Column(JSONB, default=dict)
    state_history = Column(JSONB, default=list)
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    review_note = Column(Text)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    email = relationship("EmailORM", back_populates="documents")


# ── user ──────────────────────────────────────────────────────────────────────


class UserORM(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=_uuid)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ── gmail tokens ──────────────────────────────────────────────────────────────


class GmailTokenORM(Base):
    __tablename__ = "gmail_tokens"

    id = Column(String, primary_key=True, default=_uuid)
    account_email = Column(String, nullable=False, unique=True, index=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_expiry = Column(DateTime)
    last_poll_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
