import io
from typing import Optional
import logging
import httpx

from app.core.config import settings
from app.services.transcription.base import TranscriptionProvider, TranscriptionResult
from app.services.transcription.cleaning import TranscriptCleaner
from app.services.transcription.mock_provider import MockTranscriptionProvider

logger = logging.getLogger(__name__)


class WhisperTranscriptionProvider(TranscriptionProvider):
    """OpenAI Whisper STT Provider with graceful fallback to mock mode."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.fallback = MockTranscriptionProvider()

    async def transcribe(
        self,
        source_data: bytes,
        filename: str = "audio.wav",
        mime_type: Optional[str] = None
    ) -> TranscriptionResult:
        if not self.api_key or settings.MOCK_AI:
            logger.info("OpenAI API key missing or MOCK_AI=True; using mock transcription fallback.")
            return await self.fallback.transcribe(source_data, filename, mime_type)

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        files = {"file": (filename, io.BytesIO(source_data), mime_type or "audio/wav")}
        data = {
            "model": "whisper-1",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "segment",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
                res_json = response.json()

            raw_text = res_json.get("text", "")
            raw_segments = res_json.get("segments", [])
            cleaned_text, segments, duration = TranscriptCleaner.process(raw_text, raw_segments)

            return TranscriptionResult(
                text=cleaned_text,
                segments=segments,
                language=res_json.get("language", "en"),
                duration=duration,
                provider="whisper"
            )
        except Exception as exc:
            logger.error(f"Whisper API transcription failed: {exc}. Falling back to mock provider.")
            return await self.fallback.transcribe(source_data, filename, mime_type)

    async def transcribe_text(
        self,
        text: str,
        language: str = "en"
    ) -> TranscriptionResult:
        return await self.fallback.transcribe_text(text, language)
