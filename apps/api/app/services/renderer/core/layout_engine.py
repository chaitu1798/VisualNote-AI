import math
from typing import Dict, Any, Tuple
from app.schemas.concept import Concept
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext, BoundingBox

class LayoutEngine:
    @staticmethod
    def estimate_text_height(text: str, width: float, font_size: float = 14.5, line_height: float = 1.5) -> float:
        if not text:
            return 0.0
        char_width = font_size * 0.55
        chars_per_line = max(1, int(width / char_width))
        lines = 0
        for paragraph in text.split('\n'):
            length = len(paragraph)
            if length == 0:
                lines += 1
            else:
                lines += math.ceil(length / chars_per_line)
        return lines * (font_size * line_height)

    @classmethod
    def compute_component_bounds(
        cls, 
        section: VisualSectionPlan, 
        context: RenderContext, 
        start_y: float
    ) -> BoundingBox:
        concept = section.content
        width = context.content_width
        
        # Base padding
        height = 44.0 
        
        # Header (Title + tags)
        height += 30.0 # title row
        height += cls.estimate_text_height(concept.title, width - 40, font_size=19, line_height=1.4) + 12
        
        # Explanation
        exp_width = width - 40 - 32 # box padding
        height += cls.estimate_text_height(concept.explanation, exp_width, font_size=14.5, line_height=1.5) + 24 + 16
        
        # Component specific
        if section.visual_type == "flowchart" and concept.steps:
            for step in concept.steps:
                height += 44 
                height += cls.estimate_text_height(step.description, width - 100, font_size=13)
            height += (len(concept.steps) - 1) * 24 # arrows
            height += 32
            
        elif section.visual_type == "formula_block" and concept.formula:
            height += 32 + 20
            height += cls.estimate_text_height(concept.formula.explanation, width - 70, font_size=13)
            if concept.formula.variables:
                height += 20 + len(concept.formula.variables) * 18
            height += 16
            
        elif section.visual_type == "comparison_table" and concept.comparison:
            height += 40
            for aspect_name, values in (concept.comparison.aspects or {}).items():
                row_h = max(
                    cls.estimate_text_height(aspect_name, width * 0.3, font_size=14),
                    cls.estimate_text_height(values[0] if len(values)>0 else "", width * 0.3, font_size=14),
                    cls.estimate_text_height(values[1] if len(values)>1 else "", width * 0.3, font_size=14)
                )
                height += row_h + 16
            height += 16
            
        elif section.visual_type == "bullet_list" and concept.supporting_points:
            height += 30
            for pt in concept.supporting_points:
                height += cls.estimate_text_height(pt, width - 70, font_size=13.5) + 8
            height += 16
            
        elif section.visual_type == "example_card" and concept.examples:
            height += 30
            for ex in concept.examples:
                height += cls.estimate_text_height(ex, width - 70, font_size=13.5) + 8
            height += 16
            
        elif section.visual_type == "timeline" and concept.steps:
            for step in concept.steps:
                height += 50
                height += cls.estimate_text_height(step.description, width - 100, font_size=13)
            height += 16
            
        elif section.visual_type == "concept_map" and concept.steps:
            height += 150
            
        if concept.source:
            height += 24 
            
        return BoundingBox(x=context.margins["left"], y=start_y, width=width, height=height)
