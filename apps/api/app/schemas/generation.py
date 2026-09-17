from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.transcript import TranscriptResponse
from app.schemas.concept import Concept
from app.schemas.visual_plan import VisualPlanResponse


PipelineStageEnum = Literal[
    "created",
    "extracting",
    "transcribing",
    "analyzing",
    "planning",
    "rendering",
    "completed",
    "failed",
]


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
    job_type: str
    status: str
    current_stage: PipelineStageEnum
    progress: float
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
