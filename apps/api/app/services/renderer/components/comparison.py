from app.services.renderer.components.base import VisualComponentRenderer
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext

class ComparisonTableRenderer(VisualComponentRenderer):
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        if not concept.comparison:
            return ""
            
        theme = context.theme
        entities = concept.comparison.entities or []
        aspects = concept.comparison.aspects or {}
        ent0 = self._escape(entities[0]) if len(entities) > 0 else "Entity A"
        ent1 = self._escape(entities[1]) if len(entities) > 1 else "Entity B"

        html_out = f"""
        <div style="overflow-x: auto;">
            <table style="border: 1px solid {theme.card_border}; width:100%; border-collapse: collapse; margin-top: 16px;">
                <thead>
                    <tr style="background:{theme.accent_light};">
                        <th style="border: 1px solid {theme.card_border}; padding:8px; text-align:left; color:{theme.text_primary}; font-weight: bold;">Aspect</th>
                        <th style="border: 1px solid {theme.card_border}; padding:8px; text-align:left; color:{theme.text_primary}; font-weight: bold;">{ent0}</th>
                        <th style="border: 1px solid {theme.card_border}; padding:8px; text-align:left; color:{theme.text_primary}; font-weight: bold;">{ent1}</th>
                    </tr>
                </thead>
                <tbody>
        """
        for aspect_name, values in aspects.items():
            v0 = self._escape(values[0]) if len(values) > 0 else ""
            v1 = self._escape(values[1]) if len(values) > 1 else ""
            html_out += f"""
            <tr>
                <td style="border: 1px solid {theme.card_border}; padding:8px; font-weight:600; color:{theme.text_primary}; font-size: 14px;">{self._escape(aspect_name)}</td>
                <td style="border: 1px solid {theme.card_border}; padding:8px; color:{theme.text_secondary}; font-size: 14px;">{v0}</td>
                <td style="border: 1px solid {theme.card_border}; padding:8px; color:{theme.text_secondary}; font-size: 14px;">{v1}</td>
            </tr>
            """
        html_out += """
                </tbody>
            </table>
        </div>
        """
        return html_out
