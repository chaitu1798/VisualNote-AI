from app.services.renderer.components.base import VisualComponentRenderer
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext

class ExampleRenderer(VisualComponentRenderer):
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        theme = context.theme
        html_out = ""
        
        if concept.examples:
            html_out += '<div style="display: flex; flex-direction: column; gap: 12px; margin: 16px 0;">'
            for ex in concept.examples:
                html_out += f"""
                <div style="padding: 14px; border-left: 4px solid {theme.accent}; background: {theme.accent_light}; border-radius: 0 6px 6px 0;">
                    <div style="font-size: 12px; font-weight: bold; color: {theme.accent}; text-transform: uppercase; margin-bottom: 6px;">Example</div>
                    <div style="font-size: 14px; color: {theme.text_primary};">{self._escape(ex)}</div>
                </div>
                """
            html_out += '</div>'
            
        return html_out
