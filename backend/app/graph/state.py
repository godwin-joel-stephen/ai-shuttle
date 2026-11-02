from datetime import date
from typing import Any, TypedDict


class BookingState(TypedDict, total=False):
    user_id: int
    user_input: str
    intent: str | None
    booking_date: date
    booking_id: int | None
    booking: Any
    already_booked: bool
    response: str | None
    error: str | None
