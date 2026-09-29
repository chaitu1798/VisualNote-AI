from app.services.renderer.components.base import VisualComponentRenderer
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext

class ListRenderer(VisualComponentRenderer):
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        theme = context.theme
        html_out = ""
        
        if concept.supporting_points:
            html_out += f'<ul style="list-style: none; padding: 0; margin: 16px 0;">'
            for i, pt in enumerate(concept.supporting_points):
                html_out += f"""
                <li style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px; padding: 10px; border-radius: 6px; background: {theme.page_bg}; border: 1px solid {theme.card_border};">
                    <span style="font-weight: bold; color: {theme.accent};">{i+1}.</span>
                    <span style="font-size: 14px; color: {theme.text_primary};">{self._escape(pt)}</span>
                </li>
                """
            html_out += '</ul>'
            
        return html_out
