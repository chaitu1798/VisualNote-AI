from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.page import Page
from app.schemas.visual_plan import VisualPlanResponse
from app.services.renderer.browser_renderer import get_browser_renderer
from app.services.storage_service import get_storage_service

router = APIRouter()

class RegenerateRequest(BaseModel):
    theme: Optional[str] = None

class PageResponse(BaseModel):
    id: str
    project_id: str
    page_number: int
    title: str
    page_type: str
    image_url: Optional[str] = None
    generation_status: str

    class Config:
        from_attributes = True

@router.get("", response_model=List[PageResponse])
def list_pages(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    if project_id:
        return db.query(Page).filter(Page.project_id == project_id).all()
    return db.query(Page).all()

@router.post("/{page_id}/regenerate", response_model=PageResponse)
def regenerate_page(
    page_id: str,
    req: RegenerateRequest,
    db: Session = Depends(get_db)
):
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if not page.content_json:
        raise HTTPException(status_code=400, detail="Page has no visual plan content to regenerate from.")

    # Apply new theme if requested
    if req.theme:
        page.content_json["theme"] = req.theme
        db.commit()

    # Run synchronous deterministic render
    try:
        renderer = get_browser_renderer()
        plan = VisualPlanResponse(**page.content_json)

        result = renderer.render_visual_plan(plan)

        page.image_url = result.image_url
        page.generation_status = "READY"
        db.commit()
        db.refresh(page)
    except Exception as exc:
        page.generation_status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(exc)}")

    return page
