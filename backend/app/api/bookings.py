from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agent.factory import create_llm
from app.agent.llm import LLM, LLMUnavailableError
from app.agent.schemas import AgentIntent
from app.core import clock
from app.db.database import get_db
from app.graph.booking_graph import create_booking_graph, describe_booking, habit_note
from app.models.booking import Booking
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.booking import (
    BookingDetailResponse,
    BookingRequest,
    BookingResponse,
    RescheduleRequest,
    UserRequest,
)
from app.services.booking_service import BookingService
from app.services.errors import BookingError, NotFoundError


router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
)


def get_llm() -> LLM:
    return create_llm(reference_date=clock.today())


def _create_service(db: Session) -> BookingService:
    return BookingService(
        db=db,
        user_repository=UserRepository(db),
        preference_repository=PreferenceRepository(db),
        shuttle_repository=ShuttleRepository(db),
        booking_repository=BookingRepository(db),
    )


def _raise_http(error: Exception):
    # `detail` is short, user-facing text; Siri reads it aloud.
    if isinstance(error, NotFoundError):
        raise HTTPException(status_code=404, detail=str(error))

    if isinstance(error, BookingError):
        raise HTTPException(status_code=409, detail=str(error))

    if isinstance(error, LLMUnavailableError):
        raise HTTPException(
            status_code=503,
            detail=(
                "I couldn't understand that request right now. "
                "Try \"Book my usual shuttle with Clear Path\"."
            ),
        )

    raise error


def _to_detail(
    booking: Booking,
    service: BookingService | None = None,
) -> BookingDetailResponse:
    shuttle = booking.shuttle
    route = shuttle.route if shuttle else None
    detail = BookingDetailResponse(
        id=booking.id,
        booking_date=booking.booking_date,
        pickup_time=booking.pickup_time,
        arrival_time=shuttle.arrival_time if shuttle else None,
        status=booking.status,
        shuttle_name=shuttle.name if shuttle else "",
        route_name=route.name if route else "",
        pickup_location=route.pickup_location if route else None,
        destination=route.dropoff_location if route else None,
    )

    if service is not None:
        adjacent = service.get_adjacent_shuttles(booking)
        detail.earlier_available = adjacent.earlier is not None
        detail.later_available = adjacent.later is not None

    return detail


@router.get("", response_model=list[BookingDetailResponse])
def get_upcoming_bookings(
    user_id: int = Query(default=1, gt=0),
    from_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = _create_service(db)

    try:
        bookings = service.get_upcoming_bookings(
            user_id=user_id,
            from_date=from_date,
        )
    except BookingError as e:
        _raise_http(e)

    return [_to_detail(booking) for booking in bookings]


@router.get("/{booking_id}", response_model=BookingDetailResponse)
def get_booking(
    booking_id: int,
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
):
    service = _create_service(db)

    try:
        booking = service.get_booking(user_id, booking_id)
    except BookingError as e:
        _raise_http(e)

    return _to_detail(booking, service)


@router.post("", response_model=BookingResponse)
def create_booking(
    request: BookingRequest,
    db: Session = Depends(get_db),
    llm: LLM = Depends(get_llm),
):
    graph = create_booking_graph(
        db=db,
        llm=llm,
    )

    state = {"user_id": request.user_id}

    if request.booking_date is not None:
        state["intent"] = AgentIntent.BOOK_USUAL_SHUTTLE
        state["booking_date"] = request.booking_date
    else:
        state["user_input"] = request.message

    try:
        result = graph.invoke(state)
    except (BookingError, LLMUnavailableError) as e:
        _raise_http(e)

    return BookingResponse(
        booking_id=result["booking_id"],
        message=result["response"],
        already_booked=result["already_booked"],
        booking=_to_detail(result["booking"], _create_service(db)),
        usual_reason=(
            None if result["already_booked"] else habit_note(result.get("habit"))
        ),
    )


@router.post("/{booking_id}/reschedule", response_model=BookingResponse)
def reschedule_booking(
    booking_id: int,
    request: RescheduleRequest,
    db: Session = Depends(get_db),
):
    service = _create_service(db)

    try:
        booking = service.reschedule_booking(
            user_id=request.user_id,
            booking_id=booking_id,
            direction=request.direction,
        )
    except BookingError as e:
        _raise_http(e)

    return BookingResponse(
        booking_id=booking.id,
        message=f"Done. You're now on {describe_booking(booking)}.",
        booking=_to_detail(booking, service),
    )


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    request: UserRequest,
    db: Session = Depends(get_db),
):
    """Structured cancel (no LLM), e.g. for the app's on-device assistant."""

    service = _create_service(db)

    try:
        booking = service.cancel_booking(user_id=request.user_id, booking_id=booking_id)
    except BookingError as e:
        _raise_http(e)

    return BookingResponse(
        booking_id=booking.id,
        message=f"Done. I cancelled {describe_booking(booking)}.",
        booking=_to_detail(booking),
    )
