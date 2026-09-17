import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transcript import Transcript as DBTranscript
from app.models.project import Project
from app.schemas.transcript import (
    TranscriptCreate,
    TranscriptResponse,
    CleanedTranscriptResponse,
    TranscriptSegment,
)
from app.services.transcription.cleaning import TranscriptCleaner, TranscriptCleaningError

router = APIRouter()


@router.post("/clean", response_model=CleanedTranscriptResponse)
def clean_transcript(payload: TranscriptCreate):
    """Normalizes and cleans raw transcript text while preserving technical terms and formulas."""
    try:
        segments_data = [s.model_dump() for s in payload.segments] if payload.segments else None
        cleaned_text, segments, duration = TranscriptCleaner.process(payload.content, segments_data)
        words = len(cleaned_text.split())
        return CleanedTranscriptResponse(
            raw_text=payload.content,
            cleaned_text=cleaned_text,
            word_count=words,
            estimated_duration_sec=duration,
            segments=segments,
        )
    except TranscriptCleaningError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.post("/", response_model=TranscriptResponse, status_code=status.HTTP_201_CREATED)
def create_transcript(payload: TranscriptCreate, db: Session = Depends(get_db)):
    """Ingests, cleans, and stores an educational transcript."""
    try:
        segments_data = [s.model_dump() for s in payload.segments] if payload.segments else None
        cleaned_text, segments, duration = TranscriptCleaner.process(payload.content, segments_data)
    except TranscriptCleaningError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    project_id = payload.project_id
    if project_id:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )
        # Delete old transcript for project if any
        db.query(DBTranscript).filter(DBTranscript.project_id == project_id).delete()

    tr_id = f"tr-{uuid.uuid4().hex[:8]}"
    db_transcript = DBTranscript(
        id=tr_id,
        project_id=project_id,
        source_id=payload.source_id,
        language=payload.language,
        content=cleaned_text,
        duration=duration,
        segments=[s.model_dump() for s in segments],
        created_at=datetime.now(timezone.utc),
    )

    if project_id:
        db.add(db_transcript)
        db.commit()
        db.refresh(db_transcript)

    return TranscriptResponse(
        id=tr_id,
        project_id=project_id,
        source_id=payload.source_id,
        language=payload.language,
        content=cleaned_text,
        duration=duration,
        segments=segments,
        created_at=db_transcript.created_at,
    )


@router.get("/{transcript_id}", response_model=TranscriptResponse)
def get_transcript(transcript_id: str, db: Session = Depends(get_db)):
    """Retrieves a transcript by ID."""
    tr = db.query(DBTranscript).filter(DBTranscript.id == transcript_id).first()
    if not tr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript '{transcript_id}' not found."
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
