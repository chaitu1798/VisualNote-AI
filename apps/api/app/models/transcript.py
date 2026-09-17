from enum import Enum
from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, utc_now


class TranscriptProviderEnum(str, Enum):
    manual_text = "manual_text"
    manual_transcript = "manual_transcript"
    mock = "mock"
    whisper = "whisper"
    deepgram = "deepgram"
    assemblyai = "assemblyai"


class Transcript(Base, UUIDMixin):
    __tablename__ = "transcripts"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    language = Column(String(10), default="en", nullable=False)
    content = Column(Text, nullable=False)  # Cleaned transcript content
    raw_content = Column(Text, nullable=True)  # Raw uncleaned input/transcript
    duration = Column(Float, nullable=True)  # in seconds
    segments = Column(JSON, nullable=True)  # [{start: 0.0, end: 4.5, text: "..."}]
    provider = Column(String(50), default="mock", nullable=False)
    provider_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="transcript")
    source = relationship("Source", back_populates="transcripts")

