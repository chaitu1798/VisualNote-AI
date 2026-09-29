from typing import Dict, Type
from app.services.renderer.components.base import VisualComponentRenderer
from app.services.renderer.components.definition import DefinitionCardRenderer
from app.services.renderer.components.flowchart import FlowchartRenderer
from app.services.renderer.components.comparison import ComparisonTableRenderer
from app.services.renderer.components.formula import FormulaBlockRenderer
from app.services.renderer.components.timeline import TimelineRenderer
from app.services.renderer.components.concept_map import ConceptMapRenderer
from app.services.renderer.components.list import ListRenderer
from app.services.renderer.components.example import ExampleRenderer

class ComponentFactory:
    _registry: Dict[str, Type[VisualComponentRenderer]] = {
        "concept_card": DefinitionCardRenderer,
        "flowchart": FlowchartRenderer,
        "comparison_table": ComparisonTableRenderer,
        "formula_block": FormulaBlockRenderer,
        "timeline": TimelineRenderer,
        "concept_map": ConceptMapRenderer,
        "bullet_list": ListRenderer,
        "example_card": ExampleRenderer,
    }

    @classmethod
    def get_renderer(cls, visual_type: str) -> VisualComponentRenderer:
        renderer_class = cls._registry.get(visual_type, DefinitionCardRenderer)
        return renderer_class()
