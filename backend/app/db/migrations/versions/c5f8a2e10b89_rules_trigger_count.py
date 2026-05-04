"""rules: trigger_count

Revision ID: c5f8a2e10b89
Revises: b9e3d716ac42
Create Date: 2026-05-04 17:45:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c5f8a2e10b89"
down_revision: str | None = "b9e3d716ac42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "rules",
        sa.Column(
            "trigger_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("rules", "trigger_count")
