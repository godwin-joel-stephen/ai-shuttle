from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.booking_service import RescheduleDirection


class BookingRequest(BaseModel):
    """Either natural language (`message`) or an already-structured date.

    Structured requests come from callers such as the Siri App Intent and
    skip LLM interpretation.
    """

    user_id: int = Field(gt=0)
    message: str | None = Field(default=None, min_length=1)
    booking_date: date | None = None

    @model_validator(mode="after")
    def require_message_or_date(self):
        if self.message is None and self.booking_date is None:
            raise ValueError("Either message or booking_date is required.")

        return self


class RescheduleRequest(BaseModel):
    user_id: int = Field(gt=0)
    direction: RescheduleDirection


class BookingDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_date: date
    pickup_time: time
    arrival_time: time | None = None
    status: str
    shuttle_name: str
    route_name: str
    pickup_location: str | None = None
    destination: str | None = None
    earlier_available: bool | None = None
    later_available: bool | None = None


class BookingResponse(BaseModel):
    booking_id: int
    message: str
    already_booked: bool = False
    booking: BookingDetailResponse | None = None
