from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.agent.fake_llm import FakeLLM
from app.api.bookings import get_llm
from app.db.database import get_db
from app.main import app
from tests.conftest import TODAY, TOMORROW




class FailingLLM:
    def invoke(self, user_input: str):
        raise TimeoutError("model timed out")


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_llm] = lambda: FakeLLM(
        reference_date=TODAY
    )

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def book(client, user_id, **body):
    return client.post("/bookings", json={"user_id": user_id, **body})


def test_create_booking_from_message(client, user_id):
    response = book(
        client, user_id, message="Book my usual shuttle for tomorrow."
    )

    assert response.status_code == 200
    data = response.json()
    assert data["already_booked"] is False
    assert data["message"].startswith("Done. You're booked on the 7:30 AM")
    assert data["booking"]["booking_date"] == TOMORROW.isoformat()


def test_create_booking_from_structured_date(client, user_id):
    app.dependency_overrides[get_llm] = lambda: FailingLLM()

    response = book(client, user_id, booking_date=TOMORROW.isoformat())

    assert response.status_code == 200
    booking = response.json()["booking"]
    assert booking["pickup_time"] == "07:30:00"
    assert booking["arrival_time"] == "08:15:00"
    assert booking["shuttle_name"] == "Morning Shuttle C"
    assert booking["pickup_location"] == "Home"
    assert booking["destination"] == "Office"
    assert booking["earlier_available"] is True
    assert booking["later_available"] is True


def test_duplicate_booking_returns_existing(client, user_id):
    first = book(client, user_id, booking_date=TOMORROW.isoformat()).json()
    second = book(client, user_id, booking_date=TOMORROW.isoformat()).json()

    assert second["booking_id"] == first["booking_id"]
    assert second["already_booked"] is True
    assert second["message"].startswith("You're already booked")


def test_request_needs_message_or_date(client, user_id):
    assert book(client, user_id).status_code == 422


def test_past_date_returns_readable_conflict(client, user_id):
    yesterday = TODAY - timedelta(days=1)

    response = book(client, user_id, booking_date=yesterday.isoformat())

    assert response.status_code == 409
    assert response.json()["detail"] == "That date has already passed."


def test_llm_failure_returns_service_unavailable(client, user_id):
    app.dependency_overrides[get_llm] = lambda: FailingLLM()

    response = book(
        client, user_id, message="Book my usual shuttle for tomorrow."
    )

    assert response.status_code == 503


def test_reschedule_earlier_then_get(client, user_id):
    booking_id = book(
        client, user_id, booking_date=TOMORROW.isoformat()
    ).json()["booking_id"]

    response = client.post(
        f"/bookings/{booking_id}/reschedule",
        json={"user_id": user_id, "direction": "earlier"},
    )

    assert response.status_code == 200
    assert response.json()["message"].startswith(
        "Done. You're now on the 7:15 AM shuttle"
    )

    fetched = client.get(f"/bookings/{booking_id}?user_id={user_id}")
    assert fetched.status_code == 200
    assert fetched.json()["pickup_time"] == "07:15:00"


def test_get_unknown_booking_is_not_found(client, user_id):
    response = client.get(f"/bookings/999999?user_id={user_id}")

    assert response.status_code == 404


def test_get_upcoming_bookings(client, user_id):
    assert client.get(f"/bookings?user_id={user_id}").json() == []

    book(client, user_id, booking_date=TOMORROW.isoformat())

    data = client.get(f"/bookings?user_id={user_id}").json()
    assert len(data) == 1
    assert data[0]["route_name"] == "Home → Office Morning Route"
