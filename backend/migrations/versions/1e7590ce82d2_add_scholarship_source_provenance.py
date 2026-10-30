"""add scholarship source provenance

Revision ID: 1e7590ce82d2
Revises: f5851ae99954
Create Date: 2026-10-30 21:05:54.527361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e7590ce82d2'
down_revision: Union[str, Sequence[str], None] = 'f5851ae99954'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Allow provider to be NULL
    op.alter_column(
        "scholarships",
        "provider",
        existing_type=sa.String(length=255),
        nullable=True,
    )

    # Add source provenance columns
    op.add_column(
        "scholarships",
        sa.Column("sources", sa.JSON(), nullable=True),
    )

    op.add_column(
        "scholarships",
        sa.Column("source_references", sa.JSON(), nullable=True),
    )

    op.add_column(
        "scholarships",
        sa.Column("source_metadata", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scholarships", "source_metadata")
    op.drop_column("scholarships", "source_references")
    op.drop_column("scholarships", "sources")

    op.alter_column(
        "scholarships",
        "provider",
        existing_type=sa.String(length=255),
        nullable=False,
    )