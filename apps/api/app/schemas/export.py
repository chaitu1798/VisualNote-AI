from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExportRequest(BaseModel):
    project_id: str
    format: str = "pdf"


class ExportResponse(BaseModel):
    id: str
    project_id: str
    format: str
    storage_key: Optional[str] = None
    url: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
