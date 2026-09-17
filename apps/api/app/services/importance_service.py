import re
import math
from typing import List
from app.schemas.concept import Concept


class ImportanceRankingService:
    """
    Deterministic importance ranking layer.
    Combines LLM score with structural indicators, keyword density,
    concept type weighting, and early context positioning.
    Guarantees strict bounds [0.0, 1.0], handles missing/invalid/NaN scores,
    and provides stable deterministic sorting.
    """

    KEYWORD_INDICATORS = {
        "fundamental": 0.10,
        "crucial": 0.10,
        "important": 0.08,
        "core": 0.08,
        "primary": 0.06,
        "essential": 0.06,
        "key": 0.05,
        "purpose": 0.05,
        "defined as": 0.05,
        "formula": 0.05,
    }

    TYPE_WEIGHTS = {
        "definition": 0.12,
        "formula": 0.12,
        "process": 0.10,
        "comparison": 0.08,
        "timeline": 0.06,
        "relationship": 0.06,
        "example": 0.04,
        "list": 0.04,
        "general": 0.02,
    }

    @classmethod
    def calculate_score(cls, concept: Concept, full_text: str, index: int, total_concepts: int) -> float:
        # Safe score extraction
        try:
            raw_val = concept.importance_score
            if raw_val is None:
                base_score = 0.5
            else:
                base_score = float(raw_val)
                if math.isnan(base_score) or math.isinf(base_score):
                    base_score = 0.5
                else:
                    base_score = max(0.0, min(1.0, base_score))
        except (ValueError, TypeError):
            base_score = 0.5

        # 1. Concept Type weighting
        type_boost = cls.TYPE_WEIGHTS.get(concept.concept_type, 0.05)

        # 2. Position context: earlier concepts often introduce core definitions
        position_ratio = (total_concepts - index) / max(1, total_concepts)
        position_boost = position_ratio * 0.08

        # 3. Text search for indicator terms
        searchable = f"{concept.title} {concept.explanation} {' '.join(concept.supporting_points or [])}".lower()
        indicator_boost = 0.0
        for kw, weight in cls.KEYWORD_INDICATORS.items():
            if kw in searchable:
                indicator_boost += weight

        # Cap indicator boost to 0.15
        indicator_boost = min(0.15, indicator_boost)

        # 4. Term frequency of concept title in full transcript
        clean_title = re.escape(concept.title.lower())
        occurrences = len(re.findall(rf"\b{clean_title}\b", full_text.lower())) if full_text else 0
        frequency_boost = min(0.12, occurrences * 0.03)

        # Composite score calculation
        raw_composite = (
            (base_score * 0.55)
            + (type_boost * 0.15)
            + (position_boost * 0.10)
            + (indicator_boost * 0.10)
            + (frequency_boost * 0.10)
        )

        # Check for NaN / Inf before rounding
        if math.isnan(raw_composite) or math.isinf(raw_composite):
            return 0.50

        # Strictly clamp and round to [0.0, 1.0]
        normalized = round(max(0.0, min(1.0, raw_composite)), 2)
        return normalized

    @classmethod
    def rank_concepts(cls, concepts: List[Concept], full_text: str = "") -> List[Concept]:
        """
        Ranks concepts deterministically. Preserves original list length and
        guarantees stable sorting.
        """
        if not concepts:
            return []

        ranked: List[Concept] = []
        total = len(concepts)

        for i, concept in enumerate(concepts):
            updated_score = cls.calculate_score(concept, full_text, i, total)
            ranked_concept = concept.model_copy(update={"importance_score": updated_score})
            ranked.append(ranked_concept)

        # Stable sort descending by importance_score (preserves original relative order on equal scores)
        ranked.sort(key=lambda c: c.importance_score, reverse=True)
        return ranked
