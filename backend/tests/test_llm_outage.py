"""F13: with the simulated LLM outage on, everything that doesn't need the
cloud model keeps working, and the assistant fails honestly.

These use the real model factory (no model overrides): during the outage it
hands out failing stand-ins, so the agent's whole fallback chain runs
without any network call.
"""

from contextlib import contextmanager, nullcontext

import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver
from sqlalchemy import select

from app.agent.factory import create_chat_model, create_llm
from app.agent.outage_models import LLMOutageError, OutageChatModel, OutageLLM
from app.api.assistant import UNAVAILABLE_MESSAGE, get_conversation_memory, get_policy_embedder
from app.core.config import settings
from app.db.database import get_db
from app.main import app
from app.models.booking import Booking
from tests.conftest import TODAY, TOMORROW
from tests.fake_embedder import FakeEmbedder


@pytest.fixture
def outage(outage_flag):
    outage_flag.set_llm_outage(True)
    return outage_flag


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    memory = InMemorySaver()
    app.dependency_overrides[get_conversation_memory] = lambda: memory
    app.dependency_overrides[get_policy_embedder] = FakeEmbedder

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def bookings(db, user_id) -> list[Booking]:
    return db.scalars(select(Booking).where(Booking.user_id == user_id)).all()


def test_switch_turns_on_and_off(outage_flag):
    assert not outage_flag.is_llm_outage()

    outage_flag.set_llm_outage(True)
    assert outage_flag.is_llm_outage()

    outage_flag.set_llm_outage(False)
    outage_flag.set_llm_outage(False)  # turning it off twice is fine
    assert not outage_flag.is_llm_outage()


def test_factory_hands_out_failing_models_only_during_outage(outage_flag):
    assert not isinstance(create_chat_model(), OutageChatModel)

    outage_flag.set_llm_outage(True)

    model = create_chat_model("gemini-3.1-flash-lite")
    assert isinstance(model, OutageChatModel)
    assert isinstance(create_llm(TODAY), OutageLLM)
    with pytest.raises(LLMOutageError, match="gemini-3.1-flash-lite"):
        model.bind_tools([]).invoke("hi")


def test_health_reports_the_outage(client, outage_flag):
    assert client.get("/health").json() == {"status": "ok", "llm": "ok"}

    outage_flag.set_llm_outage(True)

    assert client.get("/health").json() == {"status": "ok", "llm": "outage"}


def test_structured_booking_still_works(client, db, user_id, outage):
    # Siri "Book my usual shuttle", the widget and Control Center send this.
    response = client.post(
        "/bookings", json={"user_id": user_id, "booking_date": TOMORROW.isoformat()}
    )

    assert response.status_code == 200
    assert response.json()["message"].startswith("Done. You're booked on the 7:30 AM")


def test_earlier_later_still_works(client, user_id, outage):
    booking_id = client.post(
        "/bookings", json={"user_id": user_id, "booking_date": TOMORROW.isoformat()}
    ).json()["booking_id"]

    response = client.post(
        f"/bookings/{booking_id}/reschedule",
        json={"user_id": user_id, "direction": "earlier"},
    )

    assert response.status_code == 200


def test_habits_still_work(client, user_id, outage):
    response = client.get("/habits", params={"user_id": user_id})

    assert response.status_code == 200


def test_assistant_is_honestly_unavailable_and_changes_nothing(client, db, user_id, outage):
    response = client.post(
        "/assistant/messages",
        json={"user_id": user_id, "message": "Book my usual shuttle for tomorrow"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == UNAVAILABLE_MESSAGE
    assert "Book my usual shuttle" in UNAVAILABLE_MESSAGE
    assert bookings(db, user_id) == []


def test_assistant_tries_every_fallback_before_giving_up(client, user_id, outage, monkeypatch):
    tried = []
    original = OutageChatModel._generate

    def record(self, *args, **kwargs):
        tried.append(self.model_name)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(OutageChatModel, "_generate", record)

    client.post("/assistant/messages", json={"user_id": user_id, "message": "Hi"})

    assert tried == [settings.agent_model, *settings.agent_fallback_models]


def test_natural_language_booking_is_unavailable(client, db, user_id, outage):
    response = client.post(
        "/bookings", json={"user_id": user_id, "message": "Book my usual shuttle for tomorrow."}
    )

    assert response.status_code == 503
    assert "Book my usual shuttle" in response.json()["detail"]
    assert bookings(db, user_id) == []


def test_assistant_recovers_when_outage_ends(outage):
    outage.set_llm_outage(False)

    assert not isinstance(create_chat_model(), OutageChatModel)


def test_failed_turn_is_an_error_trace(monkeypatch):
    """The Langfuse span of a failed turn is marked ERROR with the reason."""

    import langfuse
    import langfuse.langchain

    from app.observability import tracing

    class FakeSpan:
        updates = []

        def update(self, **kwargs):
            self.updates.append(kwargs)

    span = FakeSpan()

    class FakeLangfuse:
        @contextmanager
        def start_as_current_observation(self, **kwargs):
            yield span

        def get_current_trace_id(self):
            return "trace-1"

    monkeypatch.setattr(tracing, "get_langfuse", FakeLangfuse)
    monkeypatch.setattr(langfuse, "propagate_attributes", lambda **kwargs: nullcontext())
    monkeypatch.setattr(langfuse.langchain, "CallbackHandler", lambda: None)

    with pytest.raises(LLMOutageError):
        with tracing.traced("assistant-turn", user_id=1, session_id="s", input="hi"):
            raise LLMOutageError("Simulated LLM outage")

    assert span.updates == [
        {"level": "ERROR", "status_message": "LLMOutageError: Simulated LLM outage"}
    ]
