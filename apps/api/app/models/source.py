from typing import Optional
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, utc_now


class SourceTypeEnum(str, Enum):
    text = "text"
    audio = "audio"
    video = "video"
    transcript = "transcript"
    youtube = "youtube_reference"


class SourceStatusEnum(str, Enum):
    ready = "ready"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class Source(Base, UUIDMixin):
    __tablename__ = "sources"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # text, audio, video, transcript, youtube_reference
    title = Column(String(255), nullable=True)
    original_filename = Column(String(255), nullable=True)
    source_url = Column(String(1024), nullable=True)
    storage_key = Column(String(1024), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    duration = Column(Float, nullable=True)  # in seconds
    status = Column(String(50), nullable=False, default="ready")
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="source")
    transcripts = relationship("Transcript", back_populates="source", cascade="all, delete-orphan")
    jobs = relationship("GenerationJob", back_populates="source")

    @property
    def type(self) -> str:
        return self.source_type

    @type.setter
    def type(self, val: str) -> None:
        self.source_type = val

    @property
    def url(self) -> Optional[str]:
        return self.source_url

    @url.setter
    def url(self, val: Optional[str]) -> None:
        self.source_url = val

    @property
    def file_path(self) -> Optional[str]:
        return self.storage_key

    @file_path.setter
    def file_path(self, val: Optional[str]) -> None:
        self.storage_key = val



