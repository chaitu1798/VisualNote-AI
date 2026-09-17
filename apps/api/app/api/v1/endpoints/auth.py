from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
def get_current_user_placeholder():
    """Future endpoint for authenticated user profile (Phase 2)."""
    return {"message": "Auth service initialized. Production authentication implemented in Phase 2."}
