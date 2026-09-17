from app.core.config import settings
from app.services.transcription.base import TranscriptionProvider
from app.services.transcription.mock_provider import MockTranscriptionProvider
from app.services.transcription.whisper_provider import WhisperTranscriptionProvider

_transcription_provider = None


def get_transcription_provider() -> TranscriptionProvider:
    global _transcription_provider
    if _transcription_provider is None:
        if settings.MOCK_AI or settings.TRANSCRIPTION_PROVIDER == "mock":
            _transcription_provider = MockTranscriptionProvider()
        elif settings.TRANSCRIPTION_PROVIDER == "whisper":
            _transcription_provider = WhisperTranscriptionProvider()
        else:
            _transcription_provider = MockTranscriptionProvider()
    return _transcription_provider
