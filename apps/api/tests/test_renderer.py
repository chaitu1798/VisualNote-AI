from app.schemas.concept import Concept, SourceRange, ConceptStep, ConceptFormula
from app.services.visual_planner import VisualPlanner
from app.services.renderer.concept_card_renderer import ConceptCardRenderer
from app.services.renderer.browser_renderer import BrowserRenderer
from app.services.renderer.theme import get_theme


def test_concept_card_renderer_preserves_text_and_formulas():
    c = Concept(
        title="Precision Metric",
        concept_type="formula",
        importance_score=0.95,
        source=SourceRange(start=0.0, end=15.0),
        explanation="Proportion of true positive predictions among all positives.",
        visual_type="formula_block",
        formula=ConceptFormula(
            expression="Precision = TP / (TP + FP)",
            variables={"TP": "True Positives", "FP": "False Positives"},
            explanation="Precision formula",
        ),
        supporting_points=["Crucial when false positives are costly"],
        examples=["Spam detection filter"],
    )

    planner = VisualPlanner()
    plan = planner.create_visual_plan([c], page_title="ML Formulas")
    html_out = ConceptCardRenderer.render_page_html(plan)

    # Verification: Factual accuracy is 100% preserved
    assert "Precision Metric" in html_out
    assert "Precision = TP / (TP + FP)" in html_out
    assert "True Positives" in html_out
    assert "Crucial when false positives are costly" in html_out
    assert "Spam detection filter" in html_out


def test_concept_card_renderer_html_escaping_and_xss():
    malicious_title = "<script>alert('xss')</script>"
    malicious_explanation = 'Tags like <b>bold</b> & "quotes" should be escaped safely'
    c = Concept(
        title=malicious_title,
        concept_type="general",
        importance_score=0.8,
        source=SourceRange(start=0.0, end=5.0),
        explanation=malicious_explanation,
        visual_type="concept_card",
        supporting_points=["Point <one> & 'two'"],
    )
    planner = VisualPlanner()
    plan = planner.create_visual_plan([c], page_title="XSS <Test> & 'Safety'")
    html_out = ConceptCardRenderer.render_page_html(plan)

    # Must escape scripts and special characters
    assert "<script>alert" not in html_out
    assert "&lt;script&gt;alert" in html_out
    assert "&amp;" in html_out
    assert "&quot;quotes&quot;" in html_out
    # Check CSP header is present
    assert "Content-Security-Policy" in html_out



def test_theme_variations():
    for theme_name in ("clean_handwritten", "notebook", "chalkboard", "minimal"):
        theme = get_theme(theme_name)
        assert theme.name is not None
        assert theme.background is not None
        assert theme.card_bg is not None


def test_browser_renderer_execution():
    c = Concept(
        title="Operating System",
        concept_type="definition",
        importance_score=0.9,
        source=SourceRange(start=0.0, end=10.0),
        explanation="Manages computer hardware.",
        visual_type="concept_card",
    )
    planner = VisualPlanner()
    plan = planner.create_visual_plan([c])

    renderer = BrowserRenderer()
    result = renderer.render_visual_plan(plan)

    assert result.status == "READY"
    assert result.html_url is not None
    assert result.svg_content is not None
