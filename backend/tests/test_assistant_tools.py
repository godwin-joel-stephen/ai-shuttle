from datetime import date, timedelta

from app.tools.assistant_tools import create_assistant_tools
from tests.fake_embedder import FakeEmbedder
from tests.conftest import TODAY, TOMORROW


TOMORROW = TODAY + timedelta(days=1)


def tools_by_name(db, user_id):
    return {t.name: t for t in create_assistant_tools(db, user_id, FakeEmbedder())}


def test_list_shuttle_options_marks_full_shuttles(db, user_id):
    tools = tools_by_name(db, user_id)

    result = tools["list_shuttle_options"].invoke(
        {"booking_date": TOMORROW.isoformat()}
    )

    assert [s["departure"] for s in result["shuttles"]] == [
        "07:00", "07:15", "07:30", "07:45", "08:00",
    ]
    assert all(s["bookable"] for s in result["shuttles"])


def test_book_change_and_cancel(db, user_id, shuttles):
    tools = tools_by_name(db, user_id)

    booked = tools["book_usual_shuttle"].invoke(
        {"booking_date": TOMORROW.isoformat()}
    )
    booking_id = booked["booking"]["booking_id"]
    assert booked["booking"]["departure"] == "07:30"

    moved = tools["change_booking_shuttle"].invoke(
        {"booking_id": booking_id, "shuttle_id": shuttles["Morning Shuttle E"].id}
    )
    assert moved["booking"]["departure"] == "08:00"

    tools["cancel_booking"].invoke({"booking_id": booking_id})
    assert tools["get_my_bookings"].invoke({}) == {"bookings": []}


def test_cannot_move_to_another_route(db, user_id, shuttles):
    tools = tools_by_name(db, user_id)
    booking_id = tools["book_usual_shuttle"].invoke(
        {"booking_date": TOMORROW.isoformat()}
    )["booking"]["booking_id"]

    result = tools["change_booking_shuttle"].invoke(
        {"booking_id": booking_id, "shuttle_id": shuttles["Evening Shuttle A"].id}
    )

    assert result == {"error": "That shuttle runs on a different route."}


def test_tools_only_see_their_own_user(db, user_id):
    tools = tools_by_name(db, user_id)
    booking_id = tools["book_usual_shuttle"].invoke(
        {"booking_date": TOMORROW.isoformat()}
    )["booking"]["booking_id"]

    stranger = tools_by_name(db, 999_999)

    assert stranger["cancel_booking"].invoke({"booking_id": booking_id}) == {
        "error": f"Booking {booking_id} not found."
    }
