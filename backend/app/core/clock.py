"""Single source of "now" so tests can pin the date and time.

Booking rules depend on the day of the week and time of day; without
this, tests would pass or fail depending on when they run.
"""

from datetime import date, datetime


def now() -> datetime:
    return datetime.now()


def today() -> date:
    return now().date()
