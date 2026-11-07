from datetime import date

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agent.gemini_llm import GeminiLLM
from app.agent.llm import LLM
from app.agent.outage_models import OutageChatModel, OutageLLM
from app.core.config import settings
from app.core.outage import is_llm_outage


def create_llm(reference_date: date) -> LLM:
    if is_llm_outage():
        return OutageLLM()

    return GeminiLLM(
        api_key=settings.gemini_api_key,
        reference_date=reference_date,
    )


def create_chat_model(model: str | None = None) -> BaseChatModel:
    """Tool-calling chat model for the assistant agent.

    Returned as LangChain's provider-neutral BaseChatModel, so another
    provider can be swapped in here without touching the graph or tools.
    """
    if is_llm_outage():
        return OutageChatModel(model_name=model or settings.agent_model)

    return ChatGoogleGenerativeAI(
        model=model or settings.agent_model,
        google_api_key=settings.gemini_api_key,
        # No temperature: Gemini 3.x uses fixed sampling and ignores it.
        timeout=20,
        # The fallback model is the retry; retrying an overloaded model
        # only adds latency.
        max_retries=0,
        # Booking requests need tool selection, not deep reasoning; minimal
        # thinking cut per-call latency from up to ~4s to ~1-1.5s.
        thinking_config={"thinking_level": "minimal"},
    )
