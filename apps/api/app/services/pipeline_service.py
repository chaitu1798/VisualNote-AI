import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.models.source import Source
from app.models.transcript import Transcript
from app.models.concept import Concept as DBConcept
from app.models.visual_plan import VisualPlan as DBVisualPlan
from app.models.page import Page
from app.models.job import GenerationJob

from app.schemas.transcript import TranscriptResponse, TranscriptSegment
from app.schemas.generation import PipelineRunRequest, PipelineRunResponse, RenderResponse
from app.services.media.media_processor import get_media_processor
from app.services.transcription.factory import get_transcription_provider
from app.services.llm.factory import get_llm_provider
from app.services.importance_service import ImportanceRankingService
from app.services.visual_planner import get_visual_planner
from app.services.renderer.browser_renderer import get_browser_renderer

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Coordinates the core Phase 1 tracer-bullet pipeline:
    Input -> Audio Extraction -> Transcription -> Cleaning -> Analysis ->
    Concept Extraction -> Importance Ranking -> Visual Planning ->
    Deterministic Layout Rendering -> Storage & Job Persistence.
    """

    def __init__(self):
        self.media_processor = get_media_processor()
        self.transcription_provider = get_transcription_provider()
        self.llm_provider = get_llm_provider()
        self.visual_planner = get_visual_planner()
        self.renderer = get_browser_renderer()

    async def run_pipeline(
        self,
        request: PipelineRunRequest,
        db: Optional[Session] = None,
        media_bytes: Optional[bytes] = None,
        media_filename: Optional[str] = None,
    ) -> PipelineRunResponse:
        job_id = f"job-{uuid.uuid4().hex[:10]}"
        project_id = request.project_id
        db_job = None

        # 1. Initialize Job in Database if DB session available
        if db is not None:
            # Ensure a project exists
            if not project_id:
                # Find an existing user or create a demo user if none exists
                user_id = "default-dev-user"
                # Check for existing project or create one
                proj = db.query(Project).first()
                if not proj:
                    from app.models.user import User
                    user = db.query(User).first()
                    if not user:
                        user = User(
                            id=user_id,
                            email="developer@visualnote.ai",
                            name="Developer User"
                        )
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                    user_id = user.id

                    proj = Project(
                        id=f"proj-{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        title="Tracer Bullet Demo",
                        source_type="upload" if media_bytes else "transcript",
                        status="PROCESSING",
                    )
                    db.add(proj)
                    db.commit()
                    db.refresh(proj)
                project_id = proj.id

            db_job = GenerationJob(
                id=job_id,
                project_id=project_id,
                job_type="PIPELINE",
                status="PROCESSING",
                current_stage="created",
                progress=0.05,
                provider=settings.AI_PROVIDER,
            )
            db.add(db_job)
            db.commit()

        try:
            # 2. Stage: Extracting / Ingesting Media
            if media_bytes and media_filename:
                logger.info(f"Pipeline: Extracting media from '{media_filename}'")
                if db_job:
                    db_job.current_stage = "extracting"
                    db_job.progress = 0.15
                    db.commit()

                audio_data, meta = self.media_processor.extract_audio(media_bytes, media_filename)
                source_duration = meta.get("duration_sec", 0.0)

                # Persist Source
                if db:
                    src = Source(
                        id=f"src-{uuid.uuid4().hex[:8]}",
                        project_id=project_id,
                        source_type="upload",
                        storage_key=media_filename,
                        duration=source_duration,
                    )
                    db.add(src)
                    db.commit()

                # Stage: Transcribing
                if db_job:
                    db_job.current_stage = "transcribing"
                    db_job.progress = 0.30
                    db.commit()

                transcription_result = await self.transcription_provider.transcribe(
                    audio_data, filename=media_filename
                )
            else:
                # Direct raw text / transcript input
                if not request.raw_text or not request.raw_text.strip():
                    raise ValueError("No input provided: please provide audio/video or non-empty educational text.")
                text_input = request.raw_text.strip()
                if db_job:
                    db_job.current_stage = "transcribing"
                    db_job.progress = 0.30
                    db.commit()

                transcription_result = await self.transcription_provider.transcribe_text(text_input)

            # Persist Transcript
            db_transcript = None
            if db:
                # Delete any old transcript for this project to keep clean 1:1
                db.query(Transcript).filter(Transcript.project_id == project_id).delete()
                db_transcript = Transcript(
                    id=f"tr-{uuid.uuid4().hex[:8]}",
                    project_id=project_id,
                    source_id=request.source_id,
                    language=transcription_result.language,
                    content=transcription_result.text,
                    duration=transcription_result.duration,
                    segments=[s.model_dump() for s in transcription_result.segments],
                )
                db.add(db_transcript)
                db.commit()
                db.refresh(db_transcript)

            transcript_response = TranscriptResponse(
                id=db_transcript.id if db_transcript else f"tr-{uuid.uuid4().hex[:8]}",
                project_id=project_id,
                source_id=request.source_id,
                language=transcription_result.language,
                content=transcription_result.text,
                duration=transcription_result.duration,
                segments=transcription_result.segments,
                created_at=datetime.now(timezone.utc),
            )

            # 3. Stage: Analyzing & Extracting Concepts
            if db_job:
                db_job.current_stage = "analyzing"
                db_job.progress = 0.50
                db.commit()

            raw_analysis = await self.llm_provider.extract_concepts(
                transcript_text=transcription_result.text,
                segments=transcription_result.segments,
                learning_level=request.learning_level or "INTERMEDIATE"
            )

            # 4. Importance Ranking
            ranked_concepts = ImportanceRankingService.rank_concepts(
                raw_analysis.concepts, full_text=transcription_result.text
            )

            # Persist Concepts
            if db:
                db.query(DBConcept).filter(DBConcept.project_id == project_id).delete()
                for c in ranked_concepts:
                    db_c = DBConcept(
                        id=c.id or f"c-{uuid.uuid4().hex[:8]}",
                        project_id=project_id,
                        title=c.title,
                        type=c.concept_type,
                        description=c.explanation,
                        importance=c.importance_score,
                        source_start=c.source.start,
                        source_end=c.source.end,
                        structured_content=c.model_dump(),
                    )
                    db.add(db_c)
                db.commit()

            # 5. Stage: Visual Planning
            if db_job:
                db_job.current_stage = "planning"
                db_job.progress = 0.70
                db.commit()

            visual_plan = self.visual_planner.create_visual_plan(
                concepts=ranked_concepts,
                page_title=raw_analysis.title,
                theme=request.theme or settings.DEFAULT_THEME,
            )

            # Persist Visual Plan
            if db and ranked_concepts:
                primary_concept_id = ranked_concepts[0].id
                if primary_concept_id:
                    db.query(DBVisualPlan).filter(DBVisualPlan.concept_id == primary_concept_id).delete()
                    db_vp = DBVisualPlan(
                        id=visual_plan.id,
                        concept_id=primary_concept_id,
                        visual_type=visual_plan.sections[0].visual_type,
                        layout="default",
                        content_json=visual_plan.model_dump(),
                        status="READY",
                    )
                    db.add(db_vp)
                    db.commit()

            # 6. Stage: Deterministic Layout Rendering
            if db_job:
                db_job.current_stage = "rendering"
                db_job.progress = 0.85
                db.commit()

            render_result = self.renderer.render_visual_plan(visual_plan)

            # Persist Page
            if db:
                db.query(Page).filter(Page.project_id == project_id).delete()
                db_page = Page(
                    id=f"page-{uuid.uuid4().hex[:8]}",
                    project_id=project_id,
                    page_number=1,
                    title=visual_plan.page_title,
                    page_type=visual_plan.sections[0].visual_type if visual_plan.sections else "concept_card",
                    image_url=render_result.image_url,
                    content_json=visual_plan.model_dump(),
                    source_start=ranked_concepts[0].source.start if ranked_concepts else 0.0,
                    source_end=ranked_concepts[-1].source.end if ranked_concepts else 60.0,
                    generation_status="READY",
                )
                db.add(db_page)
                db.commit()

            # 7. Complete Job
            if db_job:
                db_job.current_stage = "completed"
                db_job.status = "COMPLETED"
                db_job.progress = 1.0
                db_job.completed_at = datetime.now(timezone.utc)
                db_job.result_data = {
                    "page_title": visual_plan.page_title,
                    "concept_count": len(ranked_concepts),
                    "image_url": render_result.image_url,
                    "html_url": render_result.html_url,
                }
                db.commit()

            return PipelineRunResponse(
                job_id=job_id,
                project_id=project_id,
                status="COMPLETED",
                current_stage="completed",
                progress=1.0,
                transcript=transcript_response,
                concepts=ranked_concepts,
                visual_plan=visual_plan,
                render_result=render_result,
                error=None,
            )

        except Exception as exc:
            logger.error(f"Pipeline execution failed on job {job_id}: {exc}", exc_info=True)
            if db_job:
                db_job.current_stage = "failed"
                db_job.status = "FAILED"
                db_job.error_message = str(exc)
                db_job.completed_at = datetime.now(timezone.utc)
                db.commit()

            return PipelineRunResponse(
                job_id=job_id,
                project_id=project_id,
                status="FAILED",
                current_stage="failed",
                progress=0.0,
                transcript=None,
                concepts=None,
                visual_plan=None,
                render_result=None,
                error=str(exc),
            )


_pipeline_service = None


def get_pipeline_service() -> PipelineService:
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service
