import os
import uuid
import subprocess
from pathlib import Path
import logging
from typing import List

from app.core.config import settings
from app.models.page import Page
from app.models.project import Project
from app.services.storage_service import get_storage_service
from app.services.renderer.browser_renderer import get_browser_renderer

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.storage = get_storage_service()
        self.browser_renderer = get_browser_renderer()
        self.browser_path = self.browser_renderer.browser_path

    def export_study_pack(self, project: Project, pages: List[Page]) -> str:
        """
        Generates a PDF Study Pack containing a cover page and all generated pages,
        and saves it to storage. Returns the storage_key.
        """
        if not self.browser_path:
            raise RuntimeError("PDF Export requires Headless Chrome/Edge, which was not found.")

        # Gather images
        # We need absolute local paths to images for the browser to render them in a local HTML file
        # The storage_key is usually "generated/note_xyz.png"
        storage_dir = Path(settings.STORAGE_LOCAL_DIR).resolve()

        # Build HTML
        html_parts = []
        html_parts.append("<html><head><style>")
        html_parts.append("""
            body { margin: 0; padding: 0; font-family: sans-serif; background: #fff; }
            .page { width: 100vw; height: 100vh; page-break-after: always; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-direction: column; }
            .cover { background: #f8fafc; }
            .cover h1 { font-size: 3rem; color: #1e293b; text-align: center; margin: 0 2rem; }
            .cover p { font-size: 1.2rem; color: #64748b; margin-top: 2rem; }
            .img-container { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
            img { max-width: 100%; max-height: 100%; object-fit: contain; }
            .page-number { position: absolute; bottom: 20px; right: 20px; font-size: 12px; color: #94a3b8; }
        """)
        html_parts.append("</style></head><body>")

        # Cover
        html_parts.append(f'<div class="page cover"><h1>{project.title or "Study Pack"}</h1><p>VisualNote AI</p></div>')

        # Pages
        sorted_pages = sorted(pages, key=lambda p: p.page_number)
        for i, page in enumerate(sorted_pages):
            if page.image_url:
                key = page.image_url.split("/storage/")[-1]
                img_path = storage_dir / key
                if img_path.exists():
                    img_uri = img_path.as_uri()
                    html_parts.append(f'<div class="page"><div class="img-container"><img src="{img_uri}" /></div><div class="page-number">{i + 1}</div></div>')

        html_parts.append("</body></html>")
        html_content = "".join(html_parts)

        # Write temp html
        tmp_id = uuid.uuid4().hex[:8]
        tmp_html_path = storage_dir / f"tmp_pdf_{tmp_id}.html"
        tmp_pdf_path = storage_dir / f"tmp_pdf_{tmp_id}.pdf"

        tmp_html_path.write_text(html_content, encoding="utf-8")

        pdf_key = f"exports/study_pack_{project.id}_{tmp_id}.pdf"

        try:
            file_url = tmp_html_path.as_uri()
            cmd = [
                self.browser_path,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--print-to-pdf-no-header",
                f"--print-to-pdf={str(tmp_pdf_path)}",
                file_url,
            ]
            logger.info(f"Rendering PDF with {self.browser_path}...")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            if proc.returncode == 0 and tmp_pdf_path.exists():
                pdf_bytes = tmp_pdf_path.read_bytes()
                self.storage.save(pdf_key, pdf_bytes, "application/pdf")
                logger.info(f"Successfully generated PDF: {pdf_key}")
            else:
                logger.error(f"PDF rendering failed: {proc.stderr.decode('utf-8', errors='ignore')}")
                raise RuntimeError("Failed to generate PDF via browser.")
        finally:
            if tmp_html_path.exists():
                tmp_html_path.unlink()
            if tmp_pdf_path.exists():
                tmp_pdf_path.unlink()

        return pdf_key

_pdf_service = None

def get_pdf_service() -> PDFService:
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service
