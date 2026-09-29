from app.services.renderer.components.base import VisualComponentRenderer
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext

class FlowchartRenderer(VisualComponentRenderer):
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        html_out = ""
        theme = context.theme
        if concept.steps:
            html_out += '<div style="display: flex; flex-direction: column; gap: 8px; margin: 16px 0;">'
            for i, step in enumerate(concept.steps):
                html_out += f"""
                <div style="display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 8px; border: 1px solid {theme.card_border}; background:{theme.page_bg};">
                    <div style="width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; background:{theme.accent}; color:#ffffff;">{i + 1}</div>
                    <div>
                        <strong style="color:{theme.text_primary};">{self._escape(step.name)}</strong>
                        <p style="color:{theme.text_secondary}; margin:2px 0 0 0; font-size:13px;">{self._escape(step.description)}</p>
                    </div>
                </div>
                """
                if i < len(concept.steps) - 1:
                    html_out += f"""
                    <div style="display: flex; justify-content: center; margin: -2px 0; color:{theme.accent};">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>
                    </div>
                    """
            html_out += '</div>'
        return html_out
