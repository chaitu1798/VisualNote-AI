import io
import re
import uuid
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

from app.models.source import Source, SourceTypeEnum, SourceStatusEnum
from app.models.project import Project
from app.models.transcript import Transcript, TranscriptProviderEnum
from app.models.user import User
from app.services.media.media_processor import get_media_processor, MediaProcessingError
from app.services.storage_service import get_storage_provider
from app.services.transcription.cleaning import TranscriptCleaner, TranscriptCleaningError

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".mp4", ".m4a", ".webm", ".mov", ".txt", ".pdf"}


class SourceIngestionError(Exception):
    """Custom error during source ingestion."""
    def __init__(self, message: str, code: str = "INGESTION_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class SourceIngestionService:
    """
    Modular business logic service for educational source ingestion:
    - Text ingestion
    - File upload (Audio/Video/Documents)
    - Transcript ingestion
    - YouTube reference ingestion (metadata & reference only, no unauthorized downloading)
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.media_processor = get_media_processor()
        self.storage = get_storage_provider()

    def _get_db(self, db: Optional[Session] = None) -> Optional[Session]:
        return db or self.db

    def _ensure_project(self, db: Session, project_id: Optional[str] = None, title: Optional[str] = None) -> Project:
        """Retrieves an existing project or provisions a default project."""
        if project_id:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if not proj:
                raise SourceIngestionError(f"Project '{project_id}' not found.", code="PROJECT_NOT_FOUND")
            return proj

        # Provision a default project if none supplied
        user = db.query(User).first()
        if not user:
            user = User(
                id=f"user-{uuid.uuid4().hex[:8]}",
                email="developer@visualnote.ai",
                name="Developer User",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        proj = Project(
            id=f"proj-{uuid.uuid4().hex[:8]}",
            user_id=user.id,
            title=title or "Educational Learning Note",
            status="PROCESSING",
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)
        return proj

    def ingest_text(
        self,
        raw_text: Optional[str] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        project_id: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Source:
        """Validates and ingests raw educational text into persistent Source & Transcript records."""
        active_text = content if content is not None else raw_text
        if not active_text or not active_text.strip():
            raise SourceIngestionError("Text content cannot be empty.", code="EMPTY_TEXT")

        text = active_text.strip()
        active_db = self._get_db(db)
        proj = self._ensure_project(active_db, project_id=project_id, title=title) if active_db else None

        source_id = f"src-{uuid.uuid4().hex[:8]}"
        resolved_title = title or (text[:60] + "..." if len(text) > 60 else text)

        source = Source(
            id=source_id,
            project_id=proj.id if proj else "proj-orphan",
            source_type=SourceTypeEnum.text,
            title=resolved_title,
            original_filename=None,
            mime_type="text/plain",
            file_size=len(text.encode("utf-8")),
            duration=None,
            storage_key=None,
            source_url=None,
            status=SourceStatusEnum.processed,
            meta_data={
                **(meta_data or {}),
                "character_count": len(text),
                "word_count": len(text.split()),
                "raw_text": text,
            },
        )

        if active_db:
            active_db.add(source)
            active_db.commit()
            active_db.refresh(source)

            # Persist automatic Transcript record
            tr_id = f"tr-{uuid.uuid4().hex[:8]}"
            if proj:
                active_db.query(Transcript).filter(Transcript.project_id == proj.id).delete()
            transcript = Transcript(
                id=tr_id,
                project_id=proj.id if proj else "proj-orphan",
                source_id=source.id,
                language="en",
                content=text,
                raw_content=text,
                duration=None,
                provider=TranscriptProviderEnum.manual_text,
            )
            active_db.add(transcript)
            active_db.commit()

        return source

    def ingest_transcript(
        self,
        raw_content: Optional[str] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        language: str = "en",
        project_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Source:
        """Parses and ingests a pre-existing educational transcript."""
        active_text = content if content is not None else raw_content
        if not active_text or not active_text.strip():
            raise SourceIngestionError("Transcript content cannot be empty.", code="EMPTY_TRANSCRIPT")

        text = active_text.strip()
        cleaned_text, parsed_segments, duration = TranscriptCleaner.process(text, None)

        active_db = self._get_db(db)
        proj = self._ensure_project(active_db, project_id=project_id, title=title or "Imported Transcript") if active_db else None

        source_id = f"src-{uuid.uuid4().hex[:8]}"
        resolved_title = title or "Imported Transcript"

        source = Source(
            id=source_id,
            project_id=proj.id if proj else "proj-orphan",
            source_type=SourceTypeEnum.transcript,
            title=resolved_title,
            original_filename=None,
            mime_type="text/plain",
            file_size=len(text.encode("utf-8")),
            duration=duration,
            storage_key=None,
            source_url=None,
            status=SourceStatusEnum.processed,
            meta_data={
                "segment_count": len(parsed_segments),
                "duration_sec": duration,
                "raw_text": text,
            },
        )

        if active_db:
            active_db.add(source)
            active_db.commit()
            active_db.refresh(source)

            tr_id = f"tr-{uuid.uuid4().hex[:8]}"
            if proj:
                active_db.query(Transcript).filter(Transcript.project_id == proj.id).delete()
            transcript = Transcript(
                id=tr_id,
                project_id=proj.id if proj else "proj-orphan",
                source_id=source.id,
                language=language,
                content=cleaned_text,
                raw_content=text,
                duration=duration,
                segments=[s.model_dump() for s in parsed_segments],
                provider=TranscriptProviderEnum.manual_transcript,
            )
            active_db.add(transcript)
            active_db.commit()

        return source

    def ingest_youtube_reference(
        self,
        source_url: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None,
        raw_transcript: Optional[str] = None,
        project_id: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Source:
        """
        Stores metadata and reference for an educational YouTube video.
        Strictly references metadata; no unauthorized media scraping.
        """
        active_url = url or source_url
        if not active_url or ("youtube.com" not in active_url and "youtu.be" not in active_url):
            raise ValueError("Invalid YouTube URL format")

        parsed = urlparse(active_url)
        video_id = None
        if "youtu.be" in parsed.netloc:
            video_id = parsed.path.lstrip("/")
        elif "youtube.com" in parsed.netloc:
            qs = parse_qs(parsed.query)
            video_id = qs.get("v", [None])[0]

        if not video_id:
            # Fallback regex search
            m = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", active_url)
            if m:
                video_id = m.group(1)

        active_db = self._get_db(db)
        proj = self._ensure_project(active_db, project_id=project_id, title=title or "YouTube Educational Reference") if active_db else None
        source_id = f"src-{uuid.uuid4().hex[:8]}"

        metadata_dict = {
            **(meta_data or {}),
            "video_id": video_id,
            "ingestion_type": "metadata_reference_only",
            "reference_only": True,
            "policy": "No unauthorized scraper / stream download",
        }
        if raw_transcript:
            metadata_dict["raw_text"] = raw_transcript

        source = Source(
            id=source_id,
            project_id=proj.id if proj else "proj-orphan",
            source_type=SourceTypeEnum.youtube,
            title=title or "YouTube Educational Reference",
            original_filename=None,
            mime_type=None,
            file_size=None,
            duration=None,
            storage_key=None,
            source_url=active_url,
            status=SourceStatusEnum.processed,
            meta_data=metadata_dict,
        )

        if active_db:
            active_db.add(source)
            active_db.commit()
            active_db.refresh(source)

            if raw_transcript and raw_transcript.strip():
                cleaned_text, parsed_segments, duration = TranscriptCleaner.process(raw_transcript, None)
                tr_id = f"tr-{uuid.uuid4().hex[:8]}"
                if proj:
                    active_db.query(Transcript).filter(Transcript.project_id == proj.id).delete()
                transcript = Transcript(
                    id=tr_id,
                    project_id=proj.id if proj else "proj-orphan",
                    source_id=source.id,
                    language="en",
                    content=cleaned_text,
                    raw_content=raw_transcript,
                    duration=duration,
                    segments=[s.model_dump() for s in parsed_segments],
                    provider=TranscriptProviderEnum.manual_transcript,
                )
                active_db.add(transcript)
                active_db.commit()

        return source

    def ingest_file(
        self,
        filename: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        file_obj: Any = None,
        content_type: Optional[str] = None,
        title: Optional[str] = None,
        project_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Source:
        """Validates and stores an educational file safely."""
        if file_obj is not None:
            if hasattr(file_obj, "read"):
                file_bytes = file_obj.read()
            elif isinstance(file_obj, bytes):
                file_bytes = file_obj

        if not file_bytes:
            raise SourceIngestionError("Uploaded file cannot be empty.", code="EMPTY_FILE")

        active_filename = filename or "upload.bin"
        ext = ("." + active_filename.split(".")[-1].lower()) if "." in active_filename else ""
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {ext}")

        active_db = self._get_db(db)
        if ext in {".txt", ".pdf"}:
            sanitized_name = self.media_processor.sanitize_filename(active_filename)
            resolved_mime = content_type or ("text/plain" if ext == ".txt" else "application/pdf")
        else:
            try:
                sanitized_name, resolved_mime = self.media_processor.validate_file(
                    filename=active_filename,
                    file_size=len(file_bytes),
                    content_type=content_type or "application/octet-stream",
                )
            except MediaProcessingError as exc:
                if "unsupported" in str(exc).lower():
                    raise ValueError(f"Unsupported file extension: {ext}")
                raise SourceIngestionError(exc.message, code=exc.code)

        proj = self._ensure_project(active_db, project_id=project_id, title=title or sanitized_name) if active_db else None

        source_id = f"src-{uuid.uuid4().hex[:8]}"
        storage_key = f"uploads/{source_id}_{sanitized_name}"
        self.storage.save(storage_key, file_bytes, resolved_mime)

        if resolved_mime.startswith("video/"):
            source_type = SourceTypeEnum.video
        elif resolved_mime.startswith("audio/"):
            source_type = SourceTypeEnum.audio
        else:
            source_type = SourceTypeEnum.text

        source = Source(
            id=source_id,
            project_id=proj.id if proj else "proj-orphan",
            source_type=source_type,
            title=title or sanitized_name,
            original_filename=sanitized_name,
            mime_type=resolved_mime,
            file_size=len(file_bytes),
            duration=None,
            storage_key=storage_key,
            source_url=None,
            status=SourceStatusEnum.processed,
            meta_data={
                "file_size_bytes": len(file_bytes),
                "original_filename": sanitized_name,
            },
        )

        if active_db:
            active_db.add(source)
            active_db.commit()
            active_db.refresh(source)

        return source

    def get_source_transcript(self, source_id: str, db: Optional[Session] = None) -> Optional[Transcript]:
        """Retrieves transcript record associated with source_id."""
        active_db = self._get_db(db)
        if not active_db:
            return None
        return active_db.query(Transcript).filter(Transcript.source_id == source_id).first()


_source_ingestion_service: Optional[SourceIngestionService] = None


def get_source_ingestion_service() -> SourceIngestionService:
    global _source_ingestion_service
    if _source_ingestion_service is None:
        _source_ingestion_service = SourceIngestionService()
    return _source_ingestion_service
