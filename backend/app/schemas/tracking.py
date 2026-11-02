from datetime import datetime

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    latitude: float
    longitude: float


class TripStatusResponse(BaseModel):
    booking_id: int
    booking_date: str
    shuttle_name: str
    phase: str
    message: str
    delay_minutes: int
    minutes_to_pickup: int | None
    minutes_to_arrival: int | None
    # Wall-clock times with UTC offset; clients count down to these.
    pickup_eta: datetime
    arrival_eta: datetime
    progress: float
    position: Coordinate
    pickup: Coordinate
    destination: Coordinate
    pickup_name: str
    destination_name: str
    route: list[Coordinate]
    simulated: bool


class StartSimulationRequest(BaseModel):
    user_id: int = Field(default=1, gt=0)
    # Where on the trip's timeline to start, in minutes from departure:
    # -12 starts with the shuttle on its way to the pickup stop.
    start_minutes: float = Field(default=-12, ge=-120, le=120)
    speed: float = Field(default=1.0, gt=0, le=60)


class DelayRequest(BaseModel):
    user_id: int = Field(default=1, gt=0)
    minutes: int = Field(ge=0, le=120)
