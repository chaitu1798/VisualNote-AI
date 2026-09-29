from app.services.renderer.components.base import VisualComponentRenderer
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext

class TimelineRenderer(VisualComponentRenderer):
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        if not concept.steps:
            return ""
        
        theme = context.theme
        html_out = '<div style="position: relative; padding-left: 24px; margin: 16px 0;">'
        # vertical line
        html_out += f'<div style="position: absolute; left: 6px; top: 8px; bottom: 8px; width: 2px; background-color: {theme.accent};"></div>'
        
        for step in concept.steps:
            html_out += f"""
            <div style="position: relative; margin-bottom: 20px;">
                <div style="position: absolute; left: -22px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background-color: {theme.accent}; border: 2px solid {theme.page_bg};"></div>
                <div style="font-weight: bold; color: {theme.text_primary};">{self._escape(step.name)}</div>
                <div style="font-size: 13.5px; color: {theme.text_secondary}; margin-top: 4px;">{self._escape(step.description)}</div>
            </div>
            """
        html_out += '</div>'
        return html_out
