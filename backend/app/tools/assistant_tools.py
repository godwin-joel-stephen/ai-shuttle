"""Tools the assistant agent may call.

Each tool is bound to one user, so the model can never act on another
user's data, and returns structured results the model must ground its
reply in. Booking failures come back as `{"error": ...}` so the agent can
explain them instead of the request crashing.
"""

import threading
from datetime import date, datetime, timedelta
from functools import wraps

from langchain_core.tools import BaseTool, tool
from sqlalchemy.orm import Session

from app.core import clock
from app.models.booking import Booking
from app.models.shuttle import Shuttle
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.rag.embeddings import Embedder
from app.rag.retriever import search_knowledge
from app.services.booking_service import BookingService
from app.services.errors import BookingError
from app.services.tracking_service import TrackingService


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


def shuttle_to_dict(shuttle: Shuttle, bookable: bool) -> dict:
    return {
        "shuttle_id": shuttle.id,
        "shuttle_name": shuttle.name,
        "departure": f"{shuttle.departure_time:%H:%M}",
        "arrival": f"{shuttle.arrival_time:%H:%M}",
        "bookable": bookable,
    }


def scheduled(time_of_day, delay_minutes: int) -> datetime:
    return datetime.combine(date.min, time_of_day) + timedelta(minutes=delay_minutes)


def _report_booking_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BookingError as e:
            return {"error": str(e)}

    return wrapper


def _one_at_a_time(func, lock: threading.Lock):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with lock:
            return func(*args, **kwargs)

    return wrapper


def create_assistant_tools(
    db: Session,
    user_id: int,
    embedder: Embedder,
) -> list[BaseTool]:
    service = BookingService(
        db=db,
        user_repository=UserRepository(db),
        preference_repository=PreferenceRepository(db),
        shuttle_repository=ShuttleRepository(db),
        booking_repository=BookingRepository(db),
    )
    tracking = TrackingService(db, service)

    @tool
    @_report_booking_errors
    def get_my_bookings() -> dict:
        """List the user's upcoming confirmed shuttle bookings."""

        bookings = service.get_upcoming_bookings(user_id)
        return {"bookings": [booking_to_dict(b) for b in bookings]}

    @tool
    @_report_booking_errors
    def list_shuttle_options(booking_date: date) -> dict:
        """List every shuttle on the user's usual route for a date
        (YYYY-MM-DD), with departure/arrival times and whether each can
        still be booked. Use this to find an earlier, later or
        specific-time shuttle."""

        options = service.list_usual_route_shuttles(user_id, booking_date)
        return {
            "date": booking_date.isoformat(),
            "shuttles": [shuttle_to_dict(s, ok) for s, ok in options],
        }

    @tool
    @_report_booking_errors
    def book_usual_shuttle(booking_date: date) -> dict:
        """Book the user's usual shuttle for a date (YYYY-MM-DD). Returns
        the existing booking with already_booked=true instead of booking
        twice."""

        outcome = service.book_usual_shuttle(user_id, booking_date)
        return {
            "already_booked": outcome.already_booked,
            "booking": booking_to_dict(outcome.booking),
        }

    @tool
    @_report_booking_errors
    def change_booking_shuttle(booking_id: int, shuttle_id: int) -> dict:
        """Move an existing booking to another shuttle on the same route and
        date. Get shuttle_id values from list_shuttle_options."""

        status = tracking.move_booking(user_id, booking_id, shuttle_id)
        return {"booking": booking_to_dict(status.booking)}

    @tool
    @_report_booking_errors
    def cancel_booking(booking_id: int) -> dict:
        """Cancel a booking. Only call this when the user explicitly asks to
        cancel."""

        booking = service.cancel_booking(user_id, booking_id)
        return {"booking": booking_to_dict(booking)}

    @tool
    @_report_booking_errors
    def get_shuttle_status(booking_id: int | None = None) -> dict:
        """Live status of a booked trip: phase (scheduled, approaching,
        boarding, in_transit, arrived), minutes until pickup and arrival,
        delay, and pickup/arrival times. Omit booking_id for the user's
        next trip. Use for "where's my shuttle" and "should I leave now"."""

        status = (
            tracking.status(user_id, booking_id)
            if booking_id is not None
            else tracking.next_trip_status(user_id)
        )
        if status is None:
            return {"error": "You don't have an upcoming shuttle booked."}

        return {
            "booking_id": status.booking.id,
            "date": status.booking.booking_date.isoformat(),
            "phase": status.phase.value,
            "summary": status.message,
            "delay_minutes": status.delay_minutes,
            "minutes_to_pickup": status.minutes_to_pickup,
            "minutes_to_arrival": status.minutes_to_arrival,
            # On the trip's own schedule (departure plus delay), which also
            # reads correctly for a simulated trip replayed at another time.
            "pickup_time": f"{scheduled(status.booking.shuttle.departure_time, status.delay_minutes):%-I:%M %p}",
            "arrival_time": f"{scheduled(status.booking.shuttle.arrival_time, status.delay_minutes):%-I:%M %p}",
            "pickup_stop": status.booking.shuttle.route.pickup_location,
            "pickup_coordinates": {
                "latitude": status.geometry.pickup[0],
                "longitude": status.geometry.pickup[1],
            },
            "walk_minutes": status.walk_minutes,
            "leave_in_minutes": status.leave_in_minutes,
            "faster_alternative": (
                {
                    "shuttle_id": status.alternative.shuttle.id,
                    "departure": f"{status.alternative.shuttle.departure_time:%H:%M}",
                    "arrival": f"{status.alternative.shuttle.arrival_time:%H:%M}",
                    "minutes_earlier": status.alternative.minutes_earlier,
                }
                if status.alternative
                else None
            ),
        }

    @tool
    @_report_booking_errors
    def check_booking_eligibility(booking_date: date) -> dict:
        """Check whether the user's usual shuttle can be booked on a date
        (YYYY-MM-DD) without booking it. Returns the exact rule that
        blocks it (reason_code and message). Use this to answer "why can't
        I book" questions."""

        result = service.check_eligibility(user_id, booking_date)
        return {
            "date": booking_date.isoformat(),
            "weekday": f"{booking_date:%A}",
            "eligible": result.eligible,
            "already_booked": result.already_booked,
            "reason_code": result.error.code if result.error else None,
            "message": str(result.error) if result.error else None,
        }

    @tool
    def search_policies(query: str) -> dict:
        """Search Clear Path's policy documents (booking rules, cancellation,
        pickup rules, FAQ). Use specific wording, e.g. the rule message
        from check_booking_eligibility. Returns the best-matching sections;
        an empty list means the policies don't cover the question."""

        passages = search_knowledge(db, embedder, query)
        return {
            "passages": [
                {
                    "source": f"{p.title} › {p.heading}",
                    "text": p.content,
                    "similarity": p.similarity,
                    "citable": p.citable,
                }
                for p in passages
            ]
        }

    tools = [
        get_my_bookings,
        list_shuttle_options,
        book_usual_shuttle,
        change_booking_shuttle,
        cancel_booking,
        get_shuttle_status,
        check_booking_eligibility,
        search_policies,
    ]

    # LangGraph runs tool calls from one model turn in parallel threads,
    # but these tools share one database session, which isn't thread-safe
    # ("session is in 'prepared' state"). Run them one at a time.
    lock = threading.Lock()
    for t in tools:
        t.func = _one_at_a_time(t.func, lock)

    return tools
