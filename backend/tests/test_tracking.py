from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.db.database import get_db
from app.main import app
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.services.booking_service import BookingService
from app.services.route_geometry import geometry_for
from app.services.tracking_service import TrackingService, TripPhase, compute_status
from app.tools.assistant_tools import create_assistant_tools
from tests.conftest import FIXED_NOW, TOMORROW
from tests.fake_embedder import FakeEmbedder


DEPARTURE = datetime.combine(TOMORROW, datetime.min.time()).replace(hour=7, minute=30)


@pytest.fixture
def booking_service(db):
    return BookingService(
        db=db,
        user_repository=UserRepository(db),
        preference_repository=PreferenceRepository(db),
        shuttle_repository=ShuttleRepository(db),
        booking_repository=BookingRepository(db),
    )


@pytest.fixture
def tracking(db, booking_service):
    return TrackingService(db, booking_service)


@pytest.fixture
def booking(booking_service, user_id):
    # Usual shuttle: 7:30 AM -> 8:15 AM, Home -> Office.
    return booking_service.book_usual_shuttle(user_id, TOMORROW).booking


@pytest.mark.parametrize(
    ("minutes_from_departure", "phase", "to_pickup", "to_arrival", "message"),
    [
        (-20, TripPhase.SCHEDULED, 20, 65, "Your shuttle from Home leaves in 20 minutes."),
        (-10, TripPhase.APPROACHING, 10, 55, "Your shuttle is 10 minutes from Home."),
        (1, TripPhase.BOARDING, None, 44, "Your shuttle is at Home now."),
        (20, TripPhase.IN_TRANSIT, None, 25, "On the way. Arriving at Office in 25 minutes."),
        (50, TripPhase.ARRIVED, None, None, "Arrived at Office."),
    ],
)
def test_phases_follow_the_real_clock(
    booking, minutes_from_departure, phase, to_pickup, to_arrival, message
):
    now = DEPARTURE + timedelta(minutes=minutes_from_departure)

    status = compute_status(booking, None, now)

    assert status.phase is phase
    assert status.minutes_to_pickup == to_pickup
    assert status.minutes_to_arrival == to_arrival
    assert status.message == message
    assert status.pickup_eta == DEPARTURE
    assert status.simulated is False


def test_position_moves_from_depot_to_destination(booking):
    geometry = geometry_for("Home")
    positions = [
        compute_status(booking, None, DEPARTURE + timedelta(minutes=m)).position
        for m in (-30, -7, 1, 20, 60)
    ]

    assert positions[0] == geometry.depot
    assert positions[1] not in (geometry.depot, geometry.pickup)
    assert positions[2] == geometry.pickup
    assert positions[3] not in geometry.path
    assert positions[4] == geometry.destination


def test_simulation_replays_trip_now_at_speed(tracking, booking, user_id, monkeypatch):
    tracking.start_simulation(user_id, booking.id, start_minutes=-12, speed=4)

    one_minute_later = FIXED_NOW + timedelta(minutes=1)
    monkeypatch.setattr(clock, "now", lambda: one_minute_later)
    status = tracking.status(user_id, booking.id)

    # 1 real minute at 4x = 4 simulated minutes: 8 left, i.e. 2 real minutes.
    assert status.phase is TripPhase.APPROACHING
    assert status.minutes_to_pickup == 8
    assert status.pickup_eta == one_minute_later + timedelta(minutes=2)
    assert status.simulated is True


def test_delay_pushes_pickup_back(tracking, booking, user_id):
    tracking.start_simulation(user_id, booking.id, start_minutes=-10)

    status = tracking.set_delay(user_id, booking.id, 15)

    assert status.minutes_to_pickup == 25
    assert status.message == "Your shuttle is 25 minutes from Home, running 15 minutes late."


def test_next_trip_prefers_the_simulated_one(tracking, booking_service, booking, user_id):
    later = booking_service.book_usual_shuttle(user_id, TOMORROW + timedelta(days=1)).booking
    tracking.start_simulation(user_id, later.id)

    assert tracking.next_trip_status(user_id).booking.id == later.id

    tracking.stop_simulation(user_id, later.id)
    assert tracking.next_trip_status(user_id).booking.id == booking.id


def test_cancelled_booking_is_not_tracked(tracking, booking_service, booking, user_id):
    tracking.start_simulation(user_id, booking.id)
    booking_service.cancel_booking(user_id, booking.id)

    assert tracking.next_trip_status(user_id) is None


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_tracking_endpoints(client, booking, user_id):
    assert client.get(f"/tracking/next?user_id={user_id + 1}").status_code == 404

    started = client.post(
        f"/simulator/trips/{booking.id}",
        json={"user_id": user_id, "start_minutes": -12, "speed": 2},
    ).json()
    assert started["phase"] == "approaching"
    assert started["simulated"] is True
    assert started["pickup_name"] == "Home"
    assert len(started["route"]) == 8
    pickup_eta = datetime.fromisoformat(started["pickup_eta"])
    assert pickup_eta.tzinfo is not None
    assert pickup_eta.microsecond == 0

    delayed = client.post(
        f"/simulator/trips/{booking.id}/delay",
        json={"user_id": user_id, "minutes": 10},
    ).json()
    assert delayed["delay_minutes"] == 10

    nxt = client.get(f"/tracking/next?user_id={user_id}").json()
    assert nxt["booking_id"] == booking.id

    assert client.delete(f"/simulator/trips/{booking.id}?user_id={user_id}").status_code == 204
    assert client.get(f"/bookings/{booking.id}/tracking?user_id={user_id}").json()["simulated"] is False


def test_agent_tool_reports_next_trip(db, tracking, booking, user_id):
    tracking.start_simulation(user_id, booking.id, start_minutes=-9)
    tools = {t.name: t for t in create_assistant_tools(db, user_id, FakeEmbedder())}

    result = tools["get_shuttle_status"].invoke({})

    assert result["phase"] == "approaching"
    assert result["minutes_to_pickup"] == 9
    assert result["summary"] == "Your shuttle is 9 minutes from Home."
