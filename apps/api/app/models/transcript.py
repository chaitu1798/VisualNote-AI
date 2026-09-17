from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, utc_now


class Transcript(Base, UUIDMixin):
    __tablename__ = "transcripts"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    language = Column(String(10), default="en", nullable=False)
    content = Column(Text, nullable=False)
    duration = Column(Float, nullable=True)  # in seconds
    segments = Column(JSON, nullable=True)  # [{start: 0.0, end: 4.5, text: "..."}]
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="transcript")
