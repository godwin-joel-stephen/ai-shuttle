from datetime import date, timedelta

import pytest

from app.agent.fake_llm import FakeLLM
from app.agent.llm import LLMUnavailableError
from app.agent.schemas import AgentIntent
from app.graph.booking_graph import create_booking_graph
from tests.conftest import TODAY, TOMORROW




class FailingLLM:
    def invoke(self, user_input: str):
        raise TimeoutError("model timed out")


def test_natural_language_request_books_via_llm(db, user_id):
    graph = create_booking_graph(db, FakeLLM(reference_date=TODAY))

    result = graph.invoke(
        {
            "user_id": user_id,
            "user_input": "Book my usual shuttle for tomorrow.",
        }
    )

    assert result["intent"] == AgentIntent.BOOK_USUAL_SHUTTLE
    assert result["booking_date"] == TOMORROW
    assert result["already_booked"] is False
    assert result["response"].startswith(
        "Done. You're booked on the 7:30 AM shuttle from Home to Office"
    )


def test_structured_request_skips_llm(db, user_id):
    graph = create_booking_graph(db, FailingLLM())

    result = graph.invoke(
        {
            "user_id": user_id,
            "intent": AgentIntent.BOOK_USUAL_SHUTTLE,
            "booking_date": TOMORROW,
        }
    )

    assert result["booking"].booking_date == TOMORROW


def test_llm_failure_is_reported(db, user_id):
    graph = create_booking_graph(db, FailingLLM())

    with pytest.raises(LLMUnavailableError):
        graph.invoke(
            {
                "user_id": user_id,
                "user_input": "Book my usual shuttle for tomorrow.",
            }
        )
