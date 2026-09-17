import pytest
from app.schemas.concept import Concept, SourceRange
from app.services.visual_planner import VisualPlanner, CONCEPT_TO_VISUAL_MAP


def test_visual_planner_mapping_rules():
    planner = VisualPlanner()

    for ctype, expected_vtype in CONCEPT_TO_VISUAL_MAP.items():
        concept = Concept(
            title=f"Test {ctype}",
            concept_type=ctype,
            importance_score=0.8,
            source=SourceRange(start=0.0, end=10.0),
            explanation="Explanation text.",
            visual_type=expected_vtype,
        )
        mapped = planner.map_visual_type(concept)
        assert mapped == expected_vtype


def test_visual_planner_section_planning():
    planner = VisualPlanner()
    c1 = Concept(
        title="Operating System",
        concept_type="definition",
        importance_score=0.9,
        source=SourceRange(start=0.0, end=10.0),
        explanation="System software.",
        visual_type="concept_card",
    )
    c2 = Concept(
        title="Three-Way Handshake",
        concept_type="process",
        importance_score=0.85,
        source=SourceRange(start=10.0, end=30.0),
        explanation="SYN, SYN-ACK, ACK.",
        visual_type="flowchart",
    )

    plan = planner.create_visual_plan([c1, c2], page_title="Computer Science Fundamentals")
    assert plan.page_title == "Computer Science Fundamentals"
    assert len(plan.sections) == 2
    assert plan.sections[0].priority == 1
    assert plan.sections[0].visual_type == "concept_card"
    assert plan.sections[1].priority == 2
    assert plan.sections[1].visual_type == "flowchart"
