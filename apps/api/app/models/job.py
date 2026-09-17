from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, utc_now


class GenerationJob(Base, UUIDMixin):
    __tablename__ = "generation_jobs"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    page_id = Column(String(36), ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)
    job_type = Column(String(50), nullable=False, default="ASYNC_PIPELINE")  # TRANSCRIBE, EXTRACT, GENERATE_PAGE, PIPELINE, ASYNC_PIPELINE
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED
    current_stage = Column(String(50), nullable=False, default="created")  # created, queued, extracting, transcribing, analyzing, planning, rendering, completed, failed, cancelled
    progress = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    idempotency_key = Column(String(255), nullable=True, index=True)
    provider = Column(String(50), nullable=True)
    provider_job_id = Column(String(255), nullable=True)
    result_data = Column(JSON, nullable=True)  # Output data snapshot
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="jobs")
    source = relationship("Source", back_populates="jobs")
    concepts = relationship("Concept", back_populates="job", cascade="all, delete-orphan")
    visual_plans = relationship("VisualPlan", back_populates="job", cascade="all, delete-orphan")
    render_results = relationship("RenderResult", back_populates="job", cascade="all, delete-orphan")

