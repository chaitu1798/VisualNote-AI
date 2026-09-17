from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

SourceTypeEnum = Literal["youtube", "upload", "audio"]
ProjectStatusEnum = Literal[
    "DRAFT",
    "UPLOADING",
    "PROCESSING",
    "ANALYZING",
    "GENERATING",
    "READY",
    "FAILED",
    "ARCHIVED",
]
LearningLevelEnum = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED", "EXAM"]
OutputModeEnum = Literal["QUICK", "STANDARD", "DETAILED", "EXAM"]
VisualStyleEnum = Literal["HANDWRITTEN", "ACADEMIC", "INFOGRAPHIC"]


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    source_type: SourceTypeEnum = "youtube"
    source_url: Optional[str] = None
    learning_level: LearningLevelEnum = "INTERMEDIATE"
    output_mode: OutputModeEnum = "STANDARD"
    visual_style: VisualStyleEnum = "HANDWRITTEN"


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[ProjectStatusEnum] = None
    learning_level: Optional[LearningLevelEnum] = None
    output_mode: Optional[OutputModeEnum] = None
    visual_style: Optional[VisualStyleEnum] = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    source_type: str
    source_url: Optional[str] = None
    status: str
    learning_level: str
    output_mode: str
    visual_style: str
    page_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
