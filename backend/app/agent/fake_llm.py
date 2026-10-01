from datetime import date

from app.agent.date_resolver import resolve_tomorrow
from app.agent.schemas import AgentIntent, AgentRequest


class FakeLLM:
    """Deterministic LLM stand-in used for local development."""

    def __init__(self, reference_date: date):
        self.reference_date = reference_date

    def invoke(self, user_input: str) -> AgentRequest:
        normalized = user_input.strip().lower()

        if normalized == "book my usual shuttle for tomorrow.":
            return AgentRequest(
                intent=AgentIntent.BOOK_USUAL_SHUTTLE,
                booking_date=resolve_tomorrow(self.reference_date),
            )

        raise ValueError("Unsupported booking request.")
