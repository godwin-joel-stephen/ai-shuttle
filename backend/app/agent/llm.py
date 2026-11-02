from typing import Protocol

from app.agent.schemas import AgentRequest


class LLMUnavailableError(RuntimeError):
    """The model failed, timed out, or returned an unusable result."""


class LLM(Protocol):
    """Application-level interface for a language model."""

    def invoke(self, user_input: str) -> AgentRequest:
        """Interpret user input and return structured agent parameters."""
        ...
