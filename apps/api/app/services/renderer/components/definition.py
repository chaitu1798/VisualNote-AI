from app.services.renderer.components.base import VisualComponentRenderer
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext

class DefinitionCardRenderer(VisualComponentRenderer):
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        html_out = ""
        theme = context.theme
        if concept.supporting_points:
            html_out += f'<div class="points-section"><h4 style="color:{theme.text_primary}; margin:12px 0 6px 0; font-size:14px; text-transform:uppercase; letter-spacing:0.5px;">Key Points</h4><ul style="list-style: none; padding: 0; margin: 8px 0;">'
            for pt in concept.supporting_points:
                html_out += f'<li style="font-size: 13.5px; display: flex; align-items: flex-start; gap: 8px; color:{theme.text_secondary}; margin-bottom:4px;"><span style="color:{theme.accent}; font-weight: bold;">✓</span> {self._escape(pt)}</li>'
            html_out += '</ul></div>'
            
        if concept.examples:
            html_out += f'<div style="margin-top:10px;"><span style="font-size:12px; font-weight:600; color:{theme.text_muted}; margin-right:8px;">Examples:</span>'
            for ex in concept.examples:
                html_out += f'<span style="background:{theme.page_bg}; border:1px solid {theme.card_border}; color:{theme.text_secondary}; padding:2px 8px; border-radius:12px; font-size:12px; margin-right:6px; display:inline-block; margin-bottom:4px;">{self._escape(ex)}</span>'
            html_out += '</div>'
            
        return html_out
