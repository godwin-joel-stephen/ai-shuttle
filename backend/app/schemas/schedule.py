from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.schemas.booking import BookingDetailResponse
from app.services.schedule_service import PlanAction, WorkdayKind


# A schedule covers days, not months; the booking window is 14 days.
MAX_SCHEDULE_DAYS = 31


class ScheduleDayIn(BaseModel):
    date: date
    kind: WorkdayKind


class ScheduleRequest(BaseModel):
    """Typed days only: the phone reads the document on-device and never
    sends its text, so nothing in a document can instruct a model here."""

    user_id: int = Field(gt=0)
    days: list[ScheduleDayIn] = Field(min_length=1, max_length=MAX_SCHEDULE_DAYS)

    @field_validator("days")
    @classmethod
    def unique_dates(cls, days: list[ScheduleDayIn]) -> list[ScheduleDayIn]:
        dates = [day.date for day in days]
        if len(dates) != len(set(dates)):
            raise ValueError("Each date may appear only once.")
        return days


class ScheduleDayOut(BaseModel):
    date: date
    kind: WorkdayKind
    action: PlanAction
    message: str
    reason_code: str | None = None
    bookings: list[BookingDetailResponse] = []
    # Only set by /schedule/apply.
    succeeded: bool | None = None


class SchedulePlanResponse(BaseModel):
    days: list[ScheduleDayOut]
    summary: str
    changes: int


class ScheduleApplyResponse(BaseModel):
    days: list[ScheduleDayOut]
    summary: str
    bookings_changed: bool
