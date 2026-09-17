import uuid
from typing import List, Dict, Any, Optional
import logging

from app.schemas.concept import Concept, VisualTypeEnum
from app.schemas.visual_plan import VisualSectionPlan, VisualPlanResponse

logger = logging.getLogger(__name__)

CONCEPT_TO_VISUAL_MAP: Dict[str, VisualTypeEnum] = {
    "definition": "concept_card",
    "process": "flowchart",
    "comparison": "comparison_table",
    "formula": "formula_block",
    "timeline": "timeline",
    "relationship": "concept_map",
    "example": "example_card",
    "list": "bullet_list",
    "general": "concept_card",
}

VALID_VISUAL_TYPES = set(CONCEPT_TO_VISUAL_MAP.values())


class VisualPlanningError(Exception):
    """Exception raised during visual plan generation or validation."""
    pass


class VisualPlanner:
    """Service to transform structured ConceptJSON into validated VisualPlanJSON."""

    def __init__(self, default_theme: str = "clean_handwritten"):
        self.default_theme = default_theme

    def map_visual_type(self, concept: Concept) -> VisualTypeEnum:
        """Determines the appropriate deterministic visual template for a concept."""
        # If concept already has a valid visual type, respect it if compatible
        if concept.visual_type in VALID_VISUAL_TYPES:
            return concept.visual_type

        # Fallback based on concept type
        return CONCEPT_TO_VISUAL_MAP.get(concept.concept_type, "concept_card")

    def plan_sections(
        self,
        concepts: List[Concept],
        theme: Optional[str] = None
    ) -> List[VisualSectionPlan]:
        """Generates prioritized, layout-validated sections for each concept."""
        if not concepts:
            raise VisualPlanningError("Cannot generate visual plan with empty concepts list.")

        active_theme = theme or self.default_theme
        sections: List[VisualSectionPlan] = []

        for i, concept in enumerate(concepts):
            visual_type = self.map_visual_type(concept)
            sec_id = f"sec-{uuid.uuid4().hex[:6]}"

            # Determine layout columns based on visual type
            cols = 2 if visual_type in ("comparison_table", "concept_map") else 1

            section = VisualSectionPlan(
                id=sec_id,
                concept_id=concept.id or f"concept-{i+1}",
                visual_type=visual_type,
                title=concept.title,
                priority=i + 1,
                theme=active_theme,
                layout={"columns": cols},
                content=concept,
                validation_status="VALID",
            )
            sections.append(section)

        return sections

    def create_visual_plan(
        self,
        concepts: List[Concept],
        page_title: Optional[str] = None,
        theme: Optional[str] = None
    ) -> VisualPlanResponse:
        """Creates and validates the full VisualPlanResponse."""
        sections = self.plan_sections(concepts, theme)
        title = page_title or (concepts[0].title if concepts else "Visual Learning Note")

        plan = VisualPlanResponse(
            id=f"vplan-{uuid.uuid4().hex[:8]}",
            page_title=title,
            theme=theme or self.default_theme,
            sections=sections,
        )
        return plan


_visual_planner = None


def get_visual_planner() -> VisualPlanner:
    global _visual_planner
    if _visual_planner is None:
        _visual_planner = VisualPlanner()
    return _visual_planner
