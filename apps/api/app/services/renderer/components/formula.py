from app.services.renderer.components.base import VisualComponentRenderer
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext

class FormulaBlockRenderer(VisualComponentRenderer):
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        if not concept.formula:
            return ""
            
        theme = context.theme
        f_expr = self._escape(concept.formula.expression)
        f_exp = self._escape(concept.formula.explanation)
        
        html_out = f"""
        <div style="padding: 16px; border-radius: 8px; margin: 16px 0; text-align: center; word-break: break-all; background:{theme.formula_bg}; border: 1px dashed {theme.card_border};">
            <div style="color:{theme.text_primary}; font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 600;">
                <code>{f_expr}</code>
            </div>
            <div style="color:{theme.text_secondary}; font-size:13px; margin-top:8px;">
                <em>{f_exp}</em>
            </div>
        """
        if concept.formula.variables:
            html_out += '<div style="margin-top:10px; font-size:12px; text-align: left;">'
            html_out += f'<strong style="color:{theme.text_primary};">Variables:</strong><ul style="margin:4px 0 0 16px; padding:0;">'
            for var_k, var_v in concept.formula.variables.items():
                html_out += f'<li style="color:{theme.text_secondary}; margin-bottom: 2px;"><code>{self._escape(var_k)}</code>: {self._escape(var_v)}</li>'
            html_out += '</ul></div>'
        html_out += '</div>'
        return html_out
