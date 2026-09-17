"""Initial Phase 0 schema tables

Revision ID: 0001_initial_phase0
Revises: 
Create Date: 2026-09-15 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_phase0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, default="youtube"),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="DRAFT", index=True),
        sa.Column("learning_level", sa.String(50), nullable=False, default="INTERMEDIATE"),
        sa.Column("output_mode", sa.String(50), nullable=False, default="STANDARD"),
        sa.Column("visual_style", sa.String(50), nullable=False, default="HANDWRITTEN"),
        sa.Column("page_count", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. sources table
    op.create_table(
        "sources",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("storage_key", sa.String(1024), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 4. transcripts table
    op.create_table(
        "transcripts",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("language", sa.String(10), nullable=False, default="en"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("segments", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 5. concepts table
    op.create_table(
        "concepts",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False, default="definition"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("importance", sa.Float(), nullable=False, default=0.5, index=True),
        sa.Column("source_start", sa.Float(), nullable=False, default=0.0),
        sa.Column("source_end", sa.Float(), nullable=False, default=0.0),
        sa.Column("structured_content", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 6. visual_plans table
    op.create_table(
        "visual_plans",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("concept_id", sa.String(36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("visual_type", sa.String(50), nullable=False, default="concept_card"),
        sa.Column("layout", sa.String(100), nullable=True, default="default"),
        sa.Column("content_json", sa.JSON(), nullable=True),
        sa.Column("generation_prompt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 7. pages table
    op.create_table(
        "pages",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("page_number", sa.Integer(), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("page_type", sa.String(50), nullable=False, default="concept_card"),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("content_json", sa.JSON(), nullable=True),
        sa.Column("source_start", sa.Float(), nullable=False, default=0.0),
        sa.Column("source_end", sa.Float(), nullable=False, default=0.0),
        sa.Column("generation_status", sa.String(50), nullable=False, default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 8. generation_jobs table
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("page_id", sa.String(36), sa.ForeignKey("pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="PENDING", index=True),
        sa.Column("progress", sa.Float(), nullable=False, default=0.0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("provider_job_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 9. exports table
    op.create_table(
        "exports",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("format", sa.String(20), nullable=False, default="pdf"),
        sa.Column("storage_key", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("exports")
    op.drop_table("generation_jobs")
    op.drop_table("pages")
    op.drop_table("visual_plans")
    op.drop_table("concepts")
    op.drop_table("transcripts")
    op.drop_table("sources")
    op.drop_table("projects")
    op.drop_table("users")
