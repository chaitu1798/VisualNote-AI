from app.schemas.concept import Concept, SourceRange
from app.services.importance_service import ImportanceRankingService


def test_importance_ranking_normalization():
    c1 = Concept(
        title="Operating System",
        concept_type="definition",
        importance_score=0.9,
        source=SourceRange(start=0.0, end=10.0),
        explanation="Fundamental software layer managing hardware resources.",
        visual_type="concept_card",
    )
    c2 = Concept(
        title="Example Printer Driver",
        concept_type="example",
        importance_score=0.3,
        source=SourceRange(start=10.0, end=20.0),
        explanation="Specific device driver example.",
        visual_type="concept_card",
    )

    full_text = "Operating System is fundamental and essential. Printer driver is an example."
    ranked = ImportanceRankingService.rank_concepts([c2, c1], full_text=full_text)

    # c1 should be ranked higher than c2 due to base score, definition type, and keyword indicators
    assert ranked[0].title == "Operating System"
    assert ranked[1].title == "Example Printer Driver"
    assert 0.0 <= ranked[0].importance_score <= 1.0
    assert 0.0 <= ranked[1].importance_score <= 1.0
    assert ranked[0].importance_score >= ranked[1].importance_score


def test_importance_ranking_bounds_edge_cases():
    # Very high initial score
    c_high = Concept(
        title="Crucial Core Concept",
        concept_type="formula",
        importance_score=1.0,
        source=SourceRange(start=0.0, end=10.0),
        explanation="Crucial formula expression.",
        visual_type="formula_block",
    )
    # Zero initial score
    c_low = Concept(
        title="Unrelated Side Note",
        concept_type="general",
        importance_score=0.0,
        source=SourceRange(start=10.0, end=20.0),
        explanation="Side note.",
        visual_type="concept_card",
    )

    ranked = ImportanceRankingService.rank_concepts([c_low, c_high], full_text="")
    assert 0.0 <= ranked[0].importance_score <= 1.0
    assert 0.0 <= ranked[1].importance_score <= 1.0


def test_importance_ranking_empty_and_single():
    assert ImportanceRankingService.rank_concepts([]) == []

    c1 = Concept(
        title="Single Item",
        concept_type="definition",
        importance_score=0.75,
        source=SourceRange(start=0.0, end=5.0),
        explanation="Only item.",
        visual_type="concept_card",
    )
    ranked = ImportanceRankingService.rank_concepts([c1])
    assert len(ranked) == 1
    assert 0.0 <= ranked[0].importance_score <= 1.0


def test_importance_ranking_equal_scores_stable():
    c1 = Concept(
        title="Beta Concept",
        concept_type="definition",
        importance_score=0.8,
        source=SourceRange(start=0.0, end=5.0),
        explanation="First same score item.",
        visual_type="concept_card",
    )
    c2 = Concept(
        title="Alpha Concept",
        concept_type="definition",
        importance_score=0.8,
        source=SourceRange(start=5.0, end=10.0),
        explanation="Second same score item.",
        visual_type="concept_card",
    )
    ranked = ImportanceRankingService.rank_concepts([c1, c2])
    assert len(ranked) == 2
    assert ranked[0].importance_score == ranked[1].importance_score
    # Both remain in valid range
    assert 0.0 <= ranked[0].importance_score <= 1.0


def test_importance_ranking_nan_or_invalid_score_sanitization():
    c_nan = Concept(
        title="NaN Concept",
        concept_type="general",
        importance_score=0.5,
        source=SourceRange(start=0.0, end=5.0),
        explanation="Concept with initially bad score.",
        visual_type="concept_card",
    )
    # Manually simulate a NaN score on the object
    c_nan.importance_score = float("nan")
    ranked = ImportanceRankingService.rank_concepts([c_nan])
    assert len(ranked) == 1
    assert not (ranked[0].importance_score != ranked[0].importance_score)  # not NaN
    assert 0.0 <= ranked[0].importance_score <= 1.0

