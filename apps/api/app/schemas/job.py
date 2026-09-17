from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

JobStatusEnum = Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED"]
JobTypeEnum = Literal[
    "TRANSCRIBE_VIDEO",
    "ANALYZE_CONTENT",
    "EXTRACT_CONCEPTS",
    "CREATE_VISUAL_PLAN",
    "GENERATE_PAGE",
    "GENERATE_PDF",
]


class JobStatusResponse(BaseModel):
    id: str
    project_id: str
    page_id: Optional[str] = None
    job_type: str
    status: JobStatusEnum
    progress: float = Field(..., ge=0.0, le=1.0)
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
