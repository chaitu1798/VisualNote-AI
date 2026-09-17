from typing import List, Optional
import json
import logging
import httpx

from app.core.config import settings
from app.schemas.transcript import TranscriptSegment
from app.schemas.concept import ConceptAnalysisResponse
from app.services.llm.base import LLMProvider
from app.services.llm.mock_provider import MockLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI Structured Outputs provider with automatic fallback to mock provider."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.fallback = MockLLMProvider()

    async def extract_concepts(
        self,
        transcript_text: str,
        segments: Optional[List[TranscriptSegment]] = None,
        learning_level: str = "INTERMEDIATE"
    ) -> ConceptAnalysisResponse:
        if not self.api_key or settings.MOCK_AI:
            logger.info("OpenAI API key not provided or MOCK_AI=True; using MockLLMProvider.")
            return await self.fallback.extract_concepts(transcript_text, segments, learning_level)

        prompt = (
            f"You are an expert educational content analyzer. Extract key concepts from this educational lecture transcript. "
            f"Learning level: {learning_level}.\n\n"
            f"Transcript:\n{transcript_text[:6000]}\n\n"
            f"Return JSON adhering strictly to: title, summary, concepts (id, title, concept_type, importance_score, source, explanation, visual_type, supporting_points, examples, steps, comparison, formula)."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You analyze educational content and output valid JSON for VisualNote AI."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()

            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            validated = ConceptAnalysisResponse.model_validate(parsed)
            return validated
        except Exception as exc:
            logger.warning(f"OpenAI extraction failed ({exc}); falling back to MockLLMProvider.")
            return await self.fallback.extract_concepts(transcript_text, segments, learning_level)
