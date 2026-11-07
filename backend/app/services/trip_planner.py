"""Goal-based trip planning (F7): "get me to the office by 8:30".

Deterministic: given a goal (arrive by and/or leave after) and dates, it
weighs every shuttle on the rider's route — arrival time including any
known delay, whether it can still be caught (walk + pickup buffer), seats
and booking rules, and the booking the rider already has — and picks one
per day:

1. the current booking, if it already meets the goal (no churn);
2. otherwise the usual shuttle, if it meets the goal (the habit learned
   for that weekday, see habit_service);
3. otherwise the latest departure that meets an arrive-by goal (most time
   at home), or the earliest after a leave-after goal.

When nothing meets the goal it says so, with the soonest-arriving option
and how late it would be; it never books something that misses the goal.
The LLM only turns the request into a goal and words the result.

The same option logic gives F4's "faster alternative" for a delayed trip.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING

from app.core import clock
from app.models.booking import Booking
from app.models.shuttle import Shuttle
from app.services.booking_service import BookingService
from app.services.errors import BookingError

if TYPE_CHECKING:
    from app.services.tracking_service import TrackingService, TripStatus


# Pickup rules: be at the stop 5 minutes before the shuttle.
PICKUP_BUFFER_MINUTES = 5

# Rules that rule out a whole day, whichever shuttle is chosen.
DAY_LEVEL_CODES = {"date_passed", "no_service_day", "outside_booking_window"}

# How far to look for a nearby day that works when a day is blocked.
NEARBY_SEARCH_DAYS = 7


class GoalAction(StrEnum):
    BOOK = "book"                  # no booking yet; book the chosen shuttle
    MOVE = "move"                  # booked, but too late; move to the chosen one
    KEEP = "keep"                  # current booking already meets the goal
    NOT_POSSIBLE = "not_possible"  # no shuttle meets the goal
    BLOCKED = "blocked"            # a booking rule rules out the day


WORKABLE = {GoalAction.BOOK, GoalAction.MOVE, GoalAction.KEEP}


@dataclass(frozen=True)
class TripGoal:
    arrive_by: time | None = None
    leave_after: time | None = None

    def __post_init__(self):
        if self.arrive_by is None and self.leave_after is None:
            raise ValueError("A goal needs an arrival or departure time.")

    def describe(self) -> str:
        parts = []
        if self.arrive_by:
            parts.append(f"by {_t(self.arrive_by)}")
        if self.leave_after:
            parts.append(f"leaving after {_t(self.leave_after)}")
        return " and ".join(parts)


@dataclass(frozen=True)
class Option:
    shuttle: Shuttle
    # Expected arrival on the trip's own schedule, including known delay.
    arrival: datetime
    delay_minutes: int
    # The booking rule that prevents booking it (None = bookable).
    problem: BookingError | None
    # Can the rider still get to the stop in time for it?
    catchable: bool
    current: bool

    @property
    def usable(self) -> bool:
        return self.current or (self.problem is None and self.catchable)

    @property
    def unusable_reason(self) -> str:
        if self.problem is not None:
            return str(self.problem)
        return f"The {_t(self.shuttle.departure_time)} leaves too soon to catch."


@dataclass
class DayPlan:
    date: date
    goal: TripGoal
    action: GoalAction
    message: str
    reason_code: str | None = None
    current: Booking | None = None
    # The current booking as an option (arrival includes its delay).
    current_option: Option | None = None
    chosen: Option | None = None
    # NOT_POSSIBLE: the soonest-arriving usable option.
    best_effort: Option | None = None
    late_by_minutes: int | None = None
    # Shuttles that would meet the goal but can't be used (full, cut-off).
    unavailable: list[Option] = field(default_factory=list)
    # BLOCKED: nearest days before/after where the goal can be met.
    nearby_days: list[date] = field(default_factory=list)
    # Set by apply().
    succeeded: bool | None = None
    booking: Booking | None = None


def _t(value: time | datetime) -> str:
    return f"{value:%-I:%M %p}"


def _minutes(delta: timedelta) -> int:
    return round(delta.total_seconds() / 60)


def day_options(
    booking_service: BookingService,
    shuttles: list[Shuttle],
    booking_date: date,
    current: Booking | None,
    status: TripStatus | None,
    walk_minutes: int,
    now: datetime,
) -> list[Option]:
    """Every shuttle on the route for a day, as the rider sees it now.

    With a live status for the current booking, time is measured on that
    trip's timeline (it may be a simulation replayed now); otherwise on
    the real clock.
    """

    options = []
    for shuttle in shuttles:
        departure = datetime.combine(booking_date, shuttle.departure_time)
        is_current = current is not None and shuttle.id == current.shuttle_id

        if status is not None:
            current_departure = datetime.combine(booking_date, status.booking.shuttle.departure_time)
            lead = _minutes(departure - current_departure) - status.timeline_minutes
        else:
            lead = _minutes(departure - now)

        delay = status.delay_minutes if (is_current and status is not None) else 0
        options.append(Option(
            shuttle=shuttle,
            arrival=datetime.combine(booking_date, shuttle.arrival_time) + timedelta(minutes=delay),
            delay_minutes=delay,
            problem=None if is_current else booking_service.departure_problem(shuttle, booking_date, now),
            catchable=lead > walk_minutes + PICKUP_BUFFER_MINUTES,
            current=is_current,
        ))
    return options


def faster_alternative(options: list[Option]) -> tuple[Option, int] | None:
    """For a delayed current trip: the usable shuttle arriving soonest,
    if it beats the current one, with the minutes saved."""

    current = next((o for o in options if o.current), None)
    candidates = [o for o in options if o.usable and not o.current]
    if current is None or not candidates:
        return None

    best = min(candidates, key=lambda o: o.arrival)
    saved = _minutes(current.arrival - best.arrival)
    return (best, saved) if saved > 0 else None


class TripPlanner:
    def __init__(self, booking_service: BookingService, tracking: TrackingService):
        self.booking_service = booking_service
        self.tracking = tracking

    def plan(self, user_id: int, dates: list[date], goal: TripGoal) -> list[DayPlan]:
        return [self._plan_day(user_id, day, goal) for day in sorted(set(dates))]

    def apply(self, user_id: int, dates: list[date], goal: TripGoal) -> list[DayPlan]:
        """Plan, then book or move where a shuttle meets the goal. Days
        that can't meet it are reported, never "fixed" with a late
        shuttle. Each day succeeds or fails on its own."""

        plans = self.plan(user_id, dates, goal)
        for day in plans:
            try:
                if day.action == GoalAction.BOOK:
                    outcome = self.booking_service.book_shuttle(user_id, day.date, day.chosen.shuttle)
                    day.booking = outcome.booking
                    day.message = (
                        f"Booked the {_t(day.chosen.shuttle.departure_time)}, "
                        f"arriving {_t(day.chosen.arrival)}." + self._unavailable_note(day)
                    )
                elif day.action == GoalAction.MOVE:
                    # Read before moving: the move updates day.current too.
                    previous = day.current_option.shuttle.departure_time
                    status = self.tracking.move_booking(user_id, day.current.id, day.chosen.shuttle.id)
                    day.booking = status.booking
                    day.message = (
                        f"Moved you from the {_t(previous)} to the "
                        f"{_t(day.chosen.shuttle.departure_time)}, arriving {_t(day.chosen.arrival)}."
                    )
                else:
                    continue
                day.succeeded = True
            except BookingError as error:
                day.succeeded = False
                day.reason_code = error.code
                day.message = str(error)
        return plans

    def _plan_day(
        self,
        user_id: int,
        booking_date: date,
        goal: TripGoal,
        suggest_nearby: bool = True,
    ) -> DayPlan:
        service = self.booking_service
        usual = service.get_usual_shuttle(user_id, booking_date)
        shuttles = service.shuttle_repository.list_by_route(usual.route_id)
        current = service.booking_repository.get_confirmed_on_route(
            user_id=user_id, route_id=usual.route_id, booking_date=booking_date,
        )
        status = self.tracking.status(user_id, current.id) if current else None
        walk = (status.walk_minutes or 0) if status else 0
        options = day_options(service, shuttles, booking_date, current, status, walk, clock.now())

        plan = DayPlan(
            date=booking_date,
            goal=goal,
            action=GoalAction.NOT_POSSIBLE,
            message="",
            current=current,
            current_option=next((o for o in options if o.current), None),
        )

        # A rule that rules out every shuttle that day (weekend, window, past).
        if current is None:
            codes = {o.problem.code if o.problem else None for o in options}
            if len(codes) == 1 and codes <= DAY_LEVEL_CODES:
                error = options[0].problem
                plan.action = GoalAction.BLOCKED
                plan.reason_code = error.code
                plan.message = str(error)
                if suggest_nearby:
                    plan.nearby_days = self._nearby_days(user_id, booking_date, goal)
                    if plan.nearby_days:
                        names = " or ".join(f"{d:%A, %B %-d}" for d in plan.nearby_days)
                        plan.message += f" {names} would get you there {goal.describe()}."
                return plan

        deadline = datetime.combine(booking_date, goal.arrive_by) if goal.arrive_by else None

        def meets(option: Option) -> bool:
            if deadline is not None and option.arrival > deadline:
                return False
            if goal.leave_after is not None and option.shuttle.departure_time < goal.leave_after:
                return False
            return True

        on_time = [o for o in options if meets(o)]
        usable = [o for o in on_time if o.usable]
        plan.unavailable = [o for o in on_time if not o.usable]

        if usable:
            plan.chosen = self._choose(usable, usual, goal)
            if plan.chosen.current:
                plan.action = GoalAction.KEEP
            elif current is not None:
                plan.action = GoalAction.MOVE
            else:
                plan.action = GoalAction.BOOK
            plan.message = self._describe(plan)
            return plan

        # Nothing meets the goal: report the soonest arrival honestly.
        candidates = [
            o for o in options
            if o.usable and (goal.leave_after is None or o.shuttle.departure_time >= goal.leave_after)
        ]
        if candidates:
            plan.best_effort = min(candidates, key=lambda o: o.arrival)
            if deadline is not None:
                plan.late_by_minutes = max(0, _minutes(plan.best_effort.arrival - deadline))
        plan.message = self._describe(plan)
        return plan

    def _nearby_days(self, user_id: int, blocked: date, goal: TripGoal) -> list[date]:
        """The closest day before and after a blocked one where a shuttle
        meets the goal (from today on)."""

        found = []
        for step in (-1, 1):
            for distance in range(1, NEARBY_SEARCH_DAYS + 1):
                day = blocked + timedelta(days=step * distance)
                if day < clock.today():
                    break
                if self._plan_day(user_id, day, goal, suggest_nearby=False).action in WORKABLE:
                    found.append(day)
                    break
        return sorted(found)

    @staticmethod
    def _choose(usable: list[Option], usual: Shuttle, goal: TripGoal) -> Option:
        for option in usable:
            if option.current:
                return option
        for option in usable:
            if option.shuttle.id == usual.id:
                return option
        if goal.arrive_by is not None:
            return max(usable, key=lambda o: o.shuttle.departure_time)
        return min(usable, key=lambda o: o.shuttle.departure_time)

    @staticmethod
    def _unavailable_note(plan: DayPlan) -> str:
        notes = [o.unusable_reason for o in plan.unavailable]
        return (" " + " ".join(notes)) if notes else ""

    def _describe(self, plan: DayPlan) -> str:
        goal = plan.goal.describe()
        chosen = plan.chosen

        if plan.action == GoalAction.KEEP:
            late = f", running {chosen.delay_minutes} minutes late" if chosen.delay_minutes else ""
            return (
                f"You're already on the {_t(chosen.shuttle.departure_time)}{late}, "
                f"arriving {_t(chosen.arrival)}, which gets you there {goal}."
            )
        if plan.action == GoalAction.BOOK:
            return (
                f"Book the {_t(chosen.shuttle.departure_time)}, arriving {_t(chosen.arrival)}."
                + self._unavailable_note(plan)
            )
        if plan.action == GoalAction.MOVE:
            return (
                f"Your {_t(plan.current.shuttle.departure_time)} arrives {_t(plan.current_option.arrival)}, "
                f"too late to get you there {goal}; move to the {_t(chosen.shuttle.departure_time)}, "
                f"arriving {_t(chosen.arrival)}." + self._unavailable_note(plan)
            )

        # NOT_POSSIBLE
        text = f"No shuttle gets you there {goal}."
        best = plan.best_effort
        if best is None:
            return text + " There's no shuttle you can still take that day."

        late = f" ({plan.late_by_minutes} minutes late)" if plan.late_by_minutes else ""
        if best.current:
            delay = f" is running {best.delay_minutes} minutes late and" if best.delay_minutes else ""
            return text + (
                f" Your {_t(best.shuttle.departure_time)}{delay} arrives {_t(best.arrival)}{late},"
                " the soonest possible."
            )
        current = plan.current_option
        if current is not None:
            saved = _minutes(current.arrival - best.arrival)
            delay = f" is running {current.delay_minutes} minutes late and" if current.delay_minutes else ""
            return text + (
                f" Your {_t(current.shuttle.departure_time)}{delay} arrives {_t(current.arrival)};"
                f" the {_t(best.shuttle.departure_time)} arrives {_t(best.arrival)}{late},"
                f" {saved} minutes sooner, if you want to switch."
            )
        return text + (
            f" The soonest is the {_t(best.shuttle.departure_time)}, arriving {_t(best.arrival)}{late}."
        )
