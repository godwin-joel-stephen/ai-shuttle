from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum

from sqlalchemy.orm import Session

from app.core import clock
from app.models.booking import Booking
from app.models.shuttle import Shuttle
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.services.errors import (
    BookingCutoffPassedError,
    BookingError,
    DatePassedError,
    NoServiceDayError,
    NotFoundError,
    OutsideBookingWindowError,
    ShuttleUnavailableError,
)


# Booking rules. knowledge/booking_policy.md explains them to users, so
# keep the two in sync.
SERVICE_WEEKDAYS = range(0, 5)  # Monday to Friday
BOOKING_WINDOW_DAYS = 14
SAME_DAY_CUTOFF = timedelta(minutes=30)


class RescheduleDirection(StrEnum):
    EARLIER = "earlier"
    LATER = "later"


@dataclass(frozen=True)
class BookingOutcome:
    booking: Booking
    already_booked: bool


@dataclass(frozen=True)
class Eligibility:
    eligible: bool
    already_booked: bool = False
    error: BookingError | None = None


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

    def _validate_departure(
        self,
        shuttle: Shuttle,
        booking_date: date,
        now: datetime,
    ) -> None:
        """Raise the first booking rule this departure breaks."""

        today = now.date()

        if booking_date < today:
            raise DatePassedError("That date has already passed.")

        if booking_date.weekday() not in SERVICE_WEEKDAYS:
            raise NoServiceDayError(
                f"Shuttles don't run on {booking_date:%A}s."
            )

        last_bookable = today + timedelta(days=BOOKING_WINDOW_DAYS)
        if booking_date > last_bookable:
            opens = booking_date - timedelta(days=BOOKING_WINDOW_DAYS)
            raise OutsideBookingWindowError(
                f"Bookings open {BOOKING_WINDOW_DAYS} days ahead, so "
                f"{booking_date:%A, %B %-d} opens on {opens:%B %-d}."
            )

        departure = datetime.combine(booking_date, shuttle.departure_time)
        if now > departure - SAME_DAY_CUTOFF:
            raise BookingCutoffPassedError(
                f"Booking for the {shuttle.departure_time:%-I:%M %p} "
                f"shuttle closed 30 minutes before departure."
            )

        if not self.shuttle_repository.has_available_seat(
            shuttle.id,
            booking_date,
        ):
            raise ShuttleUnavailableError(
                f"The {shuttle.departure_time:%-I:%M %p} shuttle "
                f"is full on {booking_date:%A}."
            )

    def _is_bookable(self, shuttle: Shuttle, booking_date: date) -> bool:
        try:
            self._validate_departure(shuttle, booking_date, clock.now())
        except BookingError:
            return False
        return True

    def check_eligibility(
        self,
        user_id: int,
        booking_date: date,
        now: datetime | None = None,
    ) -> Eligibility:
        """Whether the usual shuttle could be booked, without booking it."""

        now = now or clock.now()
        shuttle = self._resolve_usual_shuttle(user_id)

        if self.booking_repository.get_confirmed_on_route(
            user_id=user_id,
            route_id=shuttle.route_id,
            booking_date=booking_date,
        ):
            return Eligibility(eligible=False, already_booked=True)

        try:
            self._validate_departure(shuttle, booking_date, now)
        except BookingError as e:
            return Eligibility(eligible=False, error=e)

        return Eligibility(eligible=True)

    def book_usual_shuttle(
        self,
        user_id: int,
        booking_date: date,
        now: datetime | None = None,
    ) -> BookingOutcome:
        now = now or clock.now()

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

        self._validate_departure(shuttle, booking_date, now)

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

    def get_usual_shuttle(self, user_id: int) -> Shuttle:
        return self._resolve_usual_shuttle(user_id)

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
                    if self._is_bookable(shuttle, booking.booking_date)
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

    def list_usual_route_shuttles(
        self,
        user_id: int,
        booking_date: date,
    ) -> list[tuple[Shuttle, bool]]:
        """Shuttles on the user's usual route, each with whether it can
        still be booked (seats, service day, cut-off)."""

        usual = self._resolve_usual_shuttle(user_id)

        return [
            (shuttle, self._is_bookable(shuttle, booking_date))
            for shuttle in self.shuttle_repository.list_by_route(
                usual.route_id
            )
        ]

    def move_booking(
        self,
        user_id: int,
        booking_id: int,
        shuttle_id: int,
    ) -> Booking:
        booking = self._resolve_booking(user_id, booking_id)
        target = self.shuttle_repository.get_by_id(shuttle_id)

        if target is None:
            raise NotFoundError(f"Shuttle {shuttle_id} not found.")

        if target.route_id != booking.shuttle.route_id:
            raise ShuttleUnavailableError(
                "That shuttle runs on a different route."
            )

        if target.id == booking.shuttle_id:
            return booking

        self._validate_departure(target, booking.booking_date, clock.now())

        booking.shuttle_id = target.id
        booking.pickup_time = target.departure_time

        self.db.commit()
        self.db.expire(booking)

        return self._resolve_booking(user_id, booking_id)

    def cancel_booking(self, user_id: int, booking_id: int) -> Booking:
        booking = self._resolve_booking(user_id, booking_id)

        booking.status = "cancelled"

        self.db.commit()

        return booking

    def get_upcoming_bookings(
        self,
        user_id: int,
        from_date: date | None = None,
    ) -> list[Booking]:
        self._resolve_user(user_id)

        if from_date is None:
            from_date = clock.today()

        return self.booking_repository.get_upcoming_by_user_id(
            user_id=user_id,
            from_date=from_date,
        )
