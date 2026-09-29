import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.queue import get_job_queue_service
from app.models.job import GenerationJob
from app.models.source import Source
from app.schemas.concept import Concept, ConceptAnalysisResponse
from app.schemas.visual_plan import VisualPlanRequest, VisualPlanResponse
from app.schemas.generation import (
    AsyncJobCreateRequest,
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
from app.services.source_ingestion_service import get_source_ingestion_service

logger = logging.getLogger(__name__)

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


@router.post("", response_model=JobDetailResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=JobDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_async_generation_job(
    payload: AsyncJobCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Creates an asynchronous generation job queued for background worker processing.
    Supports atomic request deduplication via 'Idempotency-Key' header.
    """
    idempotency_key = request.headers.get("Idempotency-Key") or payload.idempotency_key
    queue_service = get_job_queue_service()

    # 1. Idempotency Check
    if idempotency_key:
        existing_job = db.query(GenerationJob).filter(GenerationJob.idempotency_key == idempotency_key).first()
        if existing_job:
            logger.info(f"Idempotent hit in DB for key '{idempotency_key}': returning existing job {existing_job.id}")
            return JobDetailResponse.model_validate(existing_job)

    # 2. Source resolution / creation if raw_text is provided
    source_id = payload.source_id
    project_id = payload.project_id

    if not source_id and payload.raw_text:
        ingestion = get_source_ingestion_service()
        src = ingestion.ingest_text(
            raw_text=payload.raw_text,
            project_id=project_id,
            db=db,
        )
        source_id = src.id
        project_id = src.project_id
    elif source_id:
        src = db.query(Source).filter(Source.id == source_id).first()
        if not src:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found."
            )
        project_id = project_id or src.project_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either source_id or raw_text must be provided."
        )

    # Ensure a project exists
    if not project_id:
        ingestion = get_source_ingestion_service()
        proj = ingestion._ensure_project(db, title="Visual Note Project")
        project_id = proj.id

    # 3. Create GenerationJob in PostgreSQL
    job_id = f"job-{uuid.uuid4().hex[:10]}"
    job = GenerationJob(
        id=job_id,
        project_id=project_id,
        source_id=source_id,
        job_type="ASYNC_PIPELINE",
        status="QUEUED",
        current_stage="queued",
        progress=0.05,
        idempotency_key=idempotency_key,
        provider=settings.AI_PROVIDER,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Register idempotency key in Redis
    if idempotency_key:
        queue_service.check_or_set_idempotency(idempotency_key, job.id)

    # 4. Enqueue Job to Redis Queue
    queue_service.enqueue_job(
        job_id=job.id,
        payload={
            "job_id": job.id,
            "project_id": project_id,
            "source_id": source_id,
            "theme": payload.theme or settings.DEFAULT_THEME,
            "learning_level": payload.learning_level or "INTERMEDIATE",
            "raw_text": payload.raw_text,
        }
    )

    return JobDetailResponse.model_validate(job)


@router.post("/{job_id}/retry", response_model=JobDetailResponse)
def retry_job(job_id: str, db: Session = Depends(get_db)):
    """
    Retries a failed generation job by resetting its status and enqueuing it again.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    if job.status not in ("FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only failed or cancelled jobs can be retried. Current status is {job.status}"
        )

    # Reset state
    job.status = "QUEUED"
    job.current_stage = "queued"
    job.progress = 0.05
    job.error_message = None
    job.error_code = None
    job.retry_count = 0  # reset retry count to give it a fresh start
    db.commit()
    db.refresh(job)

    # Re-enqueue
    queue_service = get_job_queue_service()

    source = db.query(Source).filter(Source.id == job.source_id).first()
    raw_text = None
    if source and source.meta_data and "raw_text" in source.meta_data:
        raw_text = source.meta_data["raw_text"]

    # Check if there is an idempotent payload
    # For a robust system we would store the initial payload, but since worker reads from source anyway, we just construct minimal payload
    queue_service.enqueue_job(
        job_id=job.id,
        payload={
            "job_id": job.id,
            "project_id": job.project_id,
            "source_id": job.source_id,
            "theme": settings.DEFAULT_THEME, # could pull from visual plan if needed
            "learning_level": "INTERMEDIATE",
            "raw_text": raw_text,
        }
    )

    return JobDetailResponse.model_validate(job)
@router.post("/pipeline", response_model=PipelineRunResponse)
async def run_pipeline_endpoint(
    fastapi_req: Request,
    db: Session = Depends(get_db),
):
    """
    Executes the end-to-end tracer bullet pipeline synchronously (Phase 1 compatibility):
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
    First checks Redis state cache for hot updates; falls back to PostgreSQL.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    # Optional hot state overlay from Redis if available
    queue_service = get_job_queue_service()
    cached = queue_service.get_job_state(job_id)
    if cached:
        if cached.get("progress") is not None:
            job.progress = cached["progress"]
        if cached.get("current_stage"):
            job.current_stage = cached["current_stage"]
        if cached.get("status"):
            job.status = cached["status"]

    return JobDetailResponse.model_validate(job)

