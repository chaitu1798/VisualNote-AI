from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import GenerationJob
from app.schemas.concept import Concept, ConceptAnalysisResponse
from app.schemas.visual_plan import VisualPlanRequest, VisualPlanResponse
from app.schemas.generation import (
    PipelineRunRequest,
    PipelineRunResponse,
    RenderRequest,
    RenderResponse,
    JobDetailResponse,
)
from app.services.llm.factory import get_llm_provider
from app.services.importance_service import ImportanceRankingService
from app.services.visual_planner import get_visual_planner
from app.services.renderer.browser_renderer import get_browser_renderer
from app.services.pipeline_service import get_pipeline_service

router = APIRouter()


@router.get("/status")
def get_generation_status():
    """Generation service health/status check."""
    return {"status": "ready"}


@router.post("/analyze", response_model=ConceptAnalysisResponse)
async def analyze_transcript(
    payload: dict,
):
    """
    Analyzes educational transcript text with LLM and applies deterministic
    importance ranking. Returns structured, validated ConceptJSON.
    """
    text = payload.get("text", "")
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text cannot be empty."
        )

    learning_level = payload.get("learning_level", "INTERMEDIATE")
    llm = get_llm_provider()

    analysis = await llm.extract_concepts(transcript_text=text, learning_level=learning_level)
    ranked = ImportanceRankingService.rank_concepts(analysis.concepts, full_text=text)

    return ConceptAnalysisResponse(
        title=analysis.title,
        summary=analysis.summary,
        concepts=ranked,
    )


@router.post("/visual-plan", response_model=VisualPlanResponse)
def generate_visual_plan(payload: VisualPlanRequest):
    """
    Converts ConceptJSON into VisualPlanJSON with template mapping and layout validation.
    """
    planner = get_visual_planner()
    try:
        plan = planner.create_visual_plan(
            concepts=payload.concepts,
            page_title=payload.page_title,
            theme=payload.theme,
        )
        return plan
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.post("/render", response_model=RenderResponse)
def render_page(payload: RenderRequest):
    """
    Renders a VisualPlanResponse deterministically to HTML and PNG screenshot.
    """
    renderer = get_browser_renderer()
    try:
        result = renderer.render_visual_plan(payload.visual_plan)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rendering failed: {str(exc)}"
        )


@router.post("/pipeline", response_model=PipelineRunResponse)
async def run_pipeline_endpoint(
    fastapi_req: Request,
    db: Session = Depends(get_db),
):
    """
    Executes the end-to-end tracer bullet pipeline:
    Input -> Transcription -> Concept Extraction -> Ranking ->
    Visual Planning -> Deterministic Rendering -> Visual Note Output.
    Supports both application/json and multipart/form-data.
    """
    pipeline = get_pipeline_service()

    content_type = fastapi_req.headers.get("content-type", "")
    media_bytes = None
    media_filename = None

    if "application/json" in content_type:
        body_json = await fastapi_req.json()
        run_req = PipelineRunRequest(**body_json)
    elif "multipart/form-data" in content_type:
        form = await fastapi_req.form()
        uploaded_file = form.get("file")
        if uploaded_file and hasattr(uploaded_file, "read"):
            media_bytes = await uploaded_file.read()
            media_filename = getattr(uploaded_file, "filename", "upload.mp4")

        raw_text = form.get("raw_text")
        theme = form.get("theme") or "clean_handwritten"
        learning_level = form.get("learning_level") or "INTERMEDIATE"
        project_id = form.get("project_id")

        run_req = PipelineRunRequest(
            raw_text=raw_text if isinstance(raw_text, str) else None,
            project_id=project_id if isinstance(project_id, str) else None,
            theme=str(theme),
            learning_level=str(learning_level),
            mock_mode=True,
        )
    else:
        # Fallback to attempting JSON parse
        try:
            body_json = await fastapi_req.json()
            run_req = PipelineRunRequest(**body_json)
        except Exception:
            run_req = PipelineRunRequest(raw_text=None, mock_mode=True)

    response = await pipeline.run_pipeline(
        request=run_req,
        db=db,
        media_bytes=media_bytes,
        media_filename=media_filename,
    )
    return response


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves generation job status, current stage, progress, and result data.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    return JobDetailResponse(
        id=job.id,
        project_id=job.project_id,
        job_type=job.job_type,
        status=job.status,
        current_stage=job.current_stage or "created",
        progress=job.progress,
        error_message=job.error_message,
        result_data=job.result_data,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
