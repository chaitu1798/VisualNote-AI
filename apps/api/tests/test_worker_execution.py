import pytest
import uuid
from app.services.worker import JobWorker
from app.core.queue import JobQueueService
from app.models.job import GenerationJob
from app.models.source import Source, SourceTypeEnum, SourceStatusEnum
from app.models.transcript import Transcript, TranscriptProviderEnum
from app.models.concept import Concept as DBConcept
from app.models.visual_plan import VisualPlan as DBVisualPlan
from app.models.render_result import RenderResult
from app.models.page import Page


@pytest.mark.asyncio
async def test_worker_process_job_success(db_session):
    test_queue = JobQueueService(allow_test_fallback=True)
    test_queue._redis = None
    worker = JobWorker(queue_service=test_queue)

    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    source_id = f"src-{uuid.uuid4().hex[:8]}"
    job_id = f"job-{uuid.uuid4().hex[:8]}"

    # Setup source and transcript
    text_content = (
        "Photosynthesis is the process used by plants to convert light energy into chemical energy. "
        "Chlorophyll absorbs light most strongly in the blue portion of the electromagnetic spectrum. "
        "Carbon dioxide and water are converted into glucose and oxygen."
    )
    source = Source(
        id=source_id,
        project_id=project_id,
        type=SourceTypeEnum.text,
        title="Photosynthesis Overview",
        status=SourceStatusEnum.processed,
        meta_data={"character_count": len(text_content)},
    )
    db_session.add(source)

    transcript = Transcript(
        id=f"tr-{uuid.uuid4().hex[:8]}",
        project_id=project_id,
        source_id=source_id,
        content=text_content,
        provider=TranscriptProviderEnum.manual_text,
    )
    db_session.add(transcript)

    job = GenerationJob(
        id=job_id,
        project_id=project_id,
        source_id=source_id,
        status="QUEUED",
        current_stage="queued",
        progress=0.0,
    )
    db_session.add(job)
    db_session.commit()

    # Process job via worker
    success = await worker.process_job(
        job_id=job_id,
        payload={"theme": "ocean", "learning_level": "BEGINNER"},
        db=db_session,
    )

    assert success is True

    # Reload job
    db_session.refresh(job)
    assert job.status == "COMPLETED"
    assert job.current_stage == "completed"
    assert job.progress == 1.0
    assert job.result_data is not None
    assert "image_url" in job.result_data

    # Verify concepts were saved to database
    concepts = db_session.query(DBConcept).filter(DBConcept.job_id == job_id).all()
    assert len(concepts) > 0

    # Verify visual plan was saved
    plans = db_session.query(DBVisualPlan).filter(DBVisualPlan.job_id == job_id).all()
    assert len(plans) > 0
    assert plans[0].theme == "ocean"

    # Verify render result was saved
    render_results = db_session.query(RenderResult).filter(RenderResult.job_id == job_id).all()
    assert len(render_results) > 0

    # Verify page was created
    pages = db_session.query(Page).filter(Page.project_id == project_id).all()
    assert len(pages) > 0


@pytest.mark.asyncio
async def test_worker_non_recoverable_error(db_session):
    test_queue = JobQueueService(allow_test_fallback=True)
    test_queue._redis = None
    worker = JobWorker(queue_service=test_queue)

    job_id = f"job-err-{uuid.uuid4().hex[:8]}"
    project_id = f"proj-err-{uuid.uuid4().hex[:8]}"

    # Create job pointing to a non-existent source
    job = GenerationJob(
        id=job_id,
        project_id=project_id,
        source_id="non-existent-source-id",
        status="QUEUED",
        current_stage="queued",
        progress=0.0,
    )
    db_session.add(job)
    db_session.commit()

    success = await worker.process_job(
        job_id=job_id,
        payload={"theme": "dark"},
        db=db_session,
    )

    assert success is False
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.current_stage == "failed"
    assert job.error_code == "PROCESSING_ERROR"


def test_worker_recoverability_classification():
    worker = JobWorker(queue_service=JobQueueService(allow_test_fallback=True))

    # ValueErrors, missing input, and unsupported formats are non-recoverable
    assert worker.is_recoverable_error(ValueError("Invalid argument")) is False
    assert worker.is_recoverable_error(RuntimeError("File not found in storage")) is False
    assert worker.is_recoverable_error(Exception("Unsupported media format")) is False

    # Connection timeouts or temporary glitches are recoverable
    assert worker.is_recoverable_error(ConnectionError("Connection timed out to provider")) is True
    assert worker.is_recoverable_error(TimeoutError("Read timed out")) is True
