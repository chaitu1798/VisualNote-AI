from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class VisualPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "visual_plans"

    concept_id = Column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    job_id = Column(String(36), ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    visual_type = Column(String(50), nullable=False, default="concept_card")  # 8 templates
    theme = Column(String(50), nullable=False, default="clean_handwritten")
    priority = Column(Integer, nullable=False, default=1)
    layout = Column(String(100), nullable=True, default="default")
    content_json = Column(JSON, nullable=True)
    generation_prompt = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")

    # Relationships
    concept = relationship("Concept", back_populates="visual_plan")
    job = relationship("GenerationJob", back_populates="visual_plans")

