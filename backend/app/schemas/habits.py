from datetime import date, time

from pydantic import BaseModel, Field

from app.services.habit_service import HabitSource


class HabitDayResponse(BaseModel):
    weekday: str
    shuttle_id: int
    departure: time
    arrival: time
    source: HabitSource
    reason: str
    rides: int
    sample: int
    # Rides this weekday often enough that a missing booking deserves a
    # reminder.
    regular: bool


class UpcomingDayResponse(BaseModel):
    date: date
    weekday: str
    booked: bool
    booked_departure: time | None = None
    habit: HabitDayResponse


class HabitsResponse(BaseModel):
    pinned_shuttle_id: int | None
    days: list[HabitDayResponse]
    # The next service days (tomorrow onward, one week), for reminders.
    upcoming: list[UpcomingDayResponse]


class PinRequest(BaseModel):
    user_id: int = Field(gt=0)
    # None unpins, so the learned habit takes over again.
    shuttle_id: int | None = None
