from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.shuttle import Shuttle
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.services.errors import (
    InvalidBookingDateError,
    NotFoundError,
    ShuttleUnavailableError,
)


class RescheduleDirection(StrEnum):
    EARLIER = "earlier"
    LATER = "later"


@dataclass(frozen=True)
class BookingOutcome:
    booking: Booking
    already_booked: bool


@dataclass(frozen=True)
class AdjacentShuttles:
    earlier: Shuttle | None
    later: Shuttle | None


class BookingService:
    def __init__(
        self,
        db: Session,
        user_repository: UserRepository,
        preference_repository: PreferenceRepository,
        shuttle_repository: ShuttleRepository,
        booking_repository: BookingRepository,
    ):
        self.db = db
        self.user_repository = user_repository
        self.preference_repository = preference_repository
        self.shuttle_repository = shuttle_repository
        self.booking_repository = booking_repository

    def _resolve_user(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise NotFoundError(f"User {user_id} not found.")

        return user

    def _resolve_usual_shuttle(self, user_id: int):
        preference = self.preference_repository.get_by_user_id(user_id)

        if preference is None or preference.usual_shuttle_id is None:
            raise NotFoundError(
                "You haven't set a usual shuttle yet."
            )

        shuttle = self.shuttle_repository.get_by_id(
            preference.usual_shuttle_id
        )

        if shuttle is None:
            raise NotFoundError(
                f"Usual shuttle "
                f"{preference.usual_shuttle_id} not found."
            )

        return shuttle

    def _resolve_booking(self, user_id: int, booking_id: int) -> Booking:
        booking = self.booking_repository.get_by_id(booking_id)

        if booking is None or booking.user_id != user_id:
            raise NotFoundError(f"Booking {booking_id} not found.")

        return booking

    def book_usual_shuttle(
        self,
        user_id: int,
        booking_date: date,
        today: date | None = None,
    ) -> BookingOutcome:
        today = today or date.today()

        if booking_date < today:
            raise InvalidBookingDateError(
                "That date has already passed."
            )

        user = self._resolve_user(user_id)
        shuttle = self._resolve_usual_shuttle(user_id)

        # Siri and network retries must not create a second seat.
        existing = self.booking_repository.get_confirmed_on_route(
            user_id=user.id,
            route_id=shuttle.route_id,
            booking_date=booking_date,
        )

        if existing is not None:
            return BookingOutcome(booking=existing, already_booked=True)

        if not self.shuttle_repository.has_available_seat(
            shuttle.id,
            booking_date,
        ):
            raise ShuttleUnavailableError(
                f"Your usual {shuttle.departure_time:%-I:%M %p} shuttle "
                f"is full on {booking_date:%A}."
            )

        booking = Booking(
            user_id=user.id,
            shuttle_id=shuttle.id,
            booking_date=booking_date,
            pickup_time=shuttle.departure_time,
            status="confirmed",
        )

        self.booking_repository.create(booking)

        self.db.commit()

        return BookingOutcome(
            booking=self._resolve_booking(user.id, booking.id),
            already_booked=False,
        )

    def get_booking(self, user_id: int, booking_id: int) -> Booking:
        return self._resolve_booking(user_id, booking_id)

    def get_adjacent_shuttles(self, booking: Booking) -> AdjacentShuttles:
        """Nearest shuttles on the same route that still have a seat."""

        shuttles = self.shuttle_repository.list_by_route(
            booking.shuttle.route_id
        )
        index = next(
            i for i, shuttle in enumerate(shuttles)
            if shuttle.id == booking.shuttle_id
        )

        def first_available(candidates: list[Shuttle]) -> Shuttle | None:
            return next(
                (
                    shuttle for shuttle in candidates
                    if self.shuttle_repository.has_available_seat(
                        shuttle.id,
                        booking.booking_date,
                    )
                ),
                None,
            )

        return AdjacentShuttles(
            earlier=first_available(list(reversed(shuttles[:index]))),
            later=first_available(shuttles[index + 1:]),
        )

    def reschedule_booking(
        self,
        user_id: int,
        booking_id: int,
        direction: RescheduleDirection,
    ) -> Booking:
        booking = self._resolve_booking(user_id, booking_id)
        adjacent = self.get_adjacent_shuttles(booking)

        target = (
            adjacent.earlier
            if direction == RescheduleDirection.EARLIER
            else adjacent.later
        )

        if target is None:
            raise ShuttleUnavailableError(
                f"There's no {direction.value} shuttle available "
                f"on {booking.booking_date:%A}."
            )

        booking.shuttle_id = target.id
        booking.pickup_time = target.departure_time

        self.db.commit()
        self.db.expire(booking)

        return self._resolve_booking(user_id, booking_id)

    def get_upcoming_bookings(
        self,
        user_id: int,
        from_date: date | None = None,
    ) -> list[Booking]:
        self._resolve_user(user_id)

        if from_date is None:
            from_date = date.today()

        return self.booking_repository.get_upcoming_by_user_id(
            user_id=user_id,
            from_date=from_date,
        )
