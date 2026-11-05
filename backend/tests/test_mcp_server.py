import asyncio
import json
from datetime import timedelta

import pytest

from app.db.database import SessionLocal
from app.mcp_server import create_mcp_server
from app.models.booking import Booking
from tests.conftest import TODAY, TOMORROW
from tests.fake_embedder import FakeEmbedder


@pytest.fixture
def server(db, user_id):
    return create_mcp_server(SessionLocal, FakeEmbedder, user_id)


def call(server, name, **arguments) -> dict:
    result = asyncio.run(server.call_tool(name, arguments))
    assert not result.is_error, result.content
    return json.loads(result.content[0].text)


def test_lists_the_agents_tools_with_safety_hints(server):
    tools = {t.name: t for t in asyncio.run(server.list_tools())}

    assert set(tools) == {
        "get_today",
        "get_my_bookings",
        "list_shuttle_options",
        "book_usual_shuttle",
        "change_booking_shuttle",
        "cancel_booking",
        "get_shuttle_status",
        "check_booking_eligibility",
        "plan_trip",
        "book_trip_plan",
        "search_policies",
    }
    assert tools["plan_trip"].annotations.read_only_hint is True
    assert tools["book_trip_plan"].annotations.read_only_hint is False
    assert tools["get_my_bookings"].annotations.read_only_hint is True
    assert tools["book_usual_shuttle"].annotations.read_only_hint is False
    assert tools["cancel_booking"].annotations.destructive_hint is True
    assert tools["book_usual_shuttle"].input_schema["required"] == ["booking_date"]


def test_get_today(server):
    assert call(server, "get_today") == {
        "date": TODAY.isoformat(),
        "weekday": f"{TODAY:%A}",
    }


def test_booking_through_mcp_uses_the_real_service(server, db):
    result = call(server, "book_usual_shuttle", booking_date=TOMORROW.isoformat())

    assert result["already_booked"] is False
    assert result["booking"]["departure"] == "07:30"
    assert db.query(Booking).filter_by(booking_date=TOMORROW).count() == 1

    bookings = call(server, "get_my_bookings")["bookings"]
    assert [b["date"] for b in bookings] == [TOMORROW.isoformat()]


def test_booking_rules_still_apply(server):
    saturday = TODAY + timedelta(days=5)  # TODAY is a Monday

    result = call(server, "book_usual_shuttle", booking_date=saturday.isoformat())

    assert result == {"error": "Shuttles don't run on Saturdays."}


def test_policy_search_through_mcp(server):
    passages = call(server, "search_policies", query="how long will the driver wait at the stop")["passages"]

    assert passages[0]["source"] == "Pickup Rules › Arriving at the stop"
