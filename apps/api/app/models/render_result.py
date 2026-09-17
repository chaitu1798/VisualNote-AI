from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, utc_now


class RenderResult(Base, UUIDMixin):
    __tablename__ = "render_results"

    job_id = Column(String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    format = Column(String(20), nullable=False, default="png")  # png, html, svg
    storage_key = Column(String(1024), nullable=False)
    url = Column(String(1024), nullable=False)
    width = Column(Integer, nullable=False, default=880)
    height = Column(Integer, nullable=False, default=980)
    renderer = Column(String(50), nullable=False, default="browser")  # browser, svg_fallback
    theme = Column(String(50), nullable=False, default="clean_handwritten")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    job = relationship("GenerationJob", back_populates="render_results")
