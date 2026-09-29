import html
from typing import List
from app.schemas.visual_plan import VisualPlanResponse, VisualSectionPlan
from app.services.renderer.core.context import RenderContext, ComponentRenderResult, RenderError
from app.services.renderer.core.layout_engine import LayoutEngine
from app.services.renderer.theme import get_theme
from app.services.renderer.components.factory import ComponentFactory

class PageComposer:
    def __init__(self, plan: VisualPlanResponse):
        self.plan = plan
        self.theme = get_theme(plan.theme)
        self.context = RenderContext(theme=self.theme)
        
    def _escape(self, text: str) -> str:
        return html.escape(str(text or ""), quote=True)
        
    def render(self) -> str:
        html_pages = []
        current_page_components = []
        
        # 120px rough header height + footer
        header_footer_allowance = 150.0 
        self.context.current_y = self.context.margins["top"] + header_footer_allowance
        
        for section in self.plan.sections:
            bounds = LayoutEngine.compute_component_bounds(section, self.context, self.context.current_y)
            
            if bounds.bottom > (self.context.max_y - header_footer_allowance):
                if len(current_page_components) > 0:
                    html_pages.append(self._render_page(current_page_components))
                    current_page_components = []
                    self.context.current_page += 1
                    self.context.current_y = self.context.margins["top"] + header_footer_allowance
                    bounds = LayoutEngine.compute_component_bounds(section, self.context, self.context.current_y)
                    
                if bounds.height > (self.context.max_y - self.context.margins["top"] - header_footer_allowance):
                    self.context.errors.append(RenderError(
                        code="LAYOUT_OVERFLOW", 
                        component_id=section.id, 
                        message="Component exceeds single page bounds"
                    ))
            
            renderer = ComponentFactory.get_renderer(section.visual_type)
            comp_html = renderer.render(section, self.context, bounds)
            current_page_components.append(comp_html)
            
            self.context.current_y = bounds.bottom + 24 
            
        if current_page_components:
            html_pages.append(self._render_page(current_page_components))
            
        return self._wrap_document(html_pages)
        
    def _render_page(self, component_htmls: List[str]) -> str:
        title = self._escape(self.plan.page_title)
        theme = self.theme
        
        header = f"""
        <header class="page-header">
            <div class="header-title-box">
                <div class="header-tag">Visual Study Note • FYP Core Pipeline</div>
                <h1>{title}</h1>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
                <div class="brand-badge">VisualNote AI</div>
                <div class="page-number">Page {self.context.current_page}</div>
            </div>
        </header>
        """
        
        footer = f"""
        <footer class="page-footer">
            <span>Generated deterministically from structured knowledge</span>
            <span>Style: {theme.name}</span>
        </footer>
        """
        
        content = "\n".join(component_htmls)
        
        return f"""
        <div class="note-page" style="width: {self.context.page_width}px; min-height: {self.context.page_height}px;">
            {header}
            <main class="sections-container">
                {content}
            </main>
            {footer}
        </div>
        """
        
    def _wrap_document(self, pages: List[str]) -> str:
        title = self._escape(self.plan.page_title)
        theme = self.theme
        pages_html = "\n".join(pages)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src data:;">
    <title>{title} — VisualNote AI</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: {theme.background};
            color: {theme.text_primary};
            font-family: {theme.font_family};
            line-height: 1.5;
            padding: 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 24px;
        }}
        .note-page {{
            background-color: {theme.page_bg};
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
            border: 1px solid {theme.card_border};
            word-wrap: break-word;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        .page-header {{
            border-bottom: 2px solid {theme.card_border};
            padding-bottom: 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-shrink: 0;
        }}
        .header-title-box h1 {{ font-size: 26px; font-weight: 700; color: {theme.text_primary}; letter-spacing: -0.5px; }}
        .header-tag {{ font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: {theme.accent}; margin-bottom: 6px; }}
        .brand-badge {{
            background: {theme.accent_light};
            color: {theme.accent};
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }}
        .page-number {{
            font-size: 12px;
            font-weight: bold;
            color: {theme.text_muted};
        }}
        .sections-container {{ flex-grow: 1; display: flex; flex-direction: column; gap: 24px; }}
        .page-footer {{
            margin-top: auto;
            padding-top: 16px;
            border-top: 1px solid {theme.card_border};
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: {theme.text_muted};
            flex-shrink: 0;
        }}
    </style>
</head>
<body>
    {pages_html}
</body>
</html>"""
