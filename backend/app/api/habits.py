"""Commute habits (F10): the usual shuttle per weekday and why, plus the
next days the rider usually rides but hasn't booked, which the app turns
into local reminders and Siri suggestions."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core import clock
from app.db.database import get_db
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.schemas.habits import (
    HabitDayResponse,
    HabitsResponse,
    PinRequest,
    UpcomingDayResponse,
)
from app.services.booking_service import SERVICE_WEEKDAYS
from app.services.errors import BookingError, NotFoundError
from app.services.habit_service import Habit, HabitService


router = APIRouter(prefix="/habits", tags=["habits"])

UPCOMING_DAYS = 7


def _service(db: Session) -> HabitService:
    return HabitService(
        db,
        PreferenceRepository(db),
        ShuttleRepository(db),
        BookingRepository(db),
    )


def habit_to_response(habit: Habit) -> HabitDayResponse:
    return HabitDayResponse(
        weekday=habit.weekday_name,
        shuttle_id=habit.shuttle.id,
        departure=habit.shuttle.departure_time,
        arrival=habit.shuttle.arrival_time,
        source=habit.source,
        reason=habit.reason,
        rides=habit.rides,
        sample=habit.sample,
        regular=habit.regular,
    )


def build_habits(db: Session, user_id: int) -> HabitsResponse:
    service = _service(db)
    today = clock.today()
    week = service.week(user_id, today)
    route_id = service.saved_shuttle(user_id).route_id
    preference = service.preference_repository.get_by_user_id(user_id)

    upcoming = []
    for offset in range(1, UPCOMING_DAYS + 1):
        day = today + timedelta(days=offset)
        if day.weekday() not in SERVICE_WEEKDAYS:
            continue
        booking = service.booking_repository.get_confirmed_on_route(
            user_id=user_id, route_id=route_id, booking_date=day,
        )
        upcoming.append(UpcomingDayResponse(
            date=day,
            weekday=f"{day:%A}",
            booked=booking is not None,
            booked_departure=booking.pickup_time if booking else None,
            habit=habit_to_response(week[day.weekday()]),
        ))

    return HabitsResponse(
        pinned_shuttle_id=preference.usual_shuttle_id if preference.usual_pinned else None,
        days=[habit_to_response(habit) for habit in week],
        upcoming=upcoming,
    )


def _raise_http(error: BookingError):
    status = 404 if isinstance(error, NotFoundError) else 409
    raise HTTPException(status_code=status, detail=str(error))


@router.get("", response_model=HabitsResponse)
def get_habits(
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
):
    try:
        return build_habits(db, user_id)
    except BookingError as error:
        _raise_http(error)


@router.post("/pin", response_model=HabitsResponse)
def pin_usual(request: PinRequest, db: Session = Depends(get_db)):
    try:
        _service(db).pin(request.user_id, request.shuttle_id)
        return build_habits(db, request.user_id)
    except BookingError as error:
        _raise_http(error)
