"""Goal-based trip planning (F7). Mirrors the `goal-*` eval cases without
a model. Clock: Monday 2026-11-02 06:00. Morning shuttles depart 7:00,
7:15, 7:30 (usual), 7:45, 8:00 and take 45 minutes."""

from datetime import time, timedelta

import pytest

from app.api.bookings import _create_service
from app.models.booking import Booking
from app.services.tracking_service import TrackingService
from app.services.trip_planner import GoalAction, TripGoal, TripPlanner
from app.tools.assistant_tools import create_assistant_tools
from tests.conftest import TODAY, TOMORROW
from tests.fake_embedder import FakeEmbedder

WEDNESDAY = TODAY + timedelta(days=2)
SATURDAY = TODAY + timedelta(days=5)


@pytest.fixture
def service(db):
    return _create_service(db)


@pytest.fixture
def tracking(db, service):
    return TrackingService(db, service)


@pytest.fixture
def planner(service, tracking):
    return TripPlanner(service, tracking)


def by(hour, minute=0):
    return TripGoal(arrive_by=time(hour, minute))


def book(service, user_id, day, shuttle):
    booking = service.book_usual_shuttle(user_id, day).booking
    if booking.shuttle_id != shuttle.id:
        service.move_booking(user_id, booking.id, shuttle.id)
    return booking


def departures(db, user_id):
    return sorted(
        (b.booking_date, f"{b.pickup_time:%H:%M}")
        for b in db.query(Booking).filter_by(user_id=user_id, status="confirmed")
    )


def fill(db, shuttle, day):
    from app.models.user import User

    other = db.query(User).filter_by(email="other@example.com").one_or_none()
    if other is None:
        other = User(name="Other", email="other@example.com")
        db.add(other)
        db.flush()
    db.add_all(
        Booking(user_id=other.id, shuttle_id=shuttle.id, booking_date=day,
                pickup_time=shuttle.departure_time, status="confirmed")
        for _ in range(shuttle.capacity)
    )
    db.commit()


def test_usual_shuttle_wins_when_it_meets_the_goal(planner, user_id):
    [day] = planner.plan(user_id, [TOMORROW], by(8, 30))

    assert day.action == GoalAction.BOOK
    assert f"{day.chosen.shuttle.departure_time:%H:%M}" == "07:30"
    assert day.message == "Book the 7:30 AM, arriving 8:15 AM."


def test_latest_shuttle_that_arrives_in_time(planner, user_id):
    [day] = planner.plan(user_id, [TOMORROW], by(8))

    assert f"{day.chosen.shuttle.departure_time:%H:%M}" == "07:15"
    assert day.chosen.arrival.time() == time(8, 0)  # arriving exactly on time counts


def test_impossible_goal_books_nothing_and_says_how_late(planner, db, user_id):
    [day] = planner.apply(user_id, [WEDNESDAY], by(7, 30))

    assert day.action == GoalAction.NOT_POSSIBLE
    assert day.late_by_minutes == 15
    assert day.message == (
        "No shuttle gets you there by 7:30 AM. "
        "The soonest is the 7:00 AM, arriving 7:45 AM (15 minutes late)."
    )
    assert departures(db, user_id) == []


def test_moves_an_existing_booking_instead_of_double_booking(planner, service, db, user_id, shuttles):
    book(service, user_id, TOMORROW, shuttles["Morning Shuttle C"])

    [day] = planner.apply(user_id, [TOMORROW], by(8))

    assert day.action == GoalAction.MOVE
    assert day.succeeded is True
    assert day.message == "Moved you from the 7:30 AM to the 7:15 AM, arriving 8:00 AM."
    assert departures(db, user_id) == [(TOMORROW, "07:15")]


def test_keeps_a_booking_that_already_meets_the_goal(planner, service, db, user_id, shuttles):
    book(service, user_id, TOMORROW, shuttles["Morning Shuttle C"])

    [day] = planner.apply(user_id, [TOMORROW], by(8, 30))

    assert day.action == GoalAction.KEEP
    assert day.message == (
        "You're already on the 7:30 AM, arriving 8:15 AM, which gets you there by 8:30 AM."
    )
    assert departures(db, user_id) == [(TOMORROW, "07:30")]


def test_full_shuttle_is_skipped_and_explained(planner, db, user_id, shuttles):
    fill(db, shuttles["Morning Shuttle B"], TOMORROW)

    [day] = planner.apply(user_id, [TOMORROW], by(8))

    assert f"{day.chosen.shuttle.departure_time:%H:%M}" == "07:00"
    assert "The 7:15 AM shuttle is full on Tuesday." in day.message
    assert departures(db, user_id) == [(TOMORROW, "07:00")]


