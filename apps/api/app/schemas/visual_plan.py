from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.concept import Concept, VisualTypeEnum


class VisualSectionPlan(BaseModel):
    id: str = Field(..., description="Unique section identifier")
    concept_id: str = Field(..., description="Associated concept identifier")
    visual_type: VisualTypeEnum = Field(..., description="Deterministic template layout type")
    title: str = Field(..., min_length=1)
    priority: int = Field(default=1, ge=1, description="Layout rendering priority")
    theme: str = Field(default="clean_handwritten", description="Theme styling preset")
    layout: Dict[str, Any] = Field(default_factory=lambda: {"columns": 1})
    content: Concept
    validation_status: str = Field(default="VALID", description="Layout validation status")


class VisualPlanRequest(BaseModel):
    concepts: List[Concept] = Field(..., min_length=1)
    page_title: Optional[str] = Field(default="Visual Learning Note")
    theme: Optional[str] = Field(default="clean_handwritten")


class VisualPlanResponse(BaseModel):
    id: str
    page_title: str
    theme: str
    sections: List[VisualSectionPlan]
    created_at: Optional[str] = None
