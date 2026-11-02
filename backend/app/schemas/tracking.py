from datetime import datetime

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    latitude: float
    longitude: float


class AlternativeResponse(BaseModel):
    shuttle_id: int
    shuttle_name: str
    departure: str  # "07:45"
    arrival: str
    minutes_earlier: int


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
    # Present while the app shares the rider's location (trip mode).
    walk_minutes: int | None = None
    # Minutes until the rider should set off; 0 or less means now.
    leave_in_minutes: int | None = None
    # A faster departure when this one is running late.
    alternative: AlternativeResponse | None = None


class StartSimulationRequest(BaseModel):
    user_id: int = Field(default=1, gt=0)
    # Where on the trip's timeline to start, in minutes from departure:
    # -12 starts with the shuttle on its way to the pickup stop.
    start_minutes: float = Field(default=-12, ge=-120, le=120)
    speed: float = Field(default=1.0, gt=0, le=60)
    # Use this walk to the stop instead of the rider's GPS position.
    walk_minutes: int | None = Field(default=None, ge=0, le=60)


class DelayRequest(BaseModel):
    user_id: int = Field(default=1, gt=0)
    minutes: int = Field(ge=0, le=120)


class LocationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class MoveBookingRequest(BaseModel):
    user_id: int = Field(default=1, gt=0)
    shuttle_id: int = Field(gt=0)
