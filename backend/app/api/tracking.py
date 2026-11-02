from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.tracking import (
    AlternativeResponse,
    Coordinate,
    DelayRequest,
    LocationRequest,
    MoveBookingRequest,
    StartSimulationRequest,
    TripStatusResponse,
)
from app.services.booking_service import BookingService
from app.services.errors import BookingError, NotFoundError
from app.services.tracking_service import TrackingService, TripStatus


router = APIRouter(tags=["tracking"])


def create_tracking_service(db: Session) -> TrackingService:
    return TrackingService(
        db,
        BookingService(
            db=db,
            user_repository=UserRepository(db),
            preference_repository=PreferenceRepository(db),
            shuttle_repository=ShuttleRepository(db),
            booking_repository=BookingRepository(db),
        ),
    )


def _coordinate(point: tuple[float, float]) -> Coordinate:
    return Coordinate(latitude=point[0], longitude=point[1])


def to_response(status: TripStatus) -> TripStatusResponse:
    route = status.booking.shuttle.route

    return TripStatusResponse(
        booking_id=status.booking.id,
        booking_date=status.booking.booking_date.isoformat(),
        shuttle_name=status.booking.shuttle.name,
        phase=status.phase.value,
        message=status.message,
        delay_minutes=status.delay_minutes,
        minutes_to_pickup=status.minutes_to_pickup,
        minutes_to_arrival=status.minutes_to_arrival,
        # The clock is naive local time; attach the local UTC offset. Whole
        # seconds, because Swift's .iso8601 decoding rejects fractions.
        pickup_eta=status.pickup_eta.replace(microsecond=0).astimezone(),
        arrival_eta=status.arrival_eta.replace(microsecond=0).astimezone(),
        progress=status.progress,
        position=_coordinate(status.position),
        pickup=_coordinate(status.geometry.pickup),
        destination=_coordinate(status.geometry.destination),
        pickup_name=route.pickup_location,
        destination_name=route.dropoff_location,
        route=[_coordinate(p) for p in status.geometry.path],
        simulated=status.simulated,
        walk_minutes=status.walk_minutes,
        leave_in_minutes=status.leave_in_minutes,
        alternative=(
            AlternativeResponse(
                shuttle_id=status.alternative.shuttle.id,
                shuttle_name=status.alternative.shuttle.name,
                departure=f"{status.alternative.shuttle.departure_time:%H:%M}",
                arrival=f"{status.alternative.shuttle.arrival_time:%H:%M}",
                minutes_earlier=status.alternative.minutes_earlier,
            )
            if status.alternative
            else None
        ),
    )


def _not_found_or_conflict(error: BookingError):
    status_code = 404 if isinstance(error, NotFoundError) else 409
    raise HTTPException(status_code=status_code, detail=str(error))


@router.get("/tracking/next", response_model=TripStatusResponse)
def next_trip(
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
):
    try:
        status = create_tracking_service(db).next_trip_status(user_id)
    except BookingError as e:
        _not_found_or_conflict(e)

    if status is None:
        raise HTTPException(status_code=404, detail="You don't have an upcoming shuttle booked.")

    return to_response(status)


@router.get("/bookings/{booking_id}/tracking", response_model=TripStatusResponse)
def booking_tracking(
    booking_id: int,
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
):
    try:
        return to_response(create_tracking_service(db).status(user_id, booking_id))
    except BookingError as e:
        _not_found_or_conflict(e)


@router.post("/users/{user_id}/location", status_code=204)
def update_location(
    user_id: int,
    request: LocationRequest,
    db: Session = Depends(get_db),
):
    """Latest rider location while trip mode runs, for walking estimates."""

    create_tracking_service(db).update_location(user_id, request.latitude, request.longitude)


@router.post("/bookings/{booking_id}/move", response_model=TripStatusResponse)
def move_booking(
    booking_id: int,
    request: MoveBookingRequest,
    db: Session = Depends(get_db),
):
    """Move a booking to a specific shuttle, e.g. the faster alternative
    offered when a shuttle is late. Returns the updated trip status."""

    try:
        status = create_tracking_service(db).move_booking(
            request.user_id,
            booking_id,
            request.shuttle_id,
        )
    except BookingError as e:
        _not_found_or_conflict(e)

    return to_response(status)


@router.post("/simulator/trips/{booking_id}", response_model=TripStatusResponse)
def start_simulation(
    booking_id: int,
    request: StartSimulationRequest,
    db: Session = Depends(get_db),
):
    """Replay a booking's trip now, for demos and testing."""

    try:
        status = create_tracking_service(db).start_simulation(
            request.user_id,
            booking_id,
            start_minutes=request.start_minutes,
            speed=request.speed,
        )
    except BookingError as e:
        _not_found_or_conflict(e)

    return to_response(status)


@router.post("/simulator/trips/{booking_id}/delay", response_model=TripStatusResponse)
def set_delay(
    booking_id: int,
    request: DelayRequest,
    db: Session = Depends(get_db),
):
    try:
        status = create_tracking_service(db).set_delay(
            request.user_id,
            booking_id,
            request.minutes,
        )
    except BookingError as e:
        _not_found_or_conflict(e)

    return to_response(status)


@router.delete("/simulator/trips/{booking_id}", status_code=204)
def stop_simulation(
    booking_id: int,
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
):
    try:
        create_tracking_service(db).stop_simulation(user_id, booking_id)
    except BookingError as e:
        _not_found_or_conflict(e)
