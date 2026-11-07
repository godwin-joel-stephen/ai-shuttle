"""Learns the rider's usual shuttle from the rides they actually booked.

For a given weekday the usual shuttle is, in order of precedence:

1. pinned   the rider chose it explicitly; always wins.
2. weekday  the departure they took on most of their recent rides on that
            weekday ("you took it on 4 of your last 5 Mondays").
3. overall  the departure they took on most of their recent rides.
4. default  the saved preference (seeded as the 7:30).

A habit only changes which shuttle "my usual" means when the rider asks
for a booking. Nothing is ever booked without them asking.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from sqlalchemy.orm import Session

from app.core import clock
from app.models.booking import Booking
from app.models.preference import Preference
from app.models.shuttle import Shuttle
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.services.errors import NotFoundError, ShuttleUnavailableError


# Only rides in this window count, so an old habit fades out.
LOOKBACK = timedelta(weeks=8)
# Most recent rides considered per weekday and overall.
WEEKDAY_SAMPLE = 5
OVERALL_SAMPLE = 10
# A habit needs at least this many rides on the same departure, and more
# than half of the sample.
MIN_RIDES = 3

SERVICE_WEEKDAYS = range(0, 5)  # Monday to Friday, as in BookingService


class HabitSource(StrEnum):
    PINNED = "pinned"
    WEEKDAY = "weekday"
    OVERALL = "overall"
    DEFAULT = "default"


@dataclass(frozen=True)
class Habit:
    weekday: int  # 0 = Monday
    shuttle: Shuttle
    source: HabitSource
    # Rides on `shuttle` within the last `sample` rides behind the habit.
    rides: int = 0
    sample: int = 0
    # Rides this weekday often enough that a missing booking is worth a
    # reminder (independent of which shuttle is usual).
    regular: bool = False

    @property
    def learned(self) -> bool:
        return self.source in (HabitSource.WEEKDAY, HabitSource.OVERALL)

    @property
    def weekday_name(self) -> str:
        return ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday")[self.weekday]

    @property
    def reason(self) -> str:
        """Why this is the usual, as a clause: "you took it on …"."""

        if self.source == HabitSource.PINNED:
            return "you pinned it as your usual"
        if self.source == HabitSource.DEFAULT:
            return "it's your saved usual shuttle"

        noun = f"{self.weekday_name}s" if self.source == HabitSource.WEEKDAY else "rides"
        if self.rides == self.sample:
            return f"you took it on each of your last {self.sample} {noun}"
        return f"you took it on {self.rides} of your last {self.sample} {noun}"


def _winner(rides: list[Booking]) -> tuple[Shuttle, int] | None:
    """The departure behind most of these rides (newest first), if any
    clears the habit threshold. Ties go to the most recently taken."""

    if not rides:
        return None
    counts = Counter(ride.shuttle_id for ride in rides)
    newest = {}
    for index, ride in enumerate(rides):
        newest.setdefault(ride.shuttle_id, index)
    shuttle_id = max(counts, key=lambda s: (counts[s], -newest[s]))
    count = counts[shuttle_id]
    if count < MIN_RIDES or count * 2 <= len(rides):
        return None
    shuttle = next(ride.shuttle for ride in rides if ride.shuttle_id == shuttle_id)
    return shuttle, count


class HabitService:
    def __init__(
        self,
        db: Session,
        preference_repository: PreferenceRepository,
        shuttle_repository: ShuttleRepository,
        booking_repository: BookingRepository,
    ):
        self.db = db
        self.preference_repository = preference_repository
        self.shuttle_repository = shuttle_repository
        self.booking_repository = booking_repository

    def _preference(self, user_id: int) -> Preference:
        preference = self.preference_repository.get_by_user_id(user_id)
        if preference is None or preference.usual_shuttle_id is None:
            raise NotFoundError("You haven't set a usual shuttle yet.")
        return preference

    def saved_shuttle(self, user_id: int) -> Shuttle:
        """The saved (default or pinned) usual shuttle; also fixes the route."""

        preference = self._preference(user_id)
        shuttle = self.shuttle_repository.get_by_id(preference.usual_shuttle_id)
        if shuttle is None:
            raise NotFoundError(f"Usual shuttle {preference.usual_shuttle_id} not found.")
        return shuttle

    def _recent_rides(self, user_id: int, route_id: int, today: date) -> list[Booking]:
        return self.booking_repository.get_rides(
            user_id=user_id,
            route_id=route_id,
            start=today - LOOKBACK,
            end=today,
        )

    def _habit(
        self,
        weekday: int,
        preference: Preference,
        saved: Shuttle,
        rides: list[Booking],
    ) -> Habit:
        on_weekday = [ride for ride in rides if ride.booking_date.weekday() == weekday]
        regular = len(on_weekday) >= MIN_RIDES

        if preference.usual_pinned:
            return Habit(weekday, saved, HabitSource.PINNED, regular=regular)

        sample = on_weekday[:WEEKDAY_SAMPLE]
        if found := _winner(sample):
            return Habit(weekday, found[0], HabitSource.WEEKDAY, found[1], len(sample), regular)

        sample = rides[:OVERALL_SAMPLE]
        if found := _winner(sample):
            return Habit(weekday, found[0], HabitSource.OVERALL, found[1], len(sample), regular)

        return Habit(weekday, saved, HabitSource.DEFAULT, regular=regular)

    def usual_for(self, user_id: int, booking_date: date, today: date | None = None) -> Habit:
        """The usual shuttle for this date's weekday, and why."""

        preference = self._preference(user_id)
        saved = self.saved_shuttle(user_id)
        rides = self._recent_rides(user_id, saved.route_id, today or clock.today())
        return self._habit(booking_date.weekday(), preference, saved, rides)

    def week(self, user_id: int, today: date | None = None) -> list[Habit]:
        """The usual shuttle for each service weekday, Monday first."""

        preference = self._preference(user_id)
        saved = self.saved_shuttle(user_id)
        rides = self._recent_rides(user_id, saved.route_id, today or clock.today())
        return [self._habit(weekday, preference, saved, rides) for weekday in SERVICE_WEEKDAYS]

    def pin(self, user_id: int, shuttle_id: int | None) -> None:
        """Pin a shuttle as the usual (it then always wins), or unpin with
        None so learning takes over again."""

        preference = self._preference(user_id)
        if shuttle_id is None:
            preference.usual_pinned = False
            self.db.commit()
            return

        shuttle = self.shuttle_repository.get_by_id(shuttle_id)
        if shuttle is None:
            raise NotFoundError(f"Shuttle {shuttle_id} not found.")
        if shuttle.route_id != self.saved_shuttle(user_id).route_id:
            raise ShuttleUnavailableError("That shuttle runs on a different route.")

        preference.usual_shuttle_id = shuttle.id
        preference.usual_pinned = True
        self.db.commit()
