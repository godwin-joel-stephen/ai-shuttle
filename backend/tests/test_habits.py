"""Learned commute habits (F10): ride history in, expected usual out.

Clock: Monday 2026-11-02 06:00. Morning shuttles depart 7:00, 7:15, 7:30
(the seeded usual), 7:45 and 8:00 and take 45 minutes."""

from datetime import date, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.agent.fake_llm import FakeLLM
from app.api.bookings import _create_service, get_llm
from app.db.database import get_db
from app.db.ride_history import add_past_rides, demo_rides
from app.main import app
from app.models.booking import Booking
from app.models.user import User
from app.services.habit_service import HabitSource
from app.services.tracking_service import TrackingService
from app.services.trip_planner import TripGoal, TripPlanner
from app.tools.assistant_tools import create_assistant_tools
from tests.conftest import TODAY
from tests.fake_embedder import FakeEmbedder

NEXT_MONDAY = TODAY + timedelta(weeks=1)
WEDNESDAY = TODAY + timedelta(days=2)
THURSDAY = TODAY + timedelta(days=3)


def ago(weeks: int, weekday: int) -> date:
    """`weekday` (0 = Monday) of the week `weeks` before this one."""
    return TODAY - timedelta(weeks=weeks) + timedelta(days=weekday)


def t(text: str) -> time:
    hour, minute = text.split(":")
    return time(int(hour), int(minute))


def rides(*specs: tuple[int, int, str]) -> list[tuple[date, time]]:
    return [(ago(weeks, weekday), t(departure)) for weeks, weekday, departure in specs]


def mondays(*departures: str) -> list[tuple[date, time]]:
    """Departures on the Mondays before this one, most recent first."""
    return rides(*((i + 1, 0, d) for i, d in enumerate(departures)))


@pytest.fixture
def service(db):
    return _create_service(db)


@pytest.fixture
def history(db, user_id):
    def add(ride_list):
        add_past_rides(db, user_id, ride_list)
    return add


def departure(habit) -> str:
    return f"{habit.shuttle.departure_time:%H:%M}"


# --- learning ---------------------------------------------------------------

def test_no_history_uses_the_saved_usual(service, user_id):
    habit = service.habits.usual_for(user_id, NEXT_MONDAY)

    assert departure(habit) == "07:30"
    assert habit.source == HabitSource.DEFAULT
    assert habit.reason == "it's your saved usual shuttle"
    assert habit.regular is False


def test_demo_history_learns_each_weekday(service, history, user_id):
    history(demo_rides(TODAY))

    week = service.habits.week(user_id)

    assert [departure(h) for h in week] == ["07:15", "07:30", "07:30", "08:00", "07:30"]
    monday, tuesday, wednesday, thursday, friday = week
    assert monday.source == HabitSource.WEEKDAY
    assert monday.reason == "you took it on 4 of your last 5 Mondays"
    assert tuesday.reason == "you took it on each of your last 5 Tuesdays"
    assert thursday.reason == "you took it on 4 of your last 5 Thursdays"
    assert friday.source == HabitSource.WEEKDAY
    # One Wednesday ride isn't a habit of its own.
    assert wednesday.source != HabitSource.WEEKDAY
    assert [h.regular for h in week] == [True, True, False, True, True]


def test_too_few_rides_are_not_a_habit(service, history, user_id):
    history(mondays("07:15", "07:15"))

    assert service.habits.usual_for(user_id, NEXT_MONDAY).source == HabitSource.DEFAULT


def test_no_majority_is_not_a_habit(service, history, user_id):
    history(mondays("07:15", "07:45", "07:15", "07:45", "08:00"))

    habit = service.habits.usual_for(user_id, NEXT_MONDAY)

    assert departure(habit) == "07:30"
    assert habit.source == HabitSource.DEFAULT


def test_recent_rides_outweigh_older_ones(service, history, user_id):
    # Switched to the 8:00 three weeks ago; only the last five count.
    history(mondays("08:00", "08:00", "08:00", "07:15", "07:15", "07:15", "07:15"))

    habit = service.habits.usual_for(user_id, NEXT_MONDAY)

    assert departure(habit) == "08:00"
    assert habit.reason == "you took it on 3 of your last 5 Mondays"


