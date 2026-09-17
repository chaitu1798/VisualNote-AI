import pytest
from pydantic import ValidationError
from app.schemas.concept import Concept, VisualPlanSchema, SourceRange
from app.schemas.project import ProjectCreate
from app.schemas.job import JobStatusResponse


def test_valid_concept_schema():
    concept = Concept(
        title="TCP Three-Way Handshake",
        concept_type="process",
        importance_score=0.95,
        source=SourceRange(start=120.0, end=180.0),
        explanation="Mechanism used to establish a reliable TCP connection.",
        visual_type="flowchart",
        steps=[
            {"name": "SYN", "description": "Client initiates request"},
            {"name": "SYN-ACK", "description": "Server acknowledges"},
            {"name": "ACK", "description": "Client confirms"},
        ],
    )
    assert concept.title == "TCP Three-Way Handshake"
    assert concept.importance_score == 0.95
    assert len(concept.steps) == 3


def test_concept_importance_bounds():
    # Importance < 0 should fail
    with pytest.raises(ValidationError):
        Concept(
            title="Invalid",
            concept_type="definition",
            importance_score=-0.1,
            source=SourceRange(start=0.0, end=10.0),
            explanation="Invalid importance",
            visual_type="concept_card",
        )

    # Importance > 1 should fail
    with pytest.raises(ValidationError):
        Concept(
            title="Invalid",
            concept_type="definition",
            importance_score=1.1,
            source=SourceRange(start=0.0, end=10.0),
            explanation="Invalid importance",
            visual_type="concept_card",
        )


def test_concept_timestamp_validation():
    # Negative start should fail
    with pytest.raises(ValidationError):
        SourceRange(start=-5.0, end=10.0)

    # Negative end should fail
    with pytest.raises(ValidationError):
        SourceRange(start=0.0, end=-1.0)

    # end < start should fail
    with pytest.raises(ValidationError):
        SourceRange(start=50.0, end=20.0)


def test_valid_visual_plan():
    concept = Concept(
        title="Binary Search Tree",
        concept_type="definition",
        importance_score=0.8,
        source=SourceRange(start=10.0, end=50.0),
        explanation="Node-based binary tree data structure.",
        visual_type="concept_card",
    )
    plan = VisualPlanSchema(
        visual_type="concept_card",
        layout="default",
        content=concept,
        style="handwritten",
    )
    assert plan.visual_type == "concept_card"
    assert plan.style == "handwritten"


def test_project_create_schema():
    project = ProjectCreate(
        title="Computer Networks Chapter 1",
        source_type="youtube",
        source_url="https://youtube.com/watch?v=example",
        learning_level="INTERMEDIATE",
        output_mode="STANDARD",
        visual_style="HANDWRITTEN",
    )
    assert project.title == "Computer Networks Chapter 1"
    assert project.source_type == "youtube"


def test_job_status_schema():
    job = JobStatusResponse(
        id="job-12345",
        project_id="proj-12345",
        job_type="EXTRACT_CONCEPTS",
        status="PROCESSING",
        progress=0.5,
        created_at="2026-09-15T12:00:00Z",
    )
    assert job.status == "PROCESSING"
    assert job.progress == 0.5
