from app.services.renderer.components.base import VisualComponentRenderer
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext

class ConceptMapRenderer(VisualComponentRenderer):
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        theme = context.theme
        
        html_out = '<div style="display: flex; flex-direction: column; align-items: center; gap: 20px; margin: 24px 0;">'
        html_out += f'<div style="padding: 12px 24px; border-radius: 8px; border: 2px solid {theme.accent}; background: {theme.accent_light}; color: {theme.text_primary}; font-weight: bold;">{self._escape(concept.title)}</div>'
        
        if concept.steps:
            html_out += f'<div style="width: 2px; height: 20px; background: {theme.card_border};"></div>'
            html_out += '<div style="display: flex; gap: 16px; flex-wrap: wrap; justify-content: center;">'
            for step in concept.steps:
                html_out += f'<div style="padding: 10px 16px; border-radius: 6px; border: 1px solid {theme.card_border}; background: {theme.page_bg}; color: {theme.text_secondary}; font-size: 13.5px;">{self._escape(step.name)}</div>'
            html_out += '</div>'
        
        html_out += '</div>'
        return html_out
