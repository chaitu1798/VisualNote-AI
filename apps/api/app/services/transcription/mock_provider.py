from typing import Optional
import logging
from app.services.transcription.base import TranscriptionProvider, TranscriptionResult
from app.services.transcription.cleaning import TranscriptCleaner
from app.fixtures.sample_transcripts import SAMPLE_TRANSCRIPTS

logger = logging.getLogger(__name__)


class MockTranscriptionProvider(TranscriptionProvider):
    """Deterministic mock transcription provider for local development, CI, and tracer bullet testing."""

    async def transcribe(
        self,
        source_data: bytes,
        filename: str = "audio.wav",
        mime_type: Optional[str] = None
    ) -> TranscriptionResult:
        logger.info(f"MockTranscriptionProvider: transcribing {len(source_data)} bytes from '{filename}'")

        lower_name = filename.lower()
        if "db" in lower_name or "sql" in lower_name:
            chosen = SAMPLE_TRANSCRIPTS["relational_databases"]["text"]
        elif "tcp" in lower_name or "network" in lower_name:
            chosen = SAMPLE_TRANSCRIPTS["tcp_handshake"]["text"]
        elif "ml" in lower_name or "metric" in lower_name:
            chosen = SAMPLE_TRANSCRIPTS["machine_learning_metrics"]["text"]
        else:
            chosen = SAMPLE_TRANSCRIPTS["operating_systems"]["text"]

        cleaned_text, segments, duration = TranscriptCleaner.process(chosen)
        return TranscriptionResult(
            text=cleaned_text,
            segments=segments,
            language="en",
            duration=duration,
            provider="mock"
        )

    async def transcribe_text(
        self,
        text: str,
        language: str = "en"
    ) -> TranscriptionResult:
        logger.info("MockTranscriptionProvider: processing raw text input")
        cleaned_text, segments, duration = TranscriptCleaner.process(text)
        return TranscriptionResult(
            text=cleaned_text,
            segments=segments,
            language=language,
            duration=duration,
            provider="mock"
        )
