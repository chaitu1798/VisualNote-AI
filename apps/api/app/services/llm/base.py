from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.transcript import TranscriptSegment
from app.schemas.concept import ConceptAnalysisResponse


class LLMProvider(ABC):
    """Abstract base class for LLM content analysis and structured concept extraction."""

    @abstractmethod
    async def extract_concepts(
        self,
        transcript_text: str,
        segments: Optional[List[TranscriptSegment]] = None,
        learning_level: str = "INTERMEDIATE"
    ) -> ConceptAnalysisResponse:
        """
        Extracts structured, validated ConceptJSON from educational transcript text.
        Must return a validated ConceptAnalysisResponse matching Pydantic schemas.
        """
        pass
