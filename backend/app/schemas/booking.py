from pydantic import BaseModel, Field


class BookingRequest(BaseModel):
    user_id: int = Field(gt=0)
    message: str = Field(min_length=1)


class BookingResponse(BaseModel):
    booking_id: int
    message: str
