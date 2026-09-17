from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Page(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pages"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    page_type = Column(String(50), nullable=False, default="concept_card")
    image_url = Column(String(1024), nullable=True)
    content_json = Column(JSON, nullable=True)
    source_start = Column(Float, nullable=False, default=0.0)
    source_end = Column(Float, nullable=False, default=0.0)
    generation_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, GENERATING, READY, FAILED

    # Relationships
    project = relationship("Project", back_populates="pages")
