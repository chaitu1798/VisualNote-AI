from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, utc_now


class Source(Base, UUIDMixin):
    __tablename__ = "sources"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    source_type = Column(String(50), nullable=False)  # youtube, upload, audio
    source_url = Column(String(1024), nullable=True)
    storage_key = Column(String(1024), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    duration = Column(Float, nullable=True)  # in seconds
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="source")
