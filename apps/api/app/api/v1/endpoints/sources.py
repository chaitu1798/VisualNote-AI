import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.source import Source
from app.models.project import Project
from app.services.media.media_processor import get_media_processor, MediaProcessingError
from app.services.storage_service import get_storage_service

router = APIRouter()


@router.get("/status")
def get_source_status():
    """Source processing status placeholder."""
    return {"status": "ready"}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_or_upload_source(
    file: Optional[UploadFile] = File(None),
    source_type: str = Form("upload"),
    project_id: Optional[str] = Form(None),
    raw_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Uploads an educational video/audio file or registers a text source.
    Validates file extension, size, and MIME type strictly.
    """
    media_processor = get_media_processor()
    storage = get_storage_service()

    # If project_id provided, verify project exists
    if project_id:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )

    source_id = f"src-{uuid.uuid4().hex[:8]}"

    if file:
        file_bytes = await file.read()
        try:
            sanitized_name, resolved_mime = media_processor.validate_file(
                filename=file.filename or "upload.mp4",
                file_size=len(file_bytes),
                content_type=file.content_type
            )
        except MediaProcessingError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": exc.code, "message": exc.message}
            )

        storage_key = f"uploads/{source_id}_{sanitized_name}"
        storage_path = storage.save(storage_key, file_bytes, resolved_mime)

        return {
            "source_id": source_id,
            "project_id": project_id,
            "source_type": "upload",
            "filename": sanitized_name,
            "mime_type": resolved_mime,
            "file_size": len(file_bytes),
            "storage_key": storage_key,
            "storage_url": storage.get_url(storage_key),
            "status": "ready",
        }
    elif raw_text:
        return {
            "source_id": source_id,
            "project_id": project_id,
            "source_type": "text",
            "character_count": len(raw_text),
            "status": "ready",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a media file or raw_text must be provided."
        )
