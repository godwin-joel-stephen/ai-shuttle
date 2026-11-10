import json
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver

from app.api.assistant import (
    get_chat_model,
    get_conversation_memory,
    get_external_tools,
    get_fallback_chat_models,
    get_policy_embedder,
)
from app.db.database import get_db
from app.graph.assistant_graph import is_unusable_reply
from app.main import app
from app.models.booking import Booking
from tests.fake_embedder import FakeEmbedder
from tests.scripted_chat_model import ScriptedChatModel, call
from tests.conftest import TODAY, TOMORROW


TOMORROW = TODAY + timedelta(days=1)


def last_tool_result(messages) -> dict:
    tool_message = next(m for m in reversed(messages) if isinstance(m, ToolMessage))
    return json.loads(tool_message.text)


@pytest.fixture
def memory():
    return InMemorySaver()


@pytest.fixture
def client(db, memory):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_conversation_memory] = lambda: memory
    app.dependency_overrides[get_policy_embedder] = FakeEmbedder
    app.dependency_overrides[get_fallback_chat_models] = lambda: []

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def use_model(model: ScriptedChatModel):
    app.dependency_overrides[get_chat_model] = lambda: model


def send(client, user_id, message, conversation_id=None):
    return client.post(
        "/assistant/messages",
        json={
            "user_id": user_id,
            "message": message,
            "conversation_id": conversation_id,
        },
    )


def test_agent_books_through_tool(client, db, user_id):
    use_model(ScriptedChatModel(script=[
        call("book_usual_shuttle", booking_date=TOMORROW.isoformat()),
        AIMessage("Done. You're on the 7:30 AM shuttle tomorrow."),
    ]))

    response = send(client, user_id, "Book my usual shuttle for tomorrow")

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Done. You're on the 7:30 AM shuttle tomorrow."
    assert data["bookings_changed"] is True
    assert data["actions"] == [{
        "tool": "book_usual_shuttle",
        "arguments": {"booking_date": TOMORROW.isoformat()},
        "succeeded": True,
        "error": None,
        "server": None,
    }]
    assert db.query(Booking).filter_by(booking_date=TOMORROW).count() == 1


def test_follow_up_uses_conversation_memory(client, db, user_id, shuttles):
    def earlier_from_options(messages):
        # The second turn must still see the first turn's booking.
        booking_result = next(
            json.loads(m.text) for m in messages
            if isinstance(m, ToolMessage) and "booking" in json.loads(m.text)
        )
        options = last_tool_result(messages)["shuttles"]
        target = next(s for s in options if s["departure"] == "07:00")
        return call(
            "change_booking_shuttle",
            call_id="call-3",
            booking_id=booking_result["booking"]["booking_id"],
            shuttle_id=target["shuttle_id"],
        )

    model = ScriptedChatModel(script=[
        call("book_usual_shuttle", booking_date=TOMORROW.isoformat()),
        AIMessage("Booked the 7:30 AM shuttle."),
        call("list_shuttle_options", call_id="call-2", booking_date=TOMORROW.isoformat()),
        earlier_from_options,
        AIMessage("Moved you to the 7:00 AM shuttle."),
    ])
    use_model(model)

    first = send(client, user_id, "Book my usual shuttle for tomorrow").json()
    second = send(
        client, user_id, "Make it 30 minutes earlier", first["conversation_id"]
    ).json()

    assert second["conversation_id"] == first["conversation_id"]
    assert [a["tool"] for a in second["actions"]] == [
        "list_shuttle_options",
        "change_booking_shuttle",
    ]
    assert second["bookings_changed"] is True

    booking = db.query(Booking).filter_by(booking_date=TOMORROW).one()
    assert booking.shuttle_id == shuttles["Morning Shuttle A"].id
    assert booking.pickup_time.isoformat() == "07:00:00"


def test_tool_error_is_reported_not_raised(client, user_id):
    yesterday = (TODAY - timedelta(days=1)).isoformat()
    use_model(ScriptedChatModel(script=[
        call("book_usual_shuttle", booking_date=yesterday),
        lambda messages: AIMessage(
            f"Sorry: {last_tool_result(messages)['error']}"
        ),
    ]))

    data = send(client, user_id, "Book my shuttle for yesterday").json()

    assert data["reply"] == "Sorry: That date has already passed."
    assert data["bookings_changed"] is False
    assert data["actions"][0]["succeeded"] is False
    assert data["actions"][0]["error"] == "That date has already passed."


def test_new_conversation_starts_without_history(client, user_id):
    model = ScriptedChatModel(script=[AIMessage("Hi"), AIMessage("Hello again")])
    use_model(model)

    send(client, user_id, "Hi")
    send(client, user_id, "Hi")

    # System prompt + the single new user message, nothing carried over.
    assert len(model.received[1]) == 2


