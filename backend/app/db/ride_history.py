"""Past rides for demos, tests and evals, so habits have something to
learn from. Inserted directly: booking rules don't apply to the past.

The demo rider's pattern over the six weeks before the current week:

  Monday     the 7:15 (early stand-up), on 4 of the last 5
  Tuesday    the 7:30, every week
  Wednesday  works from home; one ride in six weeks
  Thursday   the 8:00 (later start), on 4 of the last 5
  Friday     the 7:30, five of six weeks

Wednesday and Friday stay on the 7:30 on purpose: they are "tomorrow" on
the Tuesday/Thursday demo days, and the delay demo needs the 7:30 (its
faster alternative is the 7:45).
"""

from datetime import date, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.shuttle import Shuttle


# weeks ago (1 = last week) -> departure, per weekday (0 = Monday).
DEMO_PATTERN: dict[int, dict[int, time]] = {
    0: {1: time(7, 15), 2: time(7, 15), 3: time(7, 30), 4: time(7, 15), 5: time(7, 15), 6: time(7, 30)},
    1: {week: time(7, 30) for week in range(1, 7)},
    2: {3: time(7, 30)},
    3: {1: time(8, 0), 2: time(8, 0), 3: time(7, 30), 4: time(8, 0), 5: time(8, 0), 6: time(7, 30)},
    4: {1: time(7, 30), 2: time(7, 30), 3: time(7, 30), 5: time(7, 30), 6: time(7, 30)},
}


def demo_rides(today: date) -> list[tuple[date, time]]:
    """(date, departure) for every ride in DEMO_PATTERN, before this week."""

    this_monday = today - timedelta(days=today.weekday())
    return sorted(
        (this_monday - timedelta(weeks=weeks_ago) + timedelta(days=weekday), departure)
        for weekday, weeks in DEMO_PATTERN.items()
        for weeks_ago, departure in weeks.items()
    )


def add_past_rides(
    db: Session,
    user_id: int,
    rides: list[tuple[date, time]],
) -> int:
    """Insert confirmed bookings on the morning route; returns the count."""

    by_departure = {
        shuttle.departure_time: shuttle
        for shuttle in db.scalars(select(Shuttle).where(Shuttle.name.like("Morning%")))
    }
    db.add_all(
        Booking(
            user_id=user_id,
            shuttle_id=by_departure[departure].id,
            booking_date=ride_date,
            pickup_time=departure,
            status="confirmed",
        )
        for ride_date, departure in rides
    )
    db.commit()
    return len(rides)
