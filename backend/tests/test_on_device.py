"""F14: the app answers simple requests with Apple's on-device model, then
uses the structured cancel endpoint and records the turn in the shared
conversation, so the chat history and the cloud agent both see it."""

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.api.assistant import (
    get_chat_model,
    get_conversation_memory,
    get_fallback_chat_models,
    get_policy_embedder,
)
from app.db.database import get_db
from app.main import app
from tests.conftest import TOMORROW
from tests.fake_embedder import FakeEmbedder
from tests.scripted_chat_model import ScriptedChatModel


@pytest.fixture
def client(db):
    memory = InMemorySaver()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_conversation_memory] = lambda: memory
    app.dependency_overrides[get_policy_embedder] = FakeEmbedder
    app.dependency_overrides[get_fallback_chat_models] = lambda: []

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def book_tomorrow(client, user_id) -> int:
    return client.post(
        "/bookings", json={"user_id": user_id, "booking_date": TOMORROW.isoformat()}
    ).json()["booking_id"]


def record(client, user_id, **body):
    return client.post(
        "/assistant/on-device-turns",
        json={
            "user_id": user_id,
            "message": "Book my usual shuttle for tomorrow",
            "reply": "Done. You're booked on the 7:30 AM shuttle tomorrow.",
            "actions": [{
                "tool": "book_usual_shuttle",
                "arguments": {"booking_date": TOMORROW.isoformat()},
                "succeeded": True,
            }],
            **body,
        },
    )


def test_cancel_endpoint_cancels(client, user_id):
    booking_id = book_tomorrow(client, user_id)

    response = client.post(f"/bookings/{booking_id}/cancel", json={"user_id": user_id})

    assert response.status_code == 200
    assert response.json()["message"].startswith("Done. I cancelled the 7:30 AM shuttle")
    assert response.json()["booking"]["status"] == "cancelled"
    upcoming = client.get("/bookings", params={"user_id": user_id}).json()
    assert booking_id not in [b["id"] for b in upcoming]


def test_cancel_unknown_booking_is_404(client, user_id):
    response = client.post("/bookings/999999/cancel", json={"user_id": user_id})

    assert response.status_code == 404


def test_on_device_turn_appears_in_the_conversation(client, user_id):
    conversation_id = record(client, user_id).json()["conversation_id"]

    data = client.get(
        f"/assistant/conversations/{conversation_id}", params={"user_id": user_id}
    ).json()

    assert [m["role"] for m in data["messages"]] == ["user", "assistant"]
    reply = data["messages"][1]
    assert reply["on_device"] is True
    assert reply["text"] == "Done. You're booked on the 7:30 AM shuttle tomorrow."
    assert reply["actions"][0]["tool"] == "book_usual_shuttle"
    assert reply["actions"][0]["succeeded"] is True


def test_cloud_agent_sees_the_on_device_turn(client, user_id):
    conversation_id = record(client, user_id).json()["conversation_id"]
    model = ScriptedChatModel(script=[AIMessage("Moved it to the 7:15.")])
    app.dependency_overrides[get_chat_model] = lambda: model

    response = client.post("/assistant/messages", json={
        "user_id": user_id,
        "message": "Make it earlier",
        "conversation_id": conversation_id,
    })

    assert response.status_code == 200
    history = model.received[0]
    assert [type(m) for m in history[1:]] == [HumanMessage, AIMessage, HumanMessage]
    assert history[2].text == "Done. You're booked on the 7:30 AM shuttle tomorrow."
    assert not history[2].tool_calls

    data = client.get(
        f"/assistant/conversations/{conversation_id}", params={"user_id": user_id}
    ).json()
    assert [m.get("on_device") for m in data["messages"] if m["role"] == "assistant"] == [True, False]


def test_continues_an_existing_conversation(client, user_id):
    conversation_id = record(client, user_id).json()["conversation_id"]

    again = record(client, user_id, conversation_id=conversation_id, message="What do I have booked?")

    assert again.json()["conversation_id"] == conversation_id
    data = client.get(
        f"/assistant/conversations/{conversation_id}", params={"user_id": user_id}
    ).json()
    assert len(data["messages"]) == 4


def test_recording_works_during_llm_outage(client, user_id, outage_flag):
    outage_flag.set_llm_outage(True)

    assert record(client, user_id).status_code == 200


def test_unknown_user_is_404(client):
    assert record(client, 999999).status_code == 404
