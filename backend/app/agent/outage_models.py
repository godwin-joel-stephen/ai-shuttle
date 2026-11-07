"""Stand-in models used while the simulated LLM outage is on (app.core.outage).

They fail the way an unreachable provider does, without any network call,
so the agent's fallback chain, the 503 response and the error trace are the
real ones.
"""

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult

from app.agent.llm import LLMUnavailableError
from app.agent.schemas import AgentRequest


class LLMOutageError(LLMUnavailableError):
    """The simulated outage is on."""


OUTAGE_MESSAGE = "Simulated LLM outage: the model provider is unreachable."


class OutageChatModel(BaseChatModel):
    """A tool-calling chat model whose every call fails."""

    model_name: str = "simulated-outage"

    @property
    def _llm_type(self) -> str:
        return "simulated-outage"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "OutageChatModel":
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        raise LLMOutageError(f"{OUTAGE_MESSAGE} ({self.model_name})")


class OutageLLM:
    """The request interpreter for natural-language POST /bookings, failing."""

    def invoke(self, user_input: str) -> AgentRequest:
        raise LLMOutageError(OUTAGE_MESSAGE)
