"""phase 7 - add detected_skills_json to resume_analysis

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additive, nullable column. The resume_analysis table already stores
    # missing_skills_json (from Phase 1/2) but had no field for the skills
    # actually *found* on the resume - Phase 7 needs that distinction.
    op.add_column("resume_analysis", sa.Column("detected_skills_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("resume_analysis", "detected_skills_json")
