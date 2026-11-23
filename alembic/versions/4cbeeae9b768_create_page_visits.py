"""create page_visits

Revision ID: 4cbeeae9b768
Revises:
Create Date: 2026-11-23 02:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4cbeeae9b768"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "page_visits",
        sa.Column("path", sa.Text(), primary_key=True),
        sa.Column("total", sa.BigInteger(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("page_visits")
