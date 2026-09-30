from datetime import date
from typing import TypedDict


class BookingState(TypedDict, total=False):
    user_id: int
    booking_date: date
    booking_id: int | None
    response: str | None
    error: str | None
