"""llm_traces table

Revision ID: b9e3d716ac42
Revises: a1c4f9d2e7b3
Create Date: 2026-05-04 17:30:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b9e3d716ac42"
down_revision: str | None = "a1c4f9d2e7b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_traces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.String(length=32), nullable=False),
        sa.Column("request_message", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("debug", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ok"),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_traces_user_id", "llm_traces", ["user_id"])
    op.create_index("ix_llm_traces_created_at", "llm_traces", ["created_at"])
    op.create_index("ix_llm_traces_endpoint", "llm_traces", ["endpoint"])
    op.create_index("ix_llm_traces_status", "llm_traces", ["status"])


def downgrade() -> None:
    op.drop_index("ix_llm_traces_status", table_name="llm_traces")
    op.drop_index("ix_llm_traces_endpoint", table_name="llm_traces")
    op.drop_index("ix_llm_traces_created_at", table_name="llm_traces")
    op.drop_index("ix_llm_traces_user_id", table_name="llm_traces")
    op.drop_table("llm_traces")