def test_model_failure_returns_service_unavailable(client, user_id):
    def fail(messages):
        raise TimeoutError("model timed out")

    use_model(ScriptedChatModel(script=[fail]))

    response = send(client, user_id, "Book my shuttle")

    assert response.status_code == 503


def test_fallback_model_takes_over_when_primary_fails(client, user_id):
    def overloaded(messages):
        raise RuntimeError("503 UNAVAILABLE: high demand")

    use_model(ScriptedChatModel(script=[overloaded]))
    app.dependency_overrides[get_fallback_chat_models] = lambda: [ScriptedChatModel(
        script=[AIMessage("Answered by the fallback model.")]
    )]

    data = send(client, user_id, "Hi").json()

    assert data["reply"] == "Answered by the fallback model."


def test_slow_primary_model_hands_over_to_fallback(client, user_id, monkeypatch):
    import time

    import app.graph.assistant_graph as assistant_graph

    monkeypatch.setattr(assistant_graph, "MODEL_DEADLINE_SECONDS", 0.2)

    def overloaded(messages):
        time.sleep(1)
        return AIMessage("Too late.")

    use_model(ScriptedChatModel(script=[overloaded]))
    app.dependency_overrides[get_fallback_chat_models] = lambda: [ScriptedChatModel(
        script=[AIMessage("Answered by the fallback model.")]
    )]

    started = time.monotonic()
    data = send(client, user_id, "Hi").json()

    assert data["reply"] == "Answered by the fallback model."
    assert time.monotonic() - started < 1


def test_failure_after_booking_still_reports_the_booking(client, db, user_id):
    def overloaded(messages):
        raise RuntimeError("503 UNAVAILABLE: high demand")

    use_model(ScriptedChatModel(script=[
        call("book_usual_shuttle", booking_date=TOMORROW.isoformat()),
        overloaded,
    ]))

    response = send(client, user_id, "Book my usual shuttle for tomorrow")

    assert response.status_code == 200
    data = response.json()
    assert data["bookings_changed"] is True
    assert data["actions"][0]["tool"] == "book_usual_shuttle"
    assert data["reply"].startswith("I made changes to your bookings")
    assert db.query(Booking).filter_by(booking_date=TOMORROW).count() == 1


def test_unknown_user_is_not_found(client):
    use_model(ScriptedChatModel(script=[]))

    assert send(client, 999_999, "Hi").status_code == 404


def test_conversation_history_replays_turns(client, user_id):
    use_model(ScriptedChatModel(script=[
        call("book_usual_shuttle", booking_date=TOMORROW.isoformat()),
        AIMessage("Booked the 7:30 AM shuttle."),
        AIMessage("Anything else?"),
    ]))
    conversation_id = send(client, user_id, "Book tomorrow").json()["conversation_id"]
    send(client, user_id, "Thanks", conversation_id)

    response = client.get(
        f"/assistant/conversations/{conversation_id}?user_id={user_id}"
    )

    assert response.status_code == 200
    messages = response.json()["messages"]
    assert [(m["role"], m["text"]) for m in messages] == [
        ("user", "Book tomorrow"),
        ("assistant", "Booked the 7:30 AM shuttle."),
        ("user", "Thanks"),
        ("assistant", "Anything else?"),
    ]
    assert messages[1]["actions"][0]["tool"] == "book_usual_shuttle"
    assert messages[3]["actions"] == []


def test_other_users_cannot_read_a_conversation(client, user_id):
    use_model(ScriptedChatModel(script=[AIMessage("Hi")]))
    conversation_id = send(client, user_id, "Hi").json()["conversation_id"]

    response = client.get(
        f"/assistant/conversations/{conversation_id}?user_id={user_id + 1}"
    )

    assert response.status_code == 404


def test_why_cant_i_book_combines_rule_and_policy(client, user_id):
    saturday = (TODAY + timedelta(days=5)).isoformat()

    def explain(messages):
        policy = last_tool_result(messages)["passages"][0]
        return AIMessage(f"Per the {policy['source']}: {policy['text'][:40]}")

    use_model(ScriptedChatModel(script=[
        call("check_booking_eligibility", booking_date=saturday),
        lambda messages: call(
            "search_policies",
            call_id="call-2",
            query=last_tool_result(messages)["message"] + " weekend service days",
        ),
        explain,
    ]))

    data = send(client, user_id, "Why can't I book Saturday?").json()

    assert [a["tool"] for a in data["actions"]] == [
        "check_booking_eligibility",
        "search_policies",
    ]
    assert data["sources"] == ["Booking Policy › Service days"]
    assert data["reply"].startswith("Per the Booking Policy › Service days")
    assert data["bookings_changed"] is False


