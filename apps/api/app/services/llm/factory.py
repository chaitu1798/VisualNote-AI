from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.openai_provider import OpenAIProvider

_llm_provider = None


def get_llm_provider() -> LLMProvider:
    global _llm_provider
    if _llm_provider is None:
        if settings.MOCK_AI or settings.AI_PROVIDER == "mock":
            _llm_provider = MockLLMProvider()
        elif settings.AI_PROVIDER == "openai":
            _llm_provider = OpenAIProvider()
        else:
            _llm_provider = MockLLMProvider()
    return _llm_provider
