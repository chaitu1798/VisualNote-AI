from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.transcript import TranscriptResponse
from app.schemas.concept import Concept
from app.schemas.visual_plan import VisualPlanResponse


PipelineStageEnum = Literal[
    "created",
    "queued",
    "extracting",
    "transcribing",
    "analyzing",
    "planning",
    "rendering",
    "completed",
    "failed",
    "cancelled",
]


class AsyncJobCreateRequest(BaseModel):
    source_id: Optional[str] = Field(default=None, description="Existing source ID to process")
    raw_text: Optional[str] = Field(default=None, description="Direct text to process into source and job")
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    theme: Optional[str] = Field(default="clean_handwritten", description="Theme preset")
    learning_level: Optional[str] = Field(default="INTERMEDIATE", description="Learning depth level")
    idempotency_key: Optional[str] = Field(default=None, description="Optional unique request idempotency key")


class PipelineRunRequest(BaseModel):
    raw_text: Optional[str] = Field(default=None, description="Direct educational text or transcript")
    source_id: Optional[str] = Field(default=None, description="Uploaded source ID")
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    theme: Optional[str] = Field(default="clean_handwritten", description="Theme preset")
    learning_level: Optional[str] = Field(default="INTERMEDIATE", description="Learning depth level")
    mock_mode: Optional[bool] = Field(default=True, description="Run deterministically in mock mode")


class RenderRequest(BaseModel):
    visual_plan: VisualPlanResponse
    theme: Optional[str] = Field(default="clean_handwritten")


class RenderResponse(BaseModel):
    page_title: str
    image_url: Optional[str] = None
    html_url: Optional[str] = None
    svg_content: Optional[str] = None
    storage_path: Optional[str] = None
    status: str = "READY"


class PipelineRunResponse(BaseModel):
    job_id: str
    project_id: Optional[str] = None
    status: str
    current_stage: PipelineStageEnum
    progress: float
    transcript: Optional[TranscriptResponse] = None
    concepts: Optional[List[Concept]] = None
    visual_plan: Optional[VisualPlanResponse] = None
    render_result: Optional[RenderResponse] = None
    error: Optional[str] = None


class JobDetailResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    source_id: Optional[str] = None
    job_type: str
    status: str
    current_stage: PipelineStageEnum
    progress: float
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    idempotency_key: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

