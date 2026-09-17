from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict


class TranscriptSegment(BaseModel):
    start: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end: float = Field(..., ge=0.0, description="End timestamp in seconds")
    text: str = Field(..., min_length=1, description="Transcript segment text")

    @model_validator(mode="after")
    def validate_segment(self) -> "TranscriptSegment":
        if self.end < self.start:
            raise ValueError("Segment end cannot be less than start")
        return self


class TranscriptCreate(BaseModel):
    project_id: Optional[str] = None
    source_id: Optional[str] = None
    language: str = Field("en", max_length=10)
    content: str = Field(..., min_length=1, description="Raw transcript or educational text")
    duration: Optional[float] = Field(None, ge=0.0)
    segments: Optional[List[TranscriptSegment]] = None


class TranscriptResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    source_id: Optional[str] = None
    language: str = "en"
    content: str
    duration: Optional[float] = None
    segments: Optional[List[TranscriptSegment]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CleanedTranscriptResponse(BaseModel):
    raw_text: str
    cleaned_text: str
    word_count: int
    estimated_duration_sec: float
    segments: List[TranscriptSegment]
