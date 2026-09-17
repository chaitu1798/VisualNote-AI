from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_pages():
    """Pages listing placeholder (Phase 3 & 4)."""
    return []
