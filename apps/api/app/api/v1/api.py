from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, projects, sources, generation, pages, transcripts, exports

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(sources.router, prefix="/sources", tags=["Sources"])
api_router.include_router(transcripts.router, prefix="/transcripts", tags=["Transcripts"])
api_router.include_router(generation.router, prefix="/generation", tags=["Generation"])
api_router.include_router(pages.router, prefix="/pages", tags=["Pages"])
api_router.include_router(exports.router, prefix="/projects/{project_id}/exports", tags=["Exports"])
