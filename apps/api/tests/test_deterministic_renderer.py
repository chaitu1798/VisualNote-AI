import re
from app.schemas.concept import Concept, SourceRange, ConceptStep
from app.services.visual_planner import VisualPlanner
from app.services.renderer.core.page_composer import PageComposer
from app.services.renderer.browser_renderer import BrowserRenderer

def strip_dynamic_ids(html_str: str) -> str:
    # Remove dynamic section UUIDs
    html_str = re.sub(r'id="sec-[a-f0-9]+"', 'id="sec-STABLE"', html_str)
    return html_str

def test_deterministic_rendering():
    c = Concept(
        title="Deterministic Test",
        concept_type="process",
        importance_score=0.9,
        source=SourceRange(start=0.0, end=10.0),
        explanation="Testing if rendering produces identical output.",
        visual_type="flowchart",
        steps=[
            ConceptStep(name="Step 1", description="Do this"),
            ConceptStep(name="Step 2", description="Do that")
        ]
    )
    
    # Run 1
    planner1 = VisualPlanner()
    plan1 = planner1.create_visual_plan([c], page_title="Test")
    composer1 = PageComposer(plan1)
    output_a = composer1.render()
    output_a_stable = strip_dynamic_ids(output_a)
    
    # Run 2
    planner2 = VisualPlanner()
    plan2 = planner2.create_visual_plan([c], page_title="Test")
    composer2 = PageComposer(plan2)
    output_b = composer2.render()
    output_b_stable = strip_dynamic_ids(output_b)
    
    assert output_a_stable == output_b_stable, "Rendering is not deterministic"

def test_overflow_validation():
    # Create a very long text to force overflow
    long_text = "Overflowing text. " * 500 
    c = Concept(
        title="Long Concept",
        concept_type="general",
        importance_score=0.9,
        source=SourceRange(start=0.0, end=10.0),
        explanation=long_text,
        visual_type="concept_card",
    )
    
    planner = VisualPlanner()
    plan = planner.create_visual_plan([c])
    composer = PageComposer(plan)
    
    composer.render()
    
    # Should have triggered layout overflow
    assert any(err.code == "LAYOUT_OVERFLOW" for err in composer.context.errors)
