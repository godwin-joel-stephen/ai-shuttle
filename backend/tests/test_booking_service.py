from datetime import date, timedelta

import pytest

from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.services.booking_service import BookingService, RescheduleDirection
from app.services.errors import (
    InvalidBookingDateError,
    NotFoundError,
    ShuttleUnavailableError,
)
from app.tools.booking_tools import book_shuttle


TOMORROW = date.today() + timedelta(days=1)


def make_service(db) -> BookingService:
    return BookingService(
        db=db,
        user_repository=UserRepository(db),
        preference_repository=PreferenceRepository(db),
        shuttle_repository=ShuttleRepository(db),
        booking_repository=BookingRepository(db),
    )


def test_book_shuttle_persists_usual_shuttle(db, user_id, shuttles):
    outcome = book_shuttle(db=db, user_id=user_id, booking_date=TOMORROW)

    booking = outcome.booking
    assert outcome.already_booked is False
    assert booking.user_id == user_id
    assert booking.shuttle_id == shuttles["Morning Shuttle C"].id
    assert booking.booking_date == TOMORROW
    assert booking.pickup_time.isoformat() == "07:30:00"
    assert booking.status == "confirmed"


def test_booking_twice_returns_existing_booking(db, user_id):
    first = book_shuttle(db=db, user_id=user_id, booking_date=TOMORROW)
    second = book_shuttle(db=db, user_id=user_id, booking_date=TOMORROW)

    assert second.already_booked is True
    assert second.booking.id == first.booking.id


def test_past_date_is_rejected(db, user_id):
    with pytest.raises(InvalidBookingDateError):
        make_service(db).book_usual_shuttle(
            user_id=user_id,
            booking_date=date.today() - timedelta(days=1),
        )


def test_unknown_user_is_not_found(db):
    with pytest.raises(NotFoundError):
        make_service(db).book_usual_shuttle(
            user_id=999_999,
            booking_date=TOMORROW,
        )


def test_reschedule_moves_to_adjacent_shuttles(db, user_id, shuttles):
    service = make_service(db)
    booking = service.book_usual_shuttle(user_id, TOMORROW).booking

    earlier = service.reschedule_booking(
        user_id, booking.id, RescheduleDirection.EARLIER
    )
    assert earlier.shuttle_id == shuttles["Morning Shuttle B"].id
    assert earlier.pickup_time.isoformat() == "07:15:00"

    later = service.reschedule_booking(
        user_id, booking.id, RescheduleDirection.LATER
    )
    assert later.shuttle_id == shuttles["Morning Shuttle C"].id


def test_reschedule_without_alternative_fails(db, user_id):
    service = make_service(db)
    booking = service.book_usual_shuttle(user_id, TOMORROW).booking

    for _ in range(2):
        booking = service.reschedule_booking(
            user_id, booking.id, RescheduleDirection.EARLIER
        )

    adjacent = service.get_adjacent_shuttles(booking)
    assert adjacent.earlier is None
    assert adjacent.later is not None

    with pytest.raises(ShuttleUnavailableError):
        service.reschedule_booking(
            user_id, booking.id, RescheduleDirection.EARLIER
        )
