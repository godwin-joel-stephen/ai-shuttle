"""Schedule import (F3): typed days → planned and applied booking changes.

Clock: Monday 2026-11-02 06:00 (see conftest).
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.bookings import _create_service
from app.core import clock
from app.db.database import get_db
from app.main import app
from app.models.booking import Booking
from app.repositories.booking_repository import BookingRepository
from app.services.errors import ShuttleUnavailableError
from app.services.schedule_service import (
    PlanAction,
    ScheduleDay,
    ScheduleService,
    WorkdayKind,
    summarize,
)
from tests.conftest import TODAY

MON = TODAY
TUE, WED, THU, FRI, SAT = (TODAY + timedelta(days=n) for n in range(1, 6))


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def make_service(db) -> ScheduleService:
    return ScheduleService(
        booking_service=_create_service(db),
        booking_repository=BookingRepository(db),
    )


def add_booking(db, user_id, shuttle, booking_date) -> Booking:
    booking = Booking(
        user_id=user_id,
        shuttle_id=shuttle.id,
        booking_date=booking_date,
        pickup_time=shuttle.departure_time,
        status="confirmed",
    )
    db.add(booking)
    db.commit()
    return booking


def days(*pairs):
    return [{"date": d.isoformat(), "kind": kind} for d, kind in pairs]


def confirmed_dates(db, user_id):
    return sorted(
        b.booking_date
        for b in db.query(Booking).filter_by(user_id=user_id, status="confirmed")
    )


def by_date(response_days):
    return {day["date"]: day for day in response_days}


def test_plan_maps_each_kind_to_an_action(client, db, user_id, shuttles):
    add_booking(db, user_id, shuttles["Morning Shuttle C"], WED)  # remote → cancel
    add_booking(db, user_id, shuttles["Morning Shuttle D"], THU)  # office → keep

    response = client.post("/schedule/plan", json={
        "user_id": user_id,
        "days": days(
            (TUE, "office"), (WED, "remote"), (THU, "office"),
            (FRI, "leave"), (SAT, "office"),
        ),
    })

    assert response.status_code == 200
    data = response.json()
    plan = by_date(data["days"])
    assert plan[TUE.isoformat()]["action"] == "book"
    assert plan[TUE.isoformat()]["message"] == "Book your usual 7:30 AM shuttle."
    assert plan[WED.isoformat()]["action"] == "cancel"
    assert plan[WED.isoformat()]["bookings"][0]["pickup_time"] == "07:30:00"
    assert plan[THU.isoformat()]["action"] == "keep"
    assert plan[THU.isoformat()]["message"] == "Already booked on the 7:45 AM shuttle."
    assert plan[FRI.isoformat()]["action"] == "none"
    assert plan[SAT.isoformat()]["action"] == "blocked"
    assert plan[SAT.isoformat()]["reason_code"] == "no_service_day"
    assert data["changes"] == 2
    assert data["summary"] == "I'll book 1 day and cancel 1 day."
    # Days come back in date order regardless of input order.
    assert [d["date"] for d in data["days"]] == sorted(plan)


def test_plan_changes_nothing(client, db, user_id):
    client.post("/schedule/plan", json={
        "user_id": user_id, "days": days((TUE, "office"), (WED, "office")),
    })

    assert confirmed_dates(db, user_id) == []


def test_plan_blocks_past_and_out_of_window_days(client, user_id):
    past = TODAY - timedelta(days=3)
    far = TODAY + timedelta(days=17)  # a Thursday beyond the 14-day window

    plan = by_date(client.post("/schedule/plan", json={
        "user_id": user_id, "days": days((past, "office"), (far, "office")),
    }).json()["days"])

    assert plan[past.isoformat()]["reason_code"] == "date_passed"
    assert plan[far.isoformat()]["reason_code"] == "outside_booking_window"
    assert "opens on" in plan[far.isoformat()]["message"]


def test_apply_books_and_cancels(client, db, user_id, shuttles):
    add_booking(db, user_id, shuttles["Morning Shuttle C"], WED)

    response = client.post("/schedule/apply", json={
        "user_id": user_id,
        "days": days((TUE, "office"), (WED, "offsite"), (THU, "office")),
    })

    assert response.status_code == 200
    data = response.json()
    assert data["bookings_changed"] is True
    assert data["summary"] == "Booked 2 days and cancelled 1 day."
    applied = by_date(data["days"])
    assert applied[TUE.isoformat()]["succeeded"] is True
    assert applied[TUE.isoformat()]["message"] == "Booked the 7:30 AM shuttle."
    assert applied[WED.isoformat()]["message"] == "Cancelled your 7:30 AM booking."
    assert applied[WED.isoformat()]["bookings"][0]["status"] == "cancelled"
    assert confirmed_dates(db, user_id) == [TUE, THU]


def test_apply_twice_does_not_double_book(client, db, user_id):
    request = {"user_id": user_id, "days": days((TUE, "office"))}

    client.post("/schedule/apply", json=request)
    second = client.post("/schedule/apply", json=request).json()

    assert second["days"][0]["action"] == "keep"
    assert second["bookings_changed"] is False
    assert second["summary"] == "Nothing changed."
    assert confirmed_dates(db, user_id) == [TUE]


def test_day_away_cancels_both_directions(client, db, user_id, shuttles):
    add_booking(db, user_id, shuttles["Morning Shuttle C"], TUE)
    add_booking(db, user_id, shuttles["Evening Shuttle A"], TUE)

    data = client.post("/schedule/apply", json={
        "user_id": user_id, "days": days((TUE, "leave")),
    }).json()

    assert data["days"][0]["message"] == "Cancelled your 7:30 AM and 5:30 PM bookings."
    assert confirmed_dates(db, user_id) == []


def test_departed_shuttle_is_not_cancelled(db, user_id, shuttles, monkeypatch):
    add_booking(db, user_id, shuttles["Morning Shuttle A"], MON)  # 7:00, gone
    later = add_booking(db, user_id, shuttles["Evening Shuttle A"], MON)
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 11, 2, 7, 10))

    [day] = make_service(db).plan(user_id, [ScheduleDay(MON, WorkdayKind.REMOTE)])

    assert day.action == PlanAction.CANCEL
    assert [b.id for b in day.bookings] == [later.id]


def test_failed_day_is_reported_and_others_still_apply(db, user_id, monkeypatch):
    service = make_service(db)
    book = service.booking_service.book_usual_shuttle

    def flaky(user, booking_date, now=None):
        if booking_date == WED:
            raise ShuttleUnavailableError("The 7:30 AM shuttle is full on Wednesday.")
        return book(user, booking_date, now)

    monkeypatch.setattr(service.booking_service, "book_usual_shuttle", flaky)

    applied = service.apply(user_id, [
        ScheduleDay(TUE, WorkdayKind.OFFICE),
        ScheduleDay(WED, WorkdayKind.OFFICE),
    ])

    assert [d.succeeded for d in applied] == [True, False]
    assert applied[1].reason_code == "shuttle_unavailable"
    assert summarize(applied, applied=True) == (
        "Booked 1 day; 1 day couldn't be changed."
    )
    assert confirmed_dates(db, user_id) == [TUE]


@pytest.mark.parametrize("body", [
    {"days": []},
    {"days": days((TUE, "office"), (TUE, "remote"))},
    {"days": [{"date": TUE.isoformat(), "kind": "cancel everything"}]},
    {"days": [{"date": "next tuesday", "kind": "office"}]},
])
def test_rejects_malformed_schedules(client, user_id, body):
    response = client.post("/schedule/plan", json={"user_id": user_id, **body})

    assert response.status_code == 422


def test_summary_when_nothing_to_do(db, user_id):
    planned = make_service(db).plan(user_id, [ScheduleDay(TUE, WorkdayKind.REMOTE)])

    assert summarize(planned) == "Your bookings already match this schedule."
