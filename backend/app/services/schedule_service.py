"""Turn a work schedule into booking changes (F3 schedule import).

The phone reads the schedule document on-device and sends only typed
days (`date` + `kind`); document text never reaches the backend or any
cloud model. Planning is deterministic and reuses BookingService, so an
imported schedule follows exactly the same rules as Siri, widgets, chat
and MCP.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from app.core import clock
from app.models.booking import Booking
from app.repositories.booking_repository import BookingRepository
from app.services.booking_service import BookingService
from app.services.errors import BookingError, DatePassedError


class WorkdayKind(StrEnum):
    OFFICE = "office"    # needs the usual shuttle
    REMOTE = "remote"    # working from home
    OFFSITE = "offsite"  # working somewhere other than the office
    LEAVE = "leave"      # not working (holiday, PTO, sick)


class PlanAction(StrEnum):
    BOOK = "book"        # office day without a booking
    KEEP = "keep"        # office day, already booked
    CANCEL = "cancel"    # non-office day with booking(s)
    NONE = "none"        # non-office day, nothing booked
    BLOCKED = "blocked"  # a booking rule prevents the change


ACTIONABLE = {PlanAction.BOOK, PlanAction.CANCEL}


@dataclass(frozen=True)
class ScheduleDay:
    date: date
    kind: WorkdayKind


@dataclass
class PlannedDay:
    date: date
    kind: WorkdayKind
    action: PlanAction
    message: str
    reason_code: str | None = None
    # KEEP/CANCEL: the existing bookings; after apply, BOOK: the new one.
    bookings: list[Booking] = field(default_factory=list)
    # Set by apply(); None while only planned.
    succeeded: bool | None = None


def _time(booking_or_time) -> str:
    value = getattr(booking_or_time, "pickup_time", booking_or_time)
    return f"{value:%-I:%M %p}"


class ScheduleService:
    def __init__(
        self,
        booking_service: BookingService,
        booking_repository: BookingRepository,
    ):
        self.booking_service = booking_service
        self.booking_repository = booking_repository

    def plan(
        self,
        user_id: int,
        days: list[ScheduleDay],
        now: datetime | None = None,
    ) -> list[PlannedDay]:
        now = now or clock.now()
        return [
            self._plan_day(user_id, day, now)
            for day in sorted(days, key=lambda d: d.date)
        ]

    def apply(
        self,
        user_id: int,
        days: list[ScheduleDay],
    ) -> list[PlannedDay]:
        """Re-plan against current bookings, then make the changes.

        Each day succeeds or fails on its own; the result says which, so
        the app never claims a change that didn't happen (or hides one
        that did).
        """

        planned = self.plan(user_id, days)

        for day in planned:
            if day.action == PlanAction.BOOK:
                self._apply_booking(user_id, day)
            elif day.action == PlanAction.CANCEL:
                self._apply_cancellation(user_id, day)

        return planned

    def _plan_day(
        self,
        user_id: int,
        day: ScheduleDay,
        now: datetime,
    ) -> PlannedDay:
        if day.date < now.date():
            error = DatePassedError("That date has already passed.")
            return PlannedDay(
                date=day.date,
                kind=day.kind,
                action=PlanAction.BLOCKED,
                message=str(error),
                reason_code=error.code,
            )

        if day.kind == WorkdayKind.OFFICE:
            return self._plan_office_day(user_id, day, now)

        return self._plan_day_away(user_id, day, now)

    def _plan_office_day(
        self,
        user_id: int,
        day: ScheduleDay,
        now: datetime,
    ) -> PlannedDay:
        eligibility = self.booking_service.check_eligibility(
            user_id, day.date, now
        )

        if eligibility.already_booked:
            booked = self._usual_route_booking(user_id, day.date)
            return PlannedDay(
                date=day.date,
                kind=day.kind,
                action=PlanAction.KEEP,
                message=f"Already booked on the {_time(booked)} shuttle.",
                bookings=[booked],
            )

        if not eligibility.eligible:
            error = eligibility.error
            return PlannedDay(
                date=day.date,
                kind=day.kind,
                action=PlanAction.BLOCKED,
                message=str(error),
                reason_code=error.code if error else None,
            )

        shuttle = self.booking_service.get_usual_shuttle(user_id, day.date)
        return PlannedDay(
            date=day.date,
            kind=day.kind,
            action=PlanAction.BOOK,
            message=f"Book your usual {_time(shuttle.departure_time)} shuttle.",
        )

    def _plan_day_away(
        self,
        user_id: int,
        day: ScheduleDay,
        now: datetime,
    ) -> PlannedDay:
        bookings = self.booking_repository.get_confirmed_on_date(
            user_id=user_id,
            booking_date=day.date,
        )
        # A shuttle that has already left can't be cancelled.
        cancellable = [
            booking for booking in bookings
            if datetime.combine(booking.booking_date, booking.pickup_time) > now
        ]

        if not cancellable:
            return PlannedDay(
                date=day.date,
                kind=day.kind,
                action=PlanAction.NONE,
                message="No shuttle needed.",
            )

        times = " and ".join(_time(booking) for booking in cancellable)
        plural = "s" if len(cancellable) > 1 else ""
        return PlannedDay(
            date=day.date,
            kind=day.kind,
            action=PlanAction.CANCEL,
            message=f"Cancel your {times} booking{plural}.",
            bookings=cancellable,
        )

    def _apply_booking(self, user_id: int, day: PlannedDay) -> None:
        try:
            outcome = self.booking_service.book_usual_shuttle(user_id, day.date)
        except BookingError as error:
            day.succeeded = False
            day.reason_code = error.code
            day.message = str(error)
            return

        day.succeeded = True
        day.bookings = [outcome.booking]
        day.message = f"Booked the {_time(outcome.booking)} shuttle."

    def _apply_cancellation(self, user_id: int, day: PlannedDay) -> None:
        cancelled = []
        for booking in day.bookings:
            try:
                cancelled.append(
                    self.booking_service.cancel_booking(user_id, booking.id)
                )
            except BookingError as error:
                day.reason_code = error.code

        day.succeeded = len(cancelled) == len(day.bookings)
        day.bookings = cancelled
        if day.succeeded:
            times = " and ".join(_time(booking) for booking in cancelled)
            plural = "s" if len(cancelled) > 1 else ""
            day.message = f"Cancelled your {times} booking{plural}."
        else:
            day.message = "Couldn't cancel every booking on this day."

    def _usual_route_booking(self, user_id: int, booking_date: date) -> Booking:
        shuttle = self.booking_service.get_usual_shuttle(user_id)
        return self.booking_repository.get_confirmed_on_route(
            user_id=user_id,
            route_id=shuttle.route_id,
            booking_date=booking_date,
        )


def summarize(days: list[PlannedDay], applied: bool = False) -> str:
    """One sentence for the review screen or the result."""

    def count(action: PlanAction) -> int:
        return sum(
            1 for day in days
            if day.action == action and (not applied or day.succeeded)
        )

    def days_text(n: int) -> str:
        return f"{n} day{'s' if n != 1 else ''}"

    booked, cancelled = count(PlanAction.BOOK), count(PlanAction.CANCEL)
    failed = sum(1 for day in days if day.succeeded is False)

    if applied:
        parts = []
        if booked:
            parts.append(f"booked {days_text(booked)}")
        if cancelled:
            parts.append(f"cancelled {days_text(cancelled)}")
        text = " and ".join(parts).capitalize() if parts else "Nothing changed"
        if failed:
            text += f"; {days_text(failed)} couldn't be changed"
        return text + "."

    parts = []
    if booked:
        parts.append(f"book {days_text(booked)}")
    if cancelled:
        parts.append(f"cancel {days_text(cancelled)}")
    if not parts:
        return "Your bookings already match this schedule."
    return "I'll " + " and ".join(parts) + "."
