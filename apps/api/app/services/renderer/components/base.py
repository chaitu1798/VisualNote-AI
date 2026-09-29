from abc import ABC, abstractmethod
import html
from app.schemas.visual_plan import VisualSectionPlan
from app.services.renderer.core.context import RenderContext, BoundingBox

class VisualComponentRenderer(ABC):
    @staticmethod
    def _escape(text: str) -> str:
        return html.escape(str(text or ""), quote=True)

    def _render_header(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        title = self._escape(concept.title)
        ctype = self._escape(concept.concept_type.upper())
        score_val = concept.importance_score if concept.importance_score is not None else 0.50
        score = f"{score_val:.2f}"
        theme = context.theme
        
        return f"""
        <div class="card-header" style="margin-bottom: 16px;">
            <div class="title-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="badge" style="background:{theme.badge_bg}; color:{theme.badge_text}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; letter-spacing: 0.5px;">{ctype}</span>
                <span class="score-tag" style="font-size: 12px; color:{theme.text_muted};">Importance: <strong>{score}</strong></span>
            </div>
            <h2 class="concept-title" style="color:{theme.text_primary}; font-size: 19px; font-weight: 600; margin: 0;">{title}</h2>
        </div>
        """

    def _render_explanation(self, section: VisualSectionPlan, context: RenderContext) -> str:
        theme = context.theme
        explanation = self._escape(section.content.explanation)
        return f"""
        <div class="explanation-box" style="padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 14.5px; border-left: 4px solid {theme.accent}; background:{theme.accent_light};">
            <p style="color:{theme.text_primary}; margin: 0;">{explanation}</p>
        </div>
        """

    def _render_footer(self, section: VisualSectionPlan, context: RenderContext) -> str:
        concept = section.content
        theme = context.theme
        html_out = ""
        
        if concept.source:
            s_start = f"{concept.source.start:.1f}s"
            s_end = f"{concept.source.end:.1f}s"
            html_out += f'<div class="timestamp-tag" style="margin-top:12px; font-size:11px; color:{theme.text_muted}; text-align:right;">Source: {s_start} – {s_end}</div>'
            
        return html_out

    @abstractmethod
    def render_body(self, section: VisualSectionPlan, context: RenderContext) -> str:
        pass

    def render(self, section: VisualSectionPlan, context: RenderContext, bounds: BoundingBox) -> str:
        theme = context.theme
        header = self._render_header(section, context)
        explanation = self._render_explanation(section, context)
        body = self.render_body(section, context)
        footer = self._render_footer(section, context)
        
        return f"""
        <div class="visual-card" id="{section.id}" style="background:{theme.card_bg}; border:1px solid {theme.card_border}; box-shadow:{theme.shadow}; border-radius: 10px; padding: 22px;">
            {header}
            <div class="card-body">
                {explanation}
                {body}
            </div>
            {footer}
        </div>
        """