def test_rides_older_than_the_lookback_are_ignored(service, history, user_id):
    history(rides(*((weeks, 0, "07:15") for weeks in range(9, 13))))

    assert service.habits.usual_for(user_id, NEXT_MONDAY).source == HabitSource.DEFAULT


def test_cancelled_rides_are_ignored(db, service, history, user_id):
    history(mondays("07:15", "07:15", "07:15"))
    db.query(Booking).update({Booking.status: "cancelled"})
    db.commit()

    assert service.habits.usual_for(user_id, NEXT_MONDAY).source == HabitSource.DEFAULT


def test_overall_habit_covers_days_without_their_own(service, history, user_id):
    # Rides the 7:45 on Tuesdays and Thursdays; never on Wednesdays.
    history(rides(*((w, d, "07:45") for w in (1, 2) for d in (1, 3))))

    habit = service.habits.usual_for(user_id, WEDNESDAY)

    assert departure(habit) == "07:45"
    assert habit.source == HabitSource.OVERALL
    assert habit.reason == "you took it on each of your last 4 rides"
    assert habit.regular is False


def test_upcoming_bookings_are_not_history(service, history, user_id):
    service.book_shuttle(user_id, TODAY + timedelta(days=1), service.get_usual_shuttle(user_id))
    history(mondays("07:15", "07:15"))

    assert service.habits.usual_for(user_id, NEXT_MONDAY).source == HabitSource.DEFAULT


# --- pinning ----------------------------------------------------------------

def test_pinned_shuttle_beats_the_learned_habit(service, history, user_id, shuttles):
    history(demo_rides(TODAY))
    service.habits.pin(user_id, shuttles["Morning Shuttle D"].id)

    habit = service.habits.usual_for(user_id, NEXT_MONDAY)
    assert departure(habit) == "07:45"
    assert habit.source == HabitSource.PINNED
    assert habit.regular is True  # still rides Mondays

    service.habits.pin(user_id, None)
    assert departure(service.habits.usual_for(user_id, NEXT_MONDAY)) == "07:15"


def test_pinning_an_evening_shuttle_is_refused(service, user_id, shuttles):
    with pytest.raises(Exception, match="different route"):
        service.habits.pin(user_id, shuttles["Evening Shuttle A"].id)


# --- what follows the habit ------------------------------------------------

def test_book_my_usual_follows_the_weekday_habit(service, history, user_id):
    history(demo_rides(TODAY))

    monday = service.book_usual_shuttle(user_id, NEXT_MONDAY)
    thursday = service.book_usual_shuttle(user_id, THURSDAY)

    assert f"{monday.booking.pickup_time:%H:%M}" == "07:15"
    assert monday.habit.reason == "you took it on 4 of your last 5 Mondays"
    assert f"{thursday.booking.pickup_time:%H:%M}" == "08:00"


def test_eligibility_checks_the_weekday_habit(service, history, db, user_id, shuttles):
    history(demo_rides(TODAY))
    # Fill the 7:15 next Monday; the 7:30 still has seats.
    shuttle = shuttles["Morning Shuttle B"]
    others = User(name="Other riders", email="habit-others@example.com")
    db.add(others)
    db.flush()
    db.add_all(
        Booking(user_id=others.id, shuttle_id=shuttle.id, booking_date=NEXT_MONDAY,
                pickup_time=shuttle.departure_time, status="confirmed")
        for _ in range(shuttle.capacity)
    )
    db.commit()

    result = service.check_eligibility(user_id, NEXT_MONDAY)

    assert result.eligible is False
    assert result.error.code == "shuttle_unavailable"


def test_trip_planner_prefers_the_learned_usual(service, history, db, user_id):
    history(demo_rides(TODAY))
    planner = TripPlanner(service, TrackingService(db, service))

    [day] = planner.plan(user_id, [NEXT_MONDAY], TripGoal(arrive_by=time(8, 30)))

    # Without the habit it would pick the latest on-time shuttle, the 7:45.
    assert f"{day.chosen.shuttle.departure_time:%H:%M}" == "07:15"


