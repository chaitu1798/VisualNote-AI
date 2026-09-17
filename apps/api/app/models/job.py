from sqlalchemy import Column, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, utc_now


class GenerationJob(Base, UUIDMixin):
    __tablename__ = "generation_jobs"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)
    job_type = Column(String(50), nullable=False)  # TRANSCRIBE, EXTRACT, GENERATE_PAGE, PIPELINE, etc.
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED
    current_stage = Column(String(50), nullable=False, default="created")  # created, extracting, transcribing, analyzing, planning, rendering, completed, failed
    progress = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    error_message = Column(Text, nullable=True)
    provider = Column(String(50), nullable=True)
    provider_job_id = Column(String(255), nullable=True)
    result_data = Column(JSON, nullable=True)  # Output data snapshot
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="jobs")
