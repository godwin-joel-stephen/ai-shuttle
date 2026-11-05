"""Schedule import (F3): plan and apply booking changes for typed days.

No LLM here: the phone already turned the document into days on-device,
and mapping days to bookings is a rule, not a judgement.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.bookings import _create_service, _raise_http, _to_detail
from app.db.database import get_db
from app.repositories.booking_repository import BookingRepository
from app.schemas.schedule import (
    ScheduleApplyResponse,
    ScheduleDayOut,
    SchedulePlanResponse,
    ScheduleRequest,
)
from app.services.errors import BookingError
from app.services.schedule_service import (
    ACTIONABLE,
    PlannedDay,
    ScheduleDay,
    ScheduleService,
    summarize,
)


router = APIRouter(
    prefix="/schedule",
    tags=["schedule"],
)


def _create_schedule_service(db: Session) -> ScheduleService:
    return ScheduleService(
        booking_service=_create_service(db),
        booking_repository=BookingRepository(db),
    )


def _days(request: ScheduleRequest) -> list[ScheduleDay]:
    return [ScheduleDay(date=day.date, kind=day.kind) for day in request.days]


def _to_out(day: PlannedDay) -> ScheduleDayOut:
    return ScheduleDayOut(
        date=day.date,
        kind=day.kind,
        action=day.action,
        message=day.message,
        reason_code=day.reason_code,
        bookings=[_to_detail(booking) for booking in day.bookings],
        succeeded=day.succeeded,
    )


@router.post("/plan", response_model=SchedulePlanResponse)
def plan_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db),
):
    service = _create_schedule_service(db)

    try:
        planned = service.plan(request.user_id, _days(request))
    except BookingError as e:
        _raise_http(e)

    return SchedulePlanResponse(
        days=[_to_out(day) for day in planned],
        summary=summarize(planned),
        changes=sum(1 for day in planned if day.action in ACTIONABLE),
    )


@router.post("/apply", response_model=ScheduleApplyResponse)
def apply_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db),
):
    """Apply the days the user approved. Re-plans first, so a day that
    changed since the review (e.g. booked from Siri) isn't done twice."""

    service = _create_schedule_service(db)

    try:
        applied = service.apply(request.user_id, _days(request))
    except BookingError as e:
        _raise_http(e)

    return ScheduleApplyResponse(
        days=[_to_out(day) for day in applied],
        summary=summarize(applied, applied=True),
        bookings_changed=any(day.succeeded for day in applied),
    )