# --- API ---------------------------------------------------------------------

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_llm] = lambda: FakeLLM(reference_date=TODAY)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_structured_booking_says_why(client, history, user_id):
    history(demo_rides(TODAY))

    body = client.post(
        "/bookings", json={"user_id": user_id, "booking_date": NEXT_MONDAY.isoformat()}
    ).json()

    assert body["booking"]["pickup_time"] == "07:15:00"
    assert body["usual_reason"] == "you took it on 4 of your last 5 Mondays"
    assert body["message"].endswith("That's your usual: you took it on 4 of your last 5 Mondays.")

    again = client.post(
        "/bookings", json={"user_id": user_id, "booking_date": NEXT_MONDAY.isoformat()}
    ).json()
    assert again["already_booked"] is True
    assert again["usual_reason"] is None


def test_saved_usual_booking_has_no_reason(client, user_id):
    body = client.post(
        "/bookings", json={"user_id": user_id, "booking_date": NEXT_MONDAY.isoformat()}
    ).json()

    assert body["usual_reason"] is None
    assert "usual" not in body["message"]


def test_habits_endpoint_lists_week_and_unbooked_days(client, service, history, user_id):
    history(demo_rides(TODAY))
    service.book_usual_shuttle(user_id, TODAY + timedelta(days=1))

    body = client.get("/habits", params={"user_id": user_id}).json()

    assert [d["departure"] for d in body["days"]] == [
        "07:15:00", "07:30:00", "07:30:00", "08:00:00", "07:30:00",
    ]
    assert body["pinned_shuttle_id"] is None
    # Tomorrow (Tuesday) to next Monday; the weekend is skipped.
    upcoming = body["upcoming"]
    assert [d["weekday"] for d in upcoming] == [
        "Tuesday", "Wednesday", "Thursday", "Friday", "Monday",
    ]
    assert [d["booked"] for d in upcoming] == [True, False, False, False, False]
    assert upcoming[0]["booked_departure"] == "07:30:00"
    assert upcoming[-1]["habit"]["reason"] == "you took it on 4 of your last 5 Mondays"
    assert upcoming[1]["habit"]["regular"] is False


def test_pin_and_unpin_endpoint(client, history, user_id, shuttles):
    history(demo_rides(TODAY))
    shuttle_id = shuttles["Morning Shuttle D"].id

    pinned = client.post("/habits/pin", json={"user_id": user_id, "shuttle_id": shuttle_id}).json()
    assert pinned["pinned_shuttle_id"] == shuttle_id
    assert {d["source"] for d in pinned["days"]} == {"pinned"}

    unpinned = client.post("/habits/pin", json={"user_id": user_id, "shuttle_id": None}).json()
    assert unpinned["pinned_shuttle_id"] is None
    assert unpinned["days"][0]["departure"] == "07:15:00"

    refused = client.post(
        "/habits/pin", json={"user_id": user_id, "shuttle_id": shuttles["Evening Shuttle A"].id}
    )
    assert refused.status_code == 409


# --- agent tools ---------------------------------------------------------------

def test_habit_tools(db, history, user_id, shuttles):
    history(demo_rides(TODAY))
    tools = {t.name: t for t in create_assistant_tools(db, user_id, FakeEmbedder())}

    habits = tools["get_commute_habits"].invoke({})
    assert habits["days"][0]["departure"] == "7:15 AM"
    assert habits["days"][0]["reason"] == "you took it on 4 of your last 5 Mondays"

    booked = tools["book_usual_shuttle"].invoke({"booking_date": THURSDAY.isoformat()})
    assert booked["booking"]["departure"] == "08:00"
    assert booked["usual_because"] == "you took it on 4 of your last 5 Thursdays"

    pinned = tools["set_usual_shuttle"].invoke({"shuttle_id": shuttles["Morning Shuttle A"].id})
    assert {d["departure"] for d in pinned["days"]} == {"7:00 AM"}
    assert pinned["days"][0]["reason"] == "you pinned it as your usual"
