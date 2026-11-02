"""Tools the assistant agent may call.

Each tool is bound to one user, so the model can never act on another
user's data, and returns structured results the model must ground its
reply in. Booking failures come back as `{"error": ...}` so the agent can
explain them instead of the request crashing.
"""

from datetime import date
from functools import wraps

from langchain_core.tools import BaseTool, tool
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.shuttle import Shuttle
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.services.booking_service import BookingService
from app.services.errors import BookingError


# Tools that change bookings; the API reports when any of them succeeded.
MUTATING_TOOLS = frozenset({
    "book_usual_shuttle",
    "change_booking_shuttle",
    "cancel_booking",
})


def booking_to_dict(booking: Booking) -> dict:
    shuttle = booking.shuttle
    route = shuttle.route

    return {
        "booking_id": booking.id,
        "date": booking.booking_date.isoformat(),
        "weekday": f"{booking.booking_date:%A}",
        "status": booking.status,
        "shuttle_id": shuttle.id,
        "shuttle_name": shuttle.name,
        "departure": f"{shuttle.departure_time:%H:%M}",
        "arrival": f"{shuttle.arrival_time:%H:%M}",
        "from": route.pickup_location,
        "to": route.dropoff_location,
    }


def shuttle_to_dict(shuttle: Shuttle, seats_available: bool) -> dict:
    return {
        "shuttle_id": shuttle.id,
        "shuttle_name": shuttle.name,
        "departure": f"{shuttle.departure_time:%H:%M}",
        "arrival": f"{shuttle.arrival_time:%H:%M}",
        "seats_available": seats_available,
    }


def _report_booking_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BookingError as e:
            return {"error": str(e)}

    return wrapper


def create_assistant_tools(
    db: Session,
    user_id: int,
    today: date | None = None,
) -> list[BaseTool]:
    today = today or date.today()
    service = BookingService(
        db=db,
        user_repository=UserRepository(db),
        preference_repository=PreferenceRepository(db),
        shuttle_repository=ShuttleRepository(db),
        booking_repository=BookingRepository(db),
    )

    @tool
    @_report_booking_errors
    def get_my_bookings() -> dict:
        """List the user's upcoming confirmed shuttle bookings."""

        bookings = service.get_upcoming_bookings(user_id, from_date=today)
        return {"bookings": [booking_to_dict(b) for b in bookings]}

    @tool
    @_report_booking_errors
    def list_shuttle_options(booking_date: date) -> dict:
        """List every shuttle on the user's usual route for a date
        (YYYY-MM-DD), with departure/arrival times and seat availability.
        Use this to find an earlier, later or specific-time shuttle."""

        options = service.list_usual_route_shuttles(user_id, booking_date)
        return {
            "date": booking_date.isoformat(),
            "shuttles": [shuttle_to_dict(s, free) for s, free in options],
        }

    @tool
    @_report_booking_errors
    def book_usual_shuttle(booking_date: date) -> dict:
        """Book the user's usual shuttle for a date (YYYY-MM-DD). Returns
        the existing booking with already_booked=true instead of booking
        twice."""

        outcome = service.book_usual_shuttle(user_id, booking_date, today=today)
        return {
            "already_booked": outcome.already_booked,
            "booking": booking_to_dict(outcome.booking),
        }

    @tool
    @_report_booking_errors
    def change_booking_shuttle(booking_id: int, shuttle_id: int) -> dict:
        """Move an existing booking to another shuttle on the same route and
        date. Get shuttle_id values from list_shuttle_options."""

        booking = service.move_booking(user_id, booking_id, shuttle_id)
        return {"booking": booking_to_dict(booking)}

    @tool
    @_report_booking_errors
    def cancel_booking(booking_id: int) -> dict:
        """Cancel a booking. Only call this when the user explicitly asks to
        cancel."""

        booking = service.cancel_booking(user_id, booking_id)
        return {"booking": booking_to_dict(booking)}

    return [
        get_my_bookings,
        list_shuttle_options,
        book_usual_shuttle,
        change_booking_shuttle,
        cancel_booking,
    ]
