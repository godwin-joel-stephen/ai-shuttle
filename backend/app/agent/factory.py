from datetime import date

from app.agent.gemini_llm import GeminiLLM
from app.agent.llm import LLM
from app.core.config import settings


def create_llm(reference_date: date) -> LLM:
    return GeminiLLM(
        api_key=settings.gemini_api_key,
        reference_date=reference_date,
    )