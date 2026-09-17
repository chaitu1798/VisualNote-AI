from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class VisualPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "visual_plans"

    concept_id = Column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    visual_type = Column(String(50), nullable=False, default="concept_card")  # 6 templates
    layout = Column(String(100), nullable=True, default="default")
    content_json = Column(JSON, nullable=True)
    generation_prompt = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")

    # Relationships
    concept = relationship("Concept", back_populates="visual_plan")
