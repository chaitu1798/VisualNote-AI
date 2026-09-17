from fastapi import APIRouter
from typing import List
from app.schemas.project import ProjectResponse

router = APIRouter()


@router.get("", response_model=List[ProjectResponse])
def list_projects():
    """List projects placeholder (Phase 2)."""
    return []
