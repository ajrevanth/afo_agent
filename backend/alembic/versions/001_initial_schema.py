"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE IF NOT EXISTS documenttype AS ENUM ('invoice', 'capital_call', 'unknown')")
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documentstatus AS ENUM (
                'received', 'processing', 'classified', 'extracted',
                'pending_review', 'approved', 'rejected', 'completed',
                'failed', 'needs_attention'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documenttype AS ENUM ('invoice', 'capital_call', 'unknown');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$
    """)

    op.create_table(
        "emails",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("gmail_message_id", sa.String(), nullable=True),
        sa.Column("sender_email", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("agent_queued", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emails_gmail_message_id", "emails", ["gmail_message_id"], unique=True)
    op.create_index("ix_emails_sender_email", "emails", ["sender_email"])
    op.create_index("ix_emails_agent_queued", "emails", ["agent_queued"])
    op.create_index("ix_emails_received_at", "emails", ["received_at"])

    op.create_table(
        "documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email_id", sa.String(), nullable=True),
        sa.Column("thread_id", sa.String(), nullable=True),
        sa.Column(
            "document_type",
            postgresql.ENUM("invoice", "capital_call", "unknown", name="documenttype", create_type=False),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("fund_name", sa.String(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "received", "processing", "classified", "extracted",
                "pending_review", "approved", "rejected", "completed",
                "failed", "needs_attention",
                name="documentstatus", create_type=False,
            ),
            nullable=False,
            server_default="received",
        ),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("agent_reasoning", sa.Text(), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("state_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_email_id", "documents", ["email_id"])
    op.create_index("ix_documents_thread_id", "documents", ["thread_id"], unique=True)
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_fund_name", "documents", ["fund_name"])
    op.create_index("ix_documents_status", "documents", ["status"])

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "gmail_tokens",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("account_email", sa.String(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(), nullable=True),
        sa.Column("last_poll_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_email"),
    )
    op.create_index("ix_gmail_tokens_account_email", "gmail_tokens", ["account_email"])


def downgrade() -> None:
    op.drop_table("gmail_tokens")
    op.drop_table("users")
    op.drop_table("documents")
    op.drop_table("emails")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS documenttype")
