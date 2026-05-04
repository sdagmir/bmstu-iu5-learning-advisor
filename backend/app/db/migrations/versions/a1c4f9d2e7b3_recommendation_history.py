"""recommendation_history table

Revision ID: a1c4f9d2e7b3
Revises: 6846bc59f1da
Create Date: 2026-05-04 17:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1c4f9d2e7b3"
down_revision: str | None = "6846bc59f1da"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recommendation_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("recommendations", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("profile_change_summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_history_user_id",
        "recommendation_history",
        ["user_id"],
    )
    op.create_index(
        "ix_recommendation_history_created_at",
        "recommendation_history",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_history_created_at", table_name="recommendation_history")
    op.drop_index("ix_recommendation_history_user_id", table_name="recommendation_history")
    op.drop_table("recommendation_history")
