"""Phase 2 backend foundation

Revision ID: 0003_phase2_backend_foundation
Revises: 0002_phase1_pipeline
Create Date: 2026-09-17 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0003_phase2_backend_foundation"
down_revision: Union[str, None] = "0002_phase1_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Sources table additions
    op.add_column("sources", sa.Column("title", sa.String(255), nullable=True))
    op.add_column("sources", sa.Column("original_filename", sa.String(255), nullable=True))
    op.add_column("sources", sa.Column("status", sa.String(50), nullable=False, server_default="ready"))
    op.add_column("sources", sa.Column("meta_data", sa.JSON(), nullable=True))
    op.add_column("sources", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))



    # 2. Transcripts table additions
    op.add_column("transcripts", sa.Column("raw_content", sa.Text(), nullable=True))
    op.add_column("transcripts", sa.Column("provider", sa.String(50), nullable=False, server_default="mock"))
    op.add_column("transcripts", sa.Column("provider_metadata", sa.JSON(), nullable=True))
    op.add_column("transcripts", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # 3. Concepts table additions
    op.add_column("concepts", sa.Column("job_id", sa.String(36), sa.ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True))
    op.create_index(op.f("ix_concepts_job_id"), "concepts", ["job_id"], unique=False)
    op.add_column("concepts", sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"))

    # 4. Visual Plans table additions
    op.add_column("visual_plans", sa.Column("job_id", sa.String(36), sa.ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True))
    op.create_index(op.f("ix_visual_plans_job_id"), "visual_plans", ["job_id"], unique=False)
    op.add_column("visual_plans", sa.Column("theme", sa.String(50), nullable=False, server_default="clean_handwritten"))
    op.add_column("visual_plans", sa.Column("priority", sa.Integer(), nullable=False, server_default="1"))

    # 5. Generation Jobs table additions
    op.add_column("generation_jobs", sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True))
    op.create_index(op.f("ix_generation_jobs_source_id"), "generation_jobs", ["source_id"], unique=False)
    op.add_column("generation_jobs", sa.Column("error_code", sa.String(50), nullable=True))
    op.add_column("generation_jobs", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("generation_jobs", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("generation_jobs", sa.Column("idempotency_key", sa.String(255), nullable=True))
    op.create_index(op.f("ix_generation_jobs_idempotency_key"), "generation_jobs", ["idempotency_key"], unique=False)
    op.add_column("generation_jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("generation_jobs", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # 6. Render Results table creation
    op.create_table(
        "render_results",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("format", sa.String(20), nullable=False, server_default="png"),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False, server_default="880"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="980"),
        sa.Column("renderer", sa.String(50), nullable=False, server_default="browser"),
        sa.Column("theme", sa.String(50), nullable=False, server_default="clean_handwritten"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("render_results")

    op.drop_index(op.f("ix_generation_jobs_idempotency_key"), table_name="generation_jobs")
    op.drop_column("generation_jobs", "updated_at")
    op.drop_column("generation_jobs", "started_at")
    op.drop_column("generation_jobs", "idempotency_key")
    op.drop_column("generation_jobs", "retry_count")
    op.drop_column("generation_jobs", "last_error")
    op.drop_column("generation_jobs", "error_code")
    op.drop_index(op.f("ix_generation_jobs_source_id"), table_name="generation_jobs")
    op.drop_column("generation_jobs", "source_id")

    op.drop_column("visual_plans", "priority")
    op.drop_column("visual_plans", "theme")
    op.drop_index(op.f("ix_visual_plans_job_id"), table_name="visual_plans")
    op.drop_column("visual_plans", "job_id")

    op.drop_column("concepts", "confidence")
    op.drop_index(op.f("ix_concepts_job_id"), table_name="concepts")
    op.drop_column("concepts", "job_id")

    op.drop_column("transcripts", "updated_at")
    op.drop_column("transcripts", "provider_metadata")
    op.drop_column("transcripts", "provider")
    op.drop_column("transcripts", "raw_content")

    op.drop_column("sources", "updated_at")
    op.drop_column("sources", "meta_data")
    op.drop_column("sources", "status")
    op.drop_column("sources", "original_filename")
    op.drop_column("sources", "title")
