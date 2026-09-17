from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass, field
from app.schemas.transcript import TranscriptSegment


@dataclass
class TranscriptionResult:
    text: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    language: str = "en"
    duration: float = 0.0
    provider: str = "mock"


class TranscriptionProvider(ABC):
    """Abstract base class for all speech-to-text / transcription providers."""

    @abstractmethod
    async def transcribe(
        self,
        source_data: bytes,
        filename: str = "audio.wav",
        mime_type: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribes raw audio/video bytes into timestamped transcript segments."""
        pass

    @abstractmethod
    async def transcribe_text(
        self,
        text: str,
        language: str = "en"
    ) -> TranscriptionResult:
        """Ingests and cleans raw transcript text with timestamped segmentation."""
        pass