def test_agent_can_call_tools_from_external_mcp_servers(client, user_id):
    def get_current_weather(latitude: float, longitude: float) -> dict:
        """Current weather at a location."""
        return {"conditions": "rain", "rain_chance_next_2h_percent": 80}

    weather = StructuredTool.from_function(get_current_weather, metadata={"mcp_server": "weather"})
    app.dependency_overrides[get_external_tools] = lambda: [weather]
    use_model(ScriptedChatModel(script=[
        call("get_current_weather", latitude=12.97, longitude=77.64),
        lambda messages: AIMessage(f"It's {last_tool_result(messages)['conditions']}; take an umbrella."),
    ]))

    data = send(client, user_id, "Should I leave now?").json()

    assert data["actions"][0]["tool"] == "get_current_weather"
    assert data["actions"][0]["server"] == "weather"
    assert data["reply"] == "It's rain; take an umbrella."


def test_parallel_tool_calls_share_the_session_safely(client, db, user_id):
    # LangGraph runs tool calls from one model turn in parallel threads;
    # they share one database session ("prepared state" crash in evals).
    use_model(ScriptedChatModel(script=[
        AIMessage(content="", tool_calls=[
            {"name": "book_usual_shuttle", "args": {"booking_date": TOMORROW.isoformat()}, "id": "a"},
            {"name": "list_shuttle_options", "args": {"booking_date": TOMORROW.isoformat()}, "id": "b"},
            {"name": "get_my_bookings", "args": {}, "id": "c"},
        ]),
        AIMessage("Done."),
    ]))

    data = send(client, user_id, "Book the 8 o'clock shuttle tomorrow").json()

    assert [a["succeeded"] for a in data["actions"]] == [True, True, True]
    assert db.query(Booking).filter_by(booking_date=TOMORROW).count() == 1


def test_garbled_reply_falls_back_instead_of_reaching_the_rider(client, user_id):
    # Flash-Lite once answered a habits question with this bare text.
    use_model(ScriptedChatModel(script=[call("get_commute_habits"), AIMessage("ValueOfget_commute_habits")]))
    app.dependency_overrides[get_fallback_chat_models] = lambda: [ScriptedChatModel(
        script=[AIMessage("Your usual on Thursdays is the 7:30 AM shuttle.")]
    )]

    data = send(client, user_id, "What's my usual on Thursday?").json()

    assert data["reply"] == "Your usual on Thursdays is the 7:30 AM shuttle."


def test_garbled_reply_without_fallback_is_unavailable_not_shown(client, user_id):
    use_model(ScriptedChatModel(script=[AIMessage("ValueOfget_commute_habits")]))

    response = send(client, user_id, "What's my usual?")

    assert response.status_code == 503
    assert "get_commute_habits" not in response.text


@pytest.mark.parametrize("text, unusable", [
    ("ValueOfget_commute_habits", True),
    ("get_commute_habits", True),
    ("I called get_my_bookings for you.", True),
    ("getCommuteHabits", True),
    ("", True),
    ("Done.", False),
    ("Yes.", False),
    ("Your usual on Thursdays is the 8:00 AM shuttle.", False),
])
def test_unusable_reply_detection(text, unusable):
    names = frozenset({"get_commute_habits", "get_my_bookings"})
    assert is_unusable_reply(AIMessage(text), names) is unusable


def test_dry_weather_is_added_when_the_model_leaves_it_out(client, user_id):
    def get_current_weather(latitude: float, longitude: float) -> dict:
        """Current weather at a location."""
        return {"conditions": "clear", "precipitation_mm": 0, "rain_chance_next_2h_percent": 10}

    weather = StructuredTool.from_function(get_current_weather, metadata={"mcp_server": "weather"})
    app.dependency_overrides[get_external_tools] = lambda: [weather]
    use_model(ScriptedChatModel(script=[
        call("get_current_weather", latitude=12.97, longitude=77.64),
        AIMessage("Yes. Head out now for the 4-minute walk."),
    ]))

    data = send(client, user_id, "Should I leave now?").json()

    assert data["reply"] == (
        "Yes. Head out now for the 4-minute walk. It's clear, so you won't need an umbrella."
    )


def test_likely_rain_adds_an_umbrella_tip(client, user_id):
    def get_current_weather(latitude: float, longitude: float) -> dict:
        """Current weather at a location."""
        return {"conditions": "overcast", "precipitation_mm": 0, "rain_chance_next_2h_percent": 70}

    weather = StructuredTool.from_function(get_current_weather, metadata={"mcp_server": "weather"})
    app.dependency_overrides[get_external_tools] = lambda: [weather]
    use_model(ScriptedChatModel(script=[
        call("get_current_weather", latitude=12.97, longitude=77.64),
        AIMessage("No, leave in 3 minutes."),
    ]))

    data = send(client, user_id, "Should I leave now?").json()

    assert data["reply"] == (
        "No, leave in 3 minutes. Rain is likely (70% in the next two hours), so take an umbrella."
    )
