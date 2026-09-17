"""Phase 1 pipeline additions

Revision ID: 0002_phase1_pipeline
Revises: 0001_initial_phase0
Create Date: 2026-09-17 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_phase1_pipeline"
down_revision: Union[str, None] = "0001_initial_phase0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add duration and source_id to transcripts table
    op.add_column("transcripts", sa.Column("duration", sa.Float(), nullable=True))
    op.add_column("transcripts", sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True))
    op.create_index(op.f("ix_transcripts_source_id"), "transcripts", ["source_id"], unique=False)

    # Add current_stage and result_data to generation_jobs table
    op.add_column("generation_jobs", sa.Column("current_stage", sa.String(50), nullable=False, server_default="created"))
    op.add_column("generation_jobs", sa.Column("result_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("generation_jobs", "result_data")
    op.drop_column("generation_jobs", "current_stage")
    op.drop_index(op.f("ix_transcripts_source_id"), table_name="transcripts")
    op.drop_column("transcripts", "source_id")
    op.drop_column("transcripts", "duration")