def test_every_day_this_week_in_one_call(planner, db, user_id):
    week = [TODAY + timedelta(days=n) for n in range(5)]

    days = planner.apply(user_id, week, by(8))

    assert all(d.succeeded for d in days)
    assert departures(db, user_id) == [(d, "07:15") for d in week]


def test_delayed_trip_today_is_not_switched_unasked(planner, service, tracking, db, user_id, shuttles):
    booking = book(service, user_id, TODAY, shuttles["Morning Shuttle C"])
    tracking.start_simulation(user_id, booking.id, start_minutes=-10)
    tracking.set_delay(user_id, booking.id, 20)

    [day] = planner.apply(user_id, [TODAY], by(8, 20))

    assert day.action == GoalAction.NOT_POSSIBLE
    assert f"{day.best_effort.shuttle.departure_time:%H:%M}" == "07:45"
    assert day.message == (
        "No shuttle gets you there by 8:20 AM. Your 7:30 AM is running 20 minutes late and "
        "arrives 8:35 AM; the 7:45 AM arrives 8:30 AM (10 minutes late), 5 minutes sooner, "
        "if you want to switch."
    )
    assert departures(db, user_id) == [(TODAY, "07:30")]


def test_delayed_trip_kept_when_it_still_meets_the_goal(planner, service, tracking, user_id, shuttles):
    booking = book(service, user_id, TODAY, shuttles["Morning Shuttle C"])
    tracking.start_simulation(user_id, booking.id, start_minutes=-10)
    tracking.set_delay(user_id, booking.id, 10)

    [day] = planner.plan(user_id, [TODAY], by(8, 30))

    assert day.action == GoalAction.KEEP
    assert "running 10 minutes late, arriving 8:25 AM" in day.message


def test_departed_shuttles_are_not_options_on_the_trip_timeline(planner, service, tracking, user_id, shuttles):
    booking = book(service, user_id, TODAY, shuttles["Morning Shuttle C"])
    tracking.start_simulation(user_id, booking.id, start_minutes=-10)  # 7:20 on the trip's clock

    [day] = planner.plan(user_id, [TODAY], by(8))

    # The 7:00 and 7:15 would arrive by 8:00 but have left.
    assert day.action == GoalAction.NOT_POSSIBLE
    assert [o.unusable_reason for o in day.unavailable] == [
        "The 7:00 AM leaves too soon to catch.",
        "The 7:15 AM leaves too soon to catch.",
    ]


def test_weekend_is_blocked(planner, user_id):
    [day] = planner.plan(user_id, [SATURDAY], by(8, 30))

    assert day.action == GoalAction.BLOCKED
    assert day.reason_code == "no_service_day"
    assert day.nearby_days == [TODAY + timedelta(days=4), TODAY + timedelta(days=7)]
    assert day.message == (
        "Shuttles don't run on Saturdays. Friday, November 6 or Monday, November 9 "
        "would get you there by 8:30 AM."
    )


def test_leave_after_picks_the_earliest_departure_after(planner, user_id):
    [day] = planner.plan(user_id, [TOMORROW], TripGoal(leave_after=time(7, 40)))

    assert f"{day.chosen.shuttle.departure_time:%H:%M}" == "07:45"


def test_goal_needs_a_time():
    with pytest.raises(ValueError):
        TripGoal()


class TestTools:
    @pytest.fixture
    def tools(self, db, user_id):
        return {t.name: t for t in create_assistant_tools(db, user_id, FakeEmbedder())}

    def test_plan_trip_is_read_only_and_gives_12_hour_times(self, tools, db, user_id):
        result = tools["plan_trip"].invoke({"dates": [TOMORROW.isoformat()], "arrive_by": "08:00"})

        [day] = result["days"]
        assert day["action"] == "book"
        assert day["chosen"] == {"shuttle_id": day["chosen"]["shuttle_id"], "departure": "7:15 AM",
                                 "arrival": "8:00 AM", "delay_minutes": 0}
        assert departures(db, user_id) == []

    def test_book_trip_plan_accepts_12_hour_input(self, tools, db, user_id):
        result = tools["book_trip_plan"].invoke({"dates": [TOMORROW.isoformat()], "arrive_by": "8:00 am"})

        assert result["days"][0]["succeeded"] is True
        assert departures(db, user_id) == [(TOMORROW, "07:15")]

    def test_bad_time_is_explained(self, tools):
        result = tools["plan_trip"].invoke({"dates": [TOMORROW.isoformat()], "arrive_by": "half eight"})

        assert result == {"error": "arrive_by must be a time like 08:30."}

    def test_missing_goal_is_explained(self, tools):
        result = tools["plan_trip"].invoke({"dates": [TOMORROW.isoformat()]})

        assert "arrive_by" in result["error"]
