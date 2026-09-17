import asyncio
import logging
import signal
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.queue import get_job_queue_service, JobQueueService
from app.models.job import GenerationJob
from app.models.source import Source
from app.models.transcript import Transcript
from app.models.concept import Concept as DBConcept
from app.models.visual_plan import VisualPlan as DBVisualPlan
from app.models.page import Page
from app.models.render_result import RenderResult

from app.services.media.media_processor import get_media_processor, MediaProcessingError
from app.services.storage_service import get_storage_provider
from app.services.transcription.factory import get_transcription_provider
from app.services.llm.factory import get_llm_provider
from app.services.importance_service import ImportanceRankingService
from app.services.visual_planner import get_visual_planner
from app.services.renderer.browser_renderer import get_browser_renderer
from app.services.transcription.cleaning import TranscriptCleaner, TranscriptCleaningError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class JobWorker:
    """
    Executable Background Worker for VisualNote AI:
    - Reads jobs from Redis Queue
    - Loads Job and Source from PostgreSQL
    - Executes deterministic pipeline stages:
        queued -> extracting -> transcribing -> analyzing -> planning -> rendering -> completed
    - Persists Concept, VisualPlan, Page, and RenderResult records
    - Retries transient failures up to 3 times
    - Fast-fails non-recoverable errors
    - Handles graceful shutdown
    """

    def __init__(self, queue_service: Optional[JobQueueService] = None):
        self.queue = queue_service or get_job_queue_service()
        self.media_processor = get_media_processor()
        self.storage = get_storage_provider()
        self.transcription_provider = get_transcription_provider()
        self.llm_provider = get_llm_provider()
        self.visual_planner = get_visual_planner()
        self.renderer = get_browser_renderer()
        self.running = False

    def is_recoverable_error(self, exc: Exception) -> bool:
        """Determines whether an exception is recoverable via retry."""
        # Non-recoverable: Validation, missing input, unsupported files
        if isinstance(exc, (ValueError, MediaProcessingError, TranscriptCleaningError)):
            return False
        msg = str(exc).lower()
        if "unsupported" in msg or "not found" in msg or "empty" in msg or "invalid" in msg:
            return False
        # Recoverable: Network timeouts, browser launch hiccups, temporary redis/db glitches
        return True

    def _update_stage(
        self,
        db: Session,
        job: GenerationJob,
        stage: str,
        progress: float,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Updates job stage and progress in PostgreSQL and Redis cache."""
        job.current_stage = stage
        job.progress = progress
        job.updated_at = datetime.now(timezone.utc)
        if error_message:
            job.error_message = error_message
        if error_code:
            job.error_code = error_code
        db.commit()

        # Update Redis state cache
        state_dict = {
            "job_id": job.id,
            "project_id": job.project_id,
            "status": job.status,
            "current_stage": stage,
            "progress": progress,
            "error_message": error_message,
            "error_code": error_code,
            "result_data": job.result_data,
        }
        self.queue.set_job_state(job.id, state_dict)

    async def process_job(
        self,
        job_id: str,
        payload: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> bool:
        """Executes a single generation job through the full Phase 2 pipeline."""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                logger.error(f"Worker: Job '{job_id}' not found in database.")
                return False

            if job.status in ("COMPLETED", "CANCELLED"):
                logger.info(f"Worker: Job '{job_id}' is already {job.status}. Skipping.")
                return True

            logger.info(f"Worker: Starting processing for job '{job_id}' (attempt {job.retry_count + 1})")
            job.status = "PROCESSING"
            job.started_at = job.started_at or datetime.now(timezone.utc)
            self._update_stage(db, job, "queued", 0.05)

            source = None
            if job.source_id:
                source = db.query(Source).filter(Source.id == job.source_id).first()

            # Retrieve parameters from payload or job
            theme = payload.get("theme") or settings.DEFAULT_THEME
            learning_level = payload.get("learning_level") or "INTERMEDIATE"

            # 1. Stage: Media extraction / ingestion
            audio_bytes = None
            transcript_text = None
            segments_data = None

            if source and source.source_type in ("video", "audio") and source.storage_key:
                self._update_stage(db, job, "extracting", 0.15)
                media_bytes = self.storage.read(source.storage_key)
                if not media_bytes:
                    raise ValueError(f"Source media file not found in storage: {source.storage_key}")

                audio_bytes, meta = self.media_processor.extract_audio(media_bytes, source.original_filename or "upload.mp4")
                if meta.get("duration_sec") and not source.duration:
                    source.duration = meta["duration_sec"]
                    db.commit()

            # 2. Stage: Transcription
            self._update_stage(db, job, "transcribing", 0.30)
            if audio_bytes:
                transcription_result = await self.transcription_provider.transcribe(
                    audio_bytes, filename=source.original_filename if source else "audio.mp3"
                )
                transcript_text = transcription_result.text
                segments_data = [s.model_dump() for s in transcription_result.segments]
                duration_val = transcription_result.duration
            elif source and source.meta_data and source.meta_data.get("raw_text"):
                raw_in = source.meta_data["raw_text"]
                cleaned_in, segs, duration_val = TranscriptCleaner.process(raw_in, None)
                transcript_text = cleaned_in
                segments_data = [s.model_dump() for s in segs]
            elif payload.get("raw_text"):
                raw_in = payload["raw_text"]
                cleaned_in, segs, duration_val = TranscriptCleaner.process(raw_in, None)
                transcript_text = cleaned_in
                segments_data = [s.model_dump() for s in segs]
            else:
                # Check for existing transcript for this project
                existing_tr = db.query(Transcript).filter(Transcript.project_id == job.project_id).first()
                if existing_tr and existing_tr.content:
                    transcript_text = existing_tr.content
                    segments_data = existing_tr.segments
                    duration_val = existing_tr.duration
                else:
                    raise ValueError("No input text or media found for job.")

            # Persist or update Transcript
            db.query(Transcript).filter(Transcript.project_id == job.project_id).delete()
            db_transcript = Transcript(
                id=f"tr-{uuid.uuid4().hex[:8]}",
                project_id=job.project_id,
                source_id=job.source_id,
                language="en",
                content=transcript_text,
                raw_content=payload.get("raw_text") or (source.meta_data.get("raw_text") if source and source.meta_data else transcript_text),
                duration=duration_val if "duration_val" in locals() else None,
                segments=segments_data,
                provider=settings.TRANSCRIPTION_PROVIDER,
            )
            db.add(db_transcript)
            db.commit()

            # 3. Stage: Content Analysis & Concept Extraction
            self._update_stage(db, job, "analyzing", 0.50)
            raw_analysis = await self.llm_provider.extract_concepts(
                transcript_text=transcript_text,
                learning_level=learning_level,
            )
            ranked_concepts = ImportanceRankingService.rank_concepts(
                concepts=raw_analysis.concepts,
                full_text=transcript_text,
            )

            # Persist Concepts linked to this job
            db.query(DBConcept).filter(DBConcept.job_id == job.id).delete()
            for c in ranked_concepts:
                db_c = DBConcept(
                    id=c.id or f"c-{uuid.uuid4().hex[:8]}",
                    project_id=job.project_id,
                    job_id=job.id,
                    title=c.title,
                    type=c.concept_type,
                    description=c.explanation,
                    importance=c.importance_score,
                    confidence=c.confidence or 1.0,
                    source_start=c.source.start,
                    source_end=c.source.end,
                    structured_content=c.model_dump(),
                )
                db.add(db_c)
            db.commit()

            # 4. Stage: Visual Planning
            self._update_stage(db, job, "planning", 0.70)
            visual_plan = self.visual_planner.create_visual_plan(
                concepts=ranked_concepts,
                page_title=raw_analysis.title,
                theme=theme,
            )

            # Persist Visual Plans linked to this job
            db.query(DBVisualPlan).filter(DBVisualPlan.job_id == job.id).delete()
            if ranked_concepts:
                primary_concept_id = ranked_concepts[0].id
                db_vp = DBVisualPlan(
                    id=visual_plan.id,
                    concept_id=primary_concept_id,
                    job_id=job.id,
                    visual_type=visual_plan.sections[0].visual_type,
                    theme=theme,
                    priority=1,
                    layout="default",
                    content_json=visual_plan.model_dump(),
                    status="READY",
                )
                db.add(db_vp)
                db.commit()

            # 5. Stage: Deterministic Rendering
            self._update_stage(db, job, "rendering", 0.85)
            render_result = self.renderer.render_visual_plan(visual_plan)

            # Persist Page
            db.query(Page).filter(Page.project_id == job.project_id).delete()
            db_page = Page(
                id=f"page-{uuid.uuid4().hex[:8]}",
                project_id=job.project_id,
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

            # Persist RenderResult records
            db.query(RenderResult).filter(RenderResult.job_id == job.id).delete()
            if render_result.image_url:
                db_rr_png = RenderResult(
                    id=f"rr-png-{uuid.uuid4().hex[:8]}",
                    job_id=job.id,
                    format="png",
                    storage_key=render_result.image_url.lstrip("/storage/"),
                    url=render_result.image_url,
                    renderer="browser",
                    theme=theme,
                )
                db.add(db_rr_png)

            if render_result.html_url:
                db_rr_html = RenderResult(
                    id=f"rr-html-{uuid.uuid4().hex[:8]}",
                    job_id=job.id,
                    format="html",
                    storage_key=render_result.html_url.lstrip("/storage/"),
                    url=render_result.html_url,
                    renderer="concept_card",
                    theme=theme,
                )
                db.add(db_rr_html)
            db.commit()

            # 6. Mark Job Completed
            job.status = "COMPLETED"
            job.current_stage = "completed"
            job.progress = 1.0
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = None
            job.error_code = None
            job.result_data = {
                "page_title": visual_plan.page_title,
                "concept_count": len(ranked_concepts),
                "image_url": render_result.image_url,
                "html_url": render_result.html_url,
            }
            db.commit()

            self._update_stage(db, job, "completed", 1.0)
            logger.info(f"Worker: Job '{job_id}' completed successfully!")
            return True

        except Exception as exc:
            logger.error(f"Worker: Error processing job '{job_id}': {exc}", exc_info=True)
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.last_error = str(exc)
                if self.is_recoverable_error(exc) and job.retry_count < MAX_RETRIES:
                    job.retry_count += 1
                    job.status = "QUEUED"
                    self._update_stage(db, job, "queued", 0.05, error_message=f"Retrying: {exc}")
                    logger.warning(f"Worker: Re-enqueuing job '{job_id}' (retry {job.retry_count}/{MAX_RETRIES})")
                    self.queue.enqueue_job(job.id, payload)
                else:
                    job.status = "FAILED"
                    self._update_stage(db, job, "failed", 0.0, error_message=str(exc), error_code="PROCESSING_ERROR")
            return False

        finally:
            if should_close:
                db.close()

    async def run_worker_loop(self, poll_interval: int = 2) -> None:
        """Continuous execution loop that dequeues and processes background jobs."""
        self.running = True
        logger.info("VisualNote Background Worker initialized and listening on Redis queue...")

        while self.running:
            try:
                job_msg = self.queue.dequeue_job(timeout=poll_interval)
                if job_msg:
                    job_id = job_msg.get("job_id")
                    payload = job_msg.get("payload", {})
                    if job_id:
                        await self.process_job(job_id, payload)
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Worker loop encountered exception: {e}")
                await asyncio.sleep(poll_interval)

    def stop(self) -> None:
        """Signals the worker loop to shutdown gracefully."""
        logger.info("Worker received shutdown signal. Stopping loop...")
        self.running = False


def main():
    """CLI entrypoint to run the real worker process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    worker = JobWorker()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown():
        worker.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            pass  # Windows event loop limitation for signal handlers

    try:
        loop.run_until_complete(worker.run_worker_loop())
    except KeyboardInterrupt:
        worker.stop()
    finally:
        loop.close()
        logger.info("Worker process exited cleanly.")


if __name__ == "__main__":
    main()
