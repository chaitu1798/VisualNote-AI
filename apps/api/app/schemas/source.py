from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field

SourceTypeEnum = Literal["text", "audio", "video", "transcript", "youtube_reference"]


class SourceCreateRequest(BaseModel):
    source_type: SourceTypeEnum = Field(default="text")
    title: Optional[str] = Field(default=None, max_length=255)
    raw_text: Optional[str] = Field(default=None)
    source_url: Optional[str] = Field(default=None, max_length=1024)
    project_id: Optional[str] = Field(default=None)
    meta_data: Optional[Dict[str, Any]] = Field(default=None)


class SourceResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    source_type: str
    title: Optional[str] = None
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    storage_key: Optional[str] = None
    storage_url: Optional[str] = None
    source_url: Optional[str] = None
    status: str
    character_count: Optional[int] = None
    has_transcript: Optional[bool] = False
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def type(self) -> str:
        return self.source_type

    model_config = ConfigDict(from_attributes=True)


class SourceDetailResponse(SourceResponse):
    transcript_id: Optional[str] = None
