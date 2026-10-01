from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agent.factory import create_llm
from app.agent.llm import LLM
from app.db.database import get_db
from app.graph.booking_graph import create_booking_graph
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.booking import (
    BookingDetailResponse,
    BookingRequest,
    BookingResponse,
)
from app.services.booking_service import BookingService


router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
)


def get_llm() -> LLM:
    return create_llm(reference_date=date.today())


@router.get("", response_model=list[BookingDetailResponse])
def get_upcoming_bookings(
    user_id: int = Query(default=1, gt=0),
    from_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = BookingService(
        db=db,
        user_repository=UserRepository(db),
        preference_repository=PreferenceRepository(db),
        shuttle_repository=ShuttleRepository(db),
        booking_repository=BookingRepository(db),
    )

    try:
        bookings = service.get_upcoming_bookings(
            user_id=user_id,
            from_date=from_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return [
        BookingDetailResponse(
            id=booking.id,
            booking_date=booking.booking_date,
            pickup_time=booking.pickup_time,
            status=booking.status,
            child_name=booking.child.name if booking.child else "",
            shuttle_name=booking.shuttle.name if booking.shuttle else "",
            route_name=booking.shuttle.route.name if booking.shuttle and booking.shuttle.route else "",
            pickup_location=booking.shuttle.route.pickup_location if booking.shuttle and booking.shuttle.route else None,
            destination=booking.shuttle.route.dropoff_location if booking.shuttle and booking.shuttle.route else None,
        )
        for booking in bookings
    ]


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

    result = graph.invoke(
        {
            "user_id": request.user_id,
            "user_input": request.message,
        }
    )

    return BookingResponse(
        booking_id=result["booking_id"],
        message=result["response"],
    )
