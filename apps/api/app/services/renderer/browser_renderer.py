import html
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional
import logging

from app.core.config import settings
from app.schemas.visual_plan import VisualPlanResponse
from app.schemas.generation import RenderResponse
from app.services.renderer.concept_card_renderer import ConceptCardRenderer
from app.services.renderer.theme import get_theme
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

DEFAULT_BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


class BrowserRenderer:
    """
    Renders visual note HTML deterministically to high-resolution PNG using
    headless Chromium/Edge, with pure SVG/HTML vector fallback.
    """

    def __init__(self, browser_path: Optional[str] = None):
        self.browser_path = browser_path or self._detect_browser()
        self.storage = get_storage_service()

    def _detect_browser(self) -> Optional[str]:
        # 1. Check explicit setting / env var
        custom_path = settings.BROWSER_EXECUTABLE_PATH or os.environ.get("BROWSER_PATH")
        if custom_path and os.path.exists(custom_path):
            logger.info(f"Using explicitly configured browser: {custom_path}")
            return custom_path

        # 2. Check candidate paths
        for p in DEFAULT_BROWSER_CANDIDATES:
            if os.path.exists(p):
                logger.info(f"Detected browser for deterministic rendering: {p}")
                return p

        # 3. Check PATH
        for cmd in ("chrome", "google-chrome", "chromium", "msedge"):
            found = shutil.which(cmd)
            if found:
                logger.info(f"Detected browser in PATH: {found}")
                return found

        logger.warning("No headless Chromium/Edge browser detected; using SVG vector image fallback.")
        return None

    def render_visual_plan(self, visual_plan: VisualPlanResponse) -> RenderResponse:
        """
        Renders a VisualPlanResponse into HTML, SVG, and PNG files.
        """
        base_id = f"note_{uuid.uuid4().hex[:10]}"
        html_content = ConceptCardRenderer.render_page_html(visual_plan)

        # 1. Save HTML to storage
        html_key = f"generated/{base_id}.html"
        html_storage_path = self.storage.save(html_key, html_content.encode("utf-8"), "text/html")
        html_url = self.storage.get_url(html_key)

        # 2. Generate and save standalone SVG vector image
        svg_content = self._generate_svg_card(visual_plan)
        svg_key = f"generated/{base_id}.svg"
        svg_storage_path = self.storage.save(svg_key, svg_content.encode("utf-8"), "image/svg+xml")
        svg_url = self.storage.get_url(svg_key)

        # 3. Render PNG screenshot if headless browser is available
        image_url = None
        image_storage_path = None
        png_key = f"generated/{base_id}.png"

        # Resolve absolute local path for browser
        abs_html_path = Path(html_storage_path).resolve()
        abs_png_path = abs_html_path.with_suffix(".png")

        if self.browser_path and abs_html_path.exists():
            file_url = abs_html_path.as_uri()
            cmd = [
                self.browser_path,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--hide-scrollbars",
                "--window-size=920,1350",
                f"--screenshot={str(abs_png_path)}",
                file_url,
            ]
            try:
                logger.info(f"Rendering visual note screenshot with {self.browser_path}...")
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
                if proc.returncode == 0 and abs_png_path.exists():
                    png_bytes = abs_png_path.read_bytes()
                    self.storage.save(png_key, png_bytes, "image/png")
                    image_url = self.storage.get_url(png_key)
                    image_storage_path = str(abs_png_path.as_posix())
                    logger.info(f"Successfully generated PNG visual note: {abs_png_path}")
                else:
                    logger.warning(
                        f"Browser screenshot exited with code {proc.returncode}: {proc.stderr.decode('utf-8', errors='ignore')[:150]}"
                    )
            except Exception as exc:
                logger.error(f"Failed to capture browser screenshot: {exc}")

        # If PNG failed or was unavailable, use the generated standalone SVG vector URL
        final_image_url = image_url or svg_url
        final_storage_path = image_storage_path or str(Path(svg_storage_path).as_posix())

        return RenderResponse(
            page_title=visual_plan.page_title,
            image_url=final_image_url,
            html_url=html_url,
            svg_content=svg_content,
            storage_path=final_storage_path,
            status="READY",
        )

    def _generate_svg_card(self, visual_plan: VisualPlanResponse) -> str:
        """Generates a standalone crisp vector SVG representation of the visual plan."""
        theme = get_theme(visual_plan.theme)
        title = html.escape(visual_plan.page_title, quote=True)

        sections = visual_plan.sections or []
        card_height = 200 + max(1, len(sections)) * 260
        total_height = max(550, card_height)

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 {total_height}" width="100%" height="100%">
  <defs>
    <style>
      .title {{ font-family: 'Inter', -apple-system, sans-serif; font-size: 24px; font-weight: bold; fill: {theme.text_primary}; }}
      .header-tag {{ font-family: sans-serif; font-size: 11px; font-weight: bold; fill: {theme.accent}; letter-spacing: 1px; text-transform: uppercase; }}
      .card-title {{ font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 600; fill: {theme.text_primary}; }}
      .badge-text {{ font-family: sans-serif; font-size: 11px; font-weight: bold; fill: {theme.badge_text}; }}
      .score-text {{ font-family: sans-serif; font-size: 11px; fill: {theme.text_muted}; }}
      .body-text {{ font-family: 'Inter', sans-serif; font-size: 13.5px; fill: {theme.text_secondary}; }}
      .bullet-text {{ font-family: sans-serif; font-size: 13px; fill: {theme.text_secondary}; }}
      .footer-text {{ font-family: sans-serif; font-size: 11px; fill: {theme.text_muted}; }}
    </style>
  </defs>

  <!-- Page Background -->
  <rect width="100%" height="100%" fill="{theme.page_bg}" rx="12" stroke="{theme.card_border}" stroke-width="1.5"/>

  <!-- Header -->
  <text x="40" y="44" class="header-tag">VISUAL STUDY NOTE • DETERMINISTIC PIPELINE</text>
  <text x="40" y="78" class="title">{title}</text>
  <rect x="740" y="32" width="100" height="24" rx="6" fill="{theme.accent_light}"/>
  <text x="790" y="48" font-family="sans-serif" font-size="11px" font-weight="bold" fill="{theme.accent}" text-anchor="middle">VisualNote AI</text>
  <line x1="40" y1="96" x2="840" y2="96" stroke="{theme.card_border}" stroke-width="1.5"/>
