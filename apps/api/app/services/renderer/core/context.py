from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.renderer.theme import ThemeStyle

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    
    @property
    def bottom(self) -> float:
        return self.y + self.height

class RenderError(BaseModel):
    code: str
    component_id: Optional[str]
    message: str

class RenderContext(BaseModel):
    theme: ThemeStyle
    page_width: float = 880.0
    page_height: float = 1200.0
    margins: Dict[str, float] = {"top": 40.0, "bottom": 60.0, "left": 40.0, "right": 40.0}
    current_y: float = 0.0
    current_page: int = 1
    errors: List[RenderError] = Field(default_factory=list)

    @property
    def content_width(self) -> float:
        return self.page_width - self.margins["left"] - self.margins["right"]
        
    @property
    def max_y(self) -> float:
        return self.page_height - self.margins["bottom"]

class ComponentRenderResult(BaseModel):
    html: str
    bounding_box: BoundingBox
