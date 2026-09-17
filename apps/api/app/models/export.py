from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, utc_now


class Export(Base, UUIDMixin):
    __tablename__ = "exports"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    format = Column(String(20), nullable=False, default="pdf")  # pdf, png
    storage_key = Column(String(1024), nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="exports")