"""

        y = 120
        for i, sec in enumerate(sections):
            c = sec.content
            c_title = html.escape(c.title, quote=True)
            c_type = html.escape(c.concept_type.upper(), quote=True)
            c_exp = html.escape(c.explanation[:140], quote=True)
            c_score = f"{c.importance_score:.2f}" if c.importance_score is not None else "0.50"

            svg += f"""
  <!-- Section {i+1} Card -->
  <rect x="40" y="{y}" width="800" height="230" rx="10" fill="{theme.card_bg}" stroke="{theme.card_border}" stroke-width="1"/>
  <rect x="60" y="{y+16}" width="90" height="22" rx="4" fill="{theme.badge_bg}"/>
  <text x="105" y="{y+31}" class="badge-text" text-anchor="middle">{c_type}</text>
  <text x="820" y="{y+32}" class="score-text" text-anchor="end">Score: {c_score}</text>
  <text x="60" y="{y+62}" class="card-title">{c_title}</text>

  <!-- Explanation Box -->
  <rect x="60" y="{y+74}" width="760" height="42" rx="4" fill="{theme.accent_light}"/>
  <line x1="60" y1="{y+74}" x2="60" y2="{y+116}" stroke="{theme.accent}" stroke-width="3"/>
  <text x="74" y="{y+100}" class="body-text">{c_exp}</text>
"""
            # Key Points in Card
            pt_y = y + 138
            pts = c.supporting_points[:3] if c.supporting_points else ["Core technical concept"]
            for pt in pts:
                pt_text = html.escape(pt[:75], quote=True)
                svg += f"""
  <circle cx="68" cy="{pt_y}" r="3.5" fill="{theme.accent}"/>
  <text x="82" y="{pt_y+4}" class="bullet-text">{pt_text}</text>
"""
                pt_y += 24

            y += 250

        # Footer
        svg += f"""
  <line x1="40" y1="{y+10}" x2="840" y2="{y+10}" stroke="{theme.card_border}" stroke-width="1"/>
  <text x="40" y="{y+28}" class="footer-text">Deterministic Layout • Style: {theme.name}</text>
  <text x="840" y="{y+28}" class="footer-text" text-anchor="end">Verified Factual Knowledge</text>
</svg>"""
        return svg


_browser_renderer = None


def get_browser_renderer() -> BrowserRenderer:
    global _browser_renderer
    if _browser_renderer is None:
        _browser_renderer = BrowserRenderer()
    return _browser_renderer
