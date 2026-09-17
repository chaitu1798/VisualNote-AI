import html
from typing import List
from app.schemas.visual_plan import VisualPlanResponse, VisualSectionPlan
from app.services.renderer.theme import get_theme, ThemeStyle


class ConceptCardRenderer:
    """Deterministic HTML/CSS/SVG renderer for educational concept cards and visual learning notes."""

    @staticmethod
    def _escape(text: str) -> str:
        return html.escape(str(text or ""), quote=True)

    @classmethod
    def render_section_html(cls, sec: VisualSectionPlan, theme: ThemeStyle) -> str:
        concept = sec.content
        title = cls._escape(concept.title)
        ctype = cls._escape(concept.concept_type.upper())
        explanation = cls._escape(concept.explanation)
        score_val = concept.importance_score if concept.importance_score is not None else 0.50
        score = f"{score_val:.2f}"

        # Common Card Header
        html_out = f"""
        <div class="visual-card" style="background:{theme.card_bg}; border:1px solid {theme.card_border}; box-shadow:{theme.shadow};">
            <div class="card-header">
                <div class="title-row">
                    <span class="badge" style="background:{theme.badge_bg}; color:{theme.badge_text};">{ctype}</span>
                    <span class="score-tag">Importance: <strong>{score}</strong></span>
                </div>
                <h2 class="concept-title" style="color:{theme.text_primary};">{title}</h2>
            </div>
            <div class="card-body">
                <div class="explanation-box" style="border-left: 4px solid {theme.accent}; background:{theme.accent_light};">
                    <p style="color:{theme.text_primary};">{explanation}</p>
                </div>
        """

        # Template-specific layout rendering
        # 1. Flowchart / Process steps
        if concept.steps and len(concept.steps) > 0:
            html_out += '<div class="steps-flow">'
            for i, step in enumerate(concept.steps):
                step_num = i + 1
                sname = cls._escape(step.name)
                sdesc = cls._escape(step.description)
                html_out += f"""
                <div class="step-node" style="border: 1px solid {theme.card_border}; background:{theme.page_bg};">
                    <div class="step-badge" style="background:{theme.accent}; color:#ffffff;">{step_num}</div>
                    <div class="step-content">
                        <strong style="color:{theme.text_primary};">{sname}</strong>
                        <p style="color:{theme.text_secondary}; margin:2px 0 0 0; font-size:13px;">{sdesc}</p>
                    </div>
                </div>
                """
                if i < len(concept.steps) - 1:
                    html_out += f"""
                    <div class="step-arrow" style="color:{theme.accent};">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>
                    </div>
                    """
            html_out += '</div>'

        # 2. Formula block
        if concept.formula:
            f_expr = cls._escape(concept.formula.expression)
            f_exp = cls._escape(concept.formula.explanation)
            html_out += f"""
            <div class="formula-container" style="background:{theme.formula_bg}; border: 1px dashed {theme.card_border};">
                <div class="formula-expression" style="color:{theme.text_primary};">
                    <code>{f_expr}</code>
                </div>
                <div class="formula-explanation" style="color:{theme.text_secondary}; font-size:13px; margin-top:8px;">
                    <em>{f_exp}</em>
                </div>
            """
            if concept.formula.variables:
                html_out += '<div class="formula-vars" style="margin-top:10px; font-size:12px;">'
                html_out += f'<strong style="color:{theme.text_primary};">Variables:</strong><ul style="margin:4px 0 0 16px; padding:0;">'
                for var_k, var_v in concept.formula.variables.items():
                    html_out += f'<li style="color:{theme.text_secondary};"><code>{cls._escape(var_k)}</code>: {cls._escape(var_v)}</li>'
                html_out += '</ul></div>'
            html_out += '</div>'

        # 3. Comparison Table
        if concept.comparison:
            entities = concept.comparison.entities or []
            aspects = concept.comparison.aspects or {}
            ent0 = cls._escape(entities[0]) if len(entities) > 0 else "Entity A"
            ent1 = cls._escape(entities[1]) if len(entities) > 1 else "Entity B"

            html_out += f"""
            <div class="comparison-table-wrapper">
                <table class="comparison-table" style="border: 1px solid {theme.card_border}; width:100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background:{theme.accent_light};">
                            <th style="border: 1px solid {theme.card_border}; padding:8px; text-align:left; color:{theme.text_primary};">Aspect</th>
                            <th style="border: 1px solid {theme.card_border}; padding:8px; text-align:left; color:{theme.text_primary};">{ent0}</th>
                            <th style="border: 1px solid {theme.card_border}; padding:8px; text-align:left; color:{theme.text_primary};">{ent1}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for aspect_name, values in aspects.items():
                v0 = cls._escape(values[0]) if len(values) > 0 else ""
                v1 = cls._escape(values[1]) if len(values) > 1 else ""
                html_out += f"""
                <tr>
                    <td style="border: 1px solid {theme.card_border}; padding:8px; font-weight:600; color:{theme.text_primary};">{cls._escape(aspect_name)}</td>
                    <td style="border: 1px solid {theme.card_border}; padding:8px; color:{theme.text_secondary};">{v0}</td>
                    <td style="border: 1px solid {theme.card_border}; padding:8px; color:{theme.text_secondary};">{v1}</td>
                </tr>
                """
            html_out += """
                    </tbody>
                </table>
            </div>
            """

        # 4. Bullet List / Key Supporting Points
        if concept.supporting_points and len(concept.supporting_points) > 0:
            is_bullet_list_layout = sec.visual_type == "bullet_list"
            section_title = "Core Principles & Items" if is_bullet_list_layout else "Key Points"
            html_out += f'<div class="points-section"><h4 style="color:{theme.text_primary}; margin:12px 0 6px 0; font-size:14px; text-transform:uppercase; letter-spacing:0.5px;">{section_title}</h4><ul class="points-list">'
            for pt in concept.supporting_points:
                html_out += f"""
                <li style="color:{theme.text_secondary}; margin-bottom:4px;">
                    <span class="check-icon" style="color:{theme.accent};">✓</span> {cls._escape(pt)}
                </li>
                """
            html_out += '</ul></div>'

        # 5. Examples
        if concept.examples and len(concept.examples) > 0:
            html_out += f'<div class="examples-taglist" style="margin-top:10px;"><span style="font-size:12px; font-weight:600; color:{theme.text_muted}; margin-right:8px;">Examples:</span>'
            for ex in concept.examples:
                html_out += f'<span class="example-chip" style="background:{theme.page_bg}; border:1px solid {theme.card_border}; color:{theme.text_secondary}; padding:2px 8px; border-radius:12px; font-size:12px; margin-right:6px;">{cls._escape(ex)}</span>'
            html_out += '</div>'

        # Timestamp source range
        if concept.source:
            s_start = f"{concept.source.start:.1f}s"
            s_end = f"{concept.source.end:.1f}s"
            html_out += f'<div class="timestamp-tag" style="margin-top:12px; font-size:11px; color:{theme.text_muted}; text-align:right;">Source: {s_start} – {s_end}</div>'

        html_out += """
            </div>
        </div>
        """
        return html_out

    @classmethod
    def render_page_html(cls, visual_plan: VisualPlanResponse) -> str:
        """Renders complete HTML document for the visual note page with XSS prevention."""
        theme = get_theme(visual_plan.theme)
        title = cls._escape(visual_plan.page_title)

        sections_html = "\n".join(cls.render_section_html(sec, theme) for sec in (visual_plan.sections or []))

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Strict Content Security Policy to eliminate XSS execution in deterministic renders -->
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src data:;">
    <title>{title} — VisualNote AI</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            background-color: {theme.background};
            color: {theme.text_primary};
            font-family: {theme.font_family};
            line-height: 1.5;
            padding: 24px;
            display: flex;
            justify-content: center;
        }}
        .note-page {{
            width: 100%;
            max-width: 880px;
            background-color: {theme.page_bg};
            border-radius: 12px;
            padding: 36px 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
            border: 1px solid {theme.card_border};
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .page-header {{
            border-bottom: 2px solid {theme.card_border};
            padding-bottom: 20px;
            margin-bottom: 28px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .header-title-box h1 {{
            font-size: 26px;
            font-weight: 700;
            color: {theme.text_primary};
            letter-spacing: -0.5px;
            word-break: break-word;
        }}
        .header-tag {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: {theme.accent};
            margin-bottom: 6px;
        }}
        .brand-badge {{
            background: {theme.accent_light};
            color: {theme.accent};
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            flex-shrink: 0;
            margin-left: 12px;
        }}
        .sections-container {{
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        .visual-card {{
            border-radius: 10px;
            padding: 22px;
            transition: transform 0.2s ease;
            overflow: hidden;
        }}
        .title-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .badge {{
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }}
        .score-tag {{
            font-size: 12px;
            color: {theme.text_muted};
        }}
        .concept-title {{
            font-size: 19px;
            font-weight: 600;
            margin-bottom: 12px;
            word-break: break-word;
        }}
        .explanation-box {{
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 16px;
            font-size: 14.5px;
        }}
        .steps-flow {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin: 16px 0;
        }}
        .step-node {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: 8px;
        }}
        .step-badge {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            flex-shrink: 0;
        }}
        .step-arrow {{
            display: flex;
            justify-content: center;
            margin: -2px 0;
        }}
        .formula-container {{
            padding: 16px;
            border-radius: 8px;
            margin: 16px 0;
            text-align: center;
            word-break: break-all;
        }}
        .formula-expression {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 16px;
            font-weight: 600;
        }}
        .points-list {{
            list-style: none;
            padding: 0;
            margin: 8px 0;
        }}
        .points-list li {{
            font-size: 13.5px;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }}
        .check-icon {{
            font-weight: bold;
        }}
        .page-footer {{
            margin-top: 36px;
            padding-top: 16px;
            border-top: 1px solid {theme.card_border};
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: {theme.text_muted};
        }}
    </style>
</head>
<body>
    <div class="note-page" id="visual-note-container">
        <header class="page-header">
            <div class="header-title-box">
                <div class="header-tag">Visual Study Note • FYP Core Pipeline</div>
                <h1>{title}</h1>
            </div>
            <div class="brand-badge">VisualNote AI</div>
        </header>

        <main class="sections-container">
            {sections_html}
        </main>

        <footer class="page-footer">
            <span>Generated deterministically from structured knowledge</span>
            <span>Style: {theme.name}</span>
        </footer>
    </div>
</body>
</html>"""
        return html_doc
