from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class BookingRequest(BaseModel):
    user_id: int = Field(gt=0)
    message: str = Field(min_length=1)


class BookingResponse(BaseModel):
    booking_id: int
    message: str


class BookingDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_date: date
    pickup_time: time
    status: str
    child_name: str
    shuttle_name: str
    route_name: str
    pickup_location: str | None = None
    destination: str | None = None
