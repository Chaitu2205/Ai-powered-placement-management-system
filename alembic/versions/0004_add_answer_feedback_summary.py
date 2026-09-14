"""phase 10 - add feedback_summary to interview_answers

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additive, nullable column. Every other interview_answers column already
    # covered Phase 10's needs (score, relevance/correctness/completeness/
    # communication, good_points_json, improvements_json, suggested_answer) -
    # this is the one genuinely missing piece: a short human-readable summary
    # distinct from the structured sub-scores.
    op.add_column("interview_answers", sa.Column("feedback_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("interview_answers", "feedback_summary")
