from typing import Protocol

from app.agent.schemas import AgentRequest


class LLM(Protocol):
    """Application-level interface for a language model."""

    def invoke(self, user_input: str) -> AgentRequest:
        """Interpret user input and return structured agent parameters."""
        ...
