import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.source import Source
from app.models.transcript import Transcript
from app.schemas.source import SourceResponse
from app.schemas.transcript import TranscriptResponse, TranscriptSegment
from app.services.source_ingestion_service import get_source_ingestion_service, SourceIngestionError
from app.services.storage_service import get_storage_provider

router = APIRouter()


def _build_source_response(source: Source, db: Session) -> SourceResponse:
    storage = get_storage_provider()
    storage_url = storage.get_url(source.storage_key) if source.storage_key else None
    char_cnt = source.meta_data.get("character_count") if source.meta_data else None
    has_tr = db.query(Transcript).filter(
        (Transcript.source_id == source.id) | (Transcript.project_id == source.project_id)
    ).first() is not None

    return SourceResponse(
        id=source.id,
        project_id=source.project_id,
        source_type=source.source_type,
        title=source.title,
        original_filename=source.original_filename,
        mime_type=source.mime_type,
        file_size=source.file_size,
        duration=source.duration,
        storage_key=source.storage_key,
        storage_url=storage_url,
        source_url=source.source_url,
        status=source.status,
        character_count=char_cnt,
        has_transcript=has_tr,
        meta_data=source.meta_data,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.get("/status")
def get_source_status():
    """Source processing status check."""
    return {"status": "ready"}


@router.post("/text", response_model=SourceResponse, status_code=status.HTTP_200_OK)
async def create_text_source(
    request: Request,
    db: Session = Depends(get_db),
):
    """Direct JSON endpoint for educational text ingestion."""
    body = await request.json()
    text = body.get("text") or body.get("raw_text") or body.get("content")
    title = body.get("title")
    project_id = body.get("project_id")

    ingestion_service = get_source_ingestion_service()
    try:
        source = ingestion_service.ingest_text(
            raw_text=text,
            title=title,
            project_id=project_id,
            db=db,
        )
        return _build_source_response(source, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.post("/youtube", response_model=SourceResponse, status_code=status.HTTP_200_OK)
async def create_youtube_source(
    request: Request,
    db: Session = Depends(get_db),
):
    """Direct JSON endpoint for educational YouTube reference ingestion."""
    body = await request.json()
    url = body.get("url") or body.get("source_url")
    title = body.get("title")
    raw_transcript = body.get("raw_transcript") or body.get("transcript")
    project_id = body.get("project_id")

    ingestion_service = get_source_ingestion_service()
    try:
        source = ingestion_service.ingest_youtube_reference(
            source_url=url,
            title=title,
            raw_transcript=raw_transcript,
            project_id=project_id,
            db=db,
        )
        return _build_source_response(source, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_or_upload_source(
    request: Request,
    file: Optional[UploadFile] = File(None),
    source_type: str = Form("upload"),
    title: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    raw_text: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Uploads an educational video/audio file or registers a text/transcript/YouTube reference source.
    Delegates all parsing and validation to SourceIngestionService.
    Supports JSON body and multipart form data.
    """
    ingestion_service = get_source_ingestion_service()

    content_type = request.headers.get("content-type", "")

    # Handle pure JSON request body if applicable
    if "application/json" in content_type:
        body = await request.json()
        raw_text = body.get("raw_text") or body.get("text")
        source_type = body.get("source_type", "text")
        title = body.get("title")
        project_id = body.get("project_id")
        source_url = body.get("source_url") or body.get("url")

    try:
        if file and hasattr(file, "read"):
            file_bytes = await file.read()
            source = ingestion_service.ingest_file(
                filename=file.filename or "upload.mp4",
                file_bytes=file_bytes,
                content_type=file.content_type,
                title=title,
                project_id=project_id,
                db=db,
            )
        elif source_type == "youtube_reference" or source_url:
            source = ingestion_service.ingest_youtube_reference(
                source_url=source_url or "",
                title=title,
                raw_transcript=raw_text,
                project_id=project_id,
                db=db,
            )
        elif raw_text:
            source = ingestion_service.ingest_text(
                raw_text=raw_text,
                title=title,
                project_id=project_id,
                db=db,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either a media file, raw_text, or source_url must be provided."
            )

        return _build_source_response(source, db)

    except SourceIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message}
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.get("/{source_id}", response_model=SourceResponse)
def get_source_details(source_id: str, db: Session = Depends(get_db)):
    """Retrieves source metadata by ID."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found."
        )

    return _build_source_response(source, db)


@router.get("/{source_id}/transcript", response_model=TranscriptResponse)
def get_source_transcript(source_id: str, db: Session = Depends(get_db)):
    """Retrieves the transcript associated with the specified source ID."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found."
        )

    tr = db.query(Transcript).filter(Transcript.source_id == source_id).first()
    if not tr:
        # Fallback to project-level transcript if source_id wasn't populated
        tr = db.query(Transcript).filter(Transcript.project_id == source.project_id).first()

    if not tr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transcript found for source '{source_id}'."
        )

    segments = [TranscriptSegment(**s) for s in (tr.segments or [])]
    return TranscriptResponse(
        id=tr.id,
        project_id=tr.project_id,
        source_id=tr.source_id,
        language=tr.language,
        content=tr.content,
        duration=tr.duration,
        segments=segments,
        created_at=tr.created_at,
    )
