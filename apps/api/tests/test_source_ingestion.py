import io
import pytest
from app.services.source_ingestion_service import SourceIngestionService
from app.models.source import SourceTypeEnum, SourceStatusEnum
from app.models.transcript import TranscriptProviderEnum


def test_ingest_text(db_session):
    service = SourceIngestionService(db_session)
    text = "Machine learning is a field of inquiry devoted to understanding and building methods that 'learn'."
    source = service.ingest_text(content=text, title="ML Intro")

    assert source.id is not None
    assert source.type == SourceTypeEnum.text
    assert source.title == "ML Intro"
    assert source.status == SourceStatusEnum.processed
    assert source.meta_data.get("character_count") == len(text)

    # Verify transcript is automatically created
    transcript = service.get_source_transcript(source.id)
    assert transcript is not None
    assert transcript.content == text
    assert transcript.provider == TranscriptProviderEnum.manual_text


def test_ingest_transcript(db_session):
    service = SourceIngestionService(db_session)
    transcript_text = "00:00 Welcome to deep learning.\n00:15 Neural networks consist of layers."
    source = service.ingest_transcript(content=transcript_text, title="DL Lecture Transcript")

    assert source.id is not None
    assert source.type == SourceTypeEnum.transcript
    assert source.status == SourceStatusEnum.processed

    transcript = service.get_source_transcript(source.id)
    assert transcript is not None
    assert transcript.content == transcript_text
    assert transcript.provider == TranscriptProviderEnum.manual_transcript


def test_ingest_youtube_reference_valid(db_session):
    service = SourceIngestionService(db_session)
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    source = service.ingest_youtube_reference(url=url, title="Rick Astley Video")

    assert source.id is not None
    assert source.type == SourceTypeEnum.youtube
    assert source.url == url
    assert source.title == "Rick Astley Video"
    assert source.meta_data.get("video_id") == "dQw4w9WgXcQ"
    assert source.meta_data.get("ingestion_type") == "metadata_reference_only"


def test_ingest_youtube_reference_invalid_url(db_session):
    service = SourceIngestionService(db_session)
    url = "https://not-youtube.example.com/watch?v=123"

    with pytest.raises(ValueError, match="Invalid YouTube URL format"):
        service.ingest_youtube_reference(url=url)


def test_ingest_file_txt(db_session):
    service = SourceIngestionService(db_session)
    content = b"Content of an uploaded lecture note in plain text."
    file_obj = io.BytesIO(content)

    source = service.ingest_file(
        file_obj=file_obj,
        filename="lecture_notes.txt",
        content_type="text/plain",
        title="Lecture Note File"
    )

    assert source.id is not None
    assert source.original_filename == "lecture_notes.txt"
    assert source.file_path is not None
    assert source.meta_data.get("file_size_bytes") == len(content)


def test_ingest_file_unsupported_extension(db_session):
    service = SourceIngestionService(db_session)
    file_obj = io.BytesIO(b"executable content")

    with pytest.raises(ValueError, match="Unsupported file extension"):
        service.ingest_file(
            file_obj=file_obj,
            filename="malicious.exe",
            content_type="application/octet-stream"
        )
