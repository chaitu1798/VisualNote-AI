import pytest
from app.schemas.generation import PipelineRunRequest
from app.services.pipeline_service import PipelineService


@pytest.mark.asyncio
async def test_end_to_end_tracer_bullet():
    pipeline = PipelineService()
    req = PipelineRunRequest(
        raw_text="An Operating System manages computer hardware resources and coordinates processes.",
        theme="clean_handwritten",
        learning_level="INTERMEDIATE",
        mock_mode=True,
    )

    result = await pipeline.run_pipeline(request=req)

    assert result.status == "COMPLETED"
    assert result.current_stage == "completed"
    assert result.progress == 1.0
    assert result.transcript is not None
    assert len(result.transcript.segments) > 0
    assert result.concepts is not None
    assert len(result.concepts) >= 1
    assert result.visual_plan is not None
    assert len(result.visual_plan.sections) >= 1
    assert result.render_result is not None
    assert result.render_result.status == "READY"
    assert result.render_result.html_url is not None


@pytest.mark.asyncio
async def test_pipeline_failure_on_empty_input():
    pipeline = PipelineService()
    req = PipelineRunRequest(
        raw_text="",
        mock_mode=True,
    )
    result = await pipeline.run_pipeline(request=req)
    assert result.status == "FAILED"
    assert result.error is not None
    assert "No input provided" in result.error

