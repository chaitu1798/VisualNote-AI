from sqlalchemy import Column, String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Concept(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "concepts"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, default="definition")  # definition, process, comparison, formula, etc.
    description = Column(Text, nullable=True)
    importance = Column(Float, nullable=False, default=0.5, index=True)  # 0.0 to 1.0
    confidence = Column(Float, nullable=False, default=1.0)
    source_start = Column(Float, nullable=False, default=0.0)
    source_end = Column(Float, nullable=False, default=0.0)
    structured_content = Column(JSON, nullable=True)  # Canonical Concept JSON payload

    # Relationships
    project = relationship("Project", back_populates="concepts")
    job = relationship("GenerationJob", back_populates="concepts")
    visual_plan = relationship("VisualPlan", back_populates="concept", uselist=False, cascade="all, delete-orphan")

