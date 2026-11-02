"""Live trip status for a booking: phase, ETAs and shuttle position.

A trip runs on a timeline measured in minutes from the scheduled
departure (t = 0):

    t < -15          scheduled    shuttle still at the depot
    -15 <= t < d     approaching  driving from the depot to the pickup stop
    d <= t < d + 2   boarding     at the pickup stop
    d + 2 <= t < T+d in_transit   pickup stop -> destination
    t >= T + d       arrived

where d is the delay and T the scheduled trip length. t comes from the real
clock, or from a TripSimulation that replays the trip now (for demos).
ETAs are returned as real wall-clock times, so a client can count down
without polling even when the simulation runs faster than real time.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import ceil

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.models.booking import Booking
from app.models.trip_simulation import TripSimulation
from app.services.booking_service import BookingService
from app.services.route_geometry import Point, RouteGeometry, geometry_for, point_along


APPROACH_MINUTES = 15
BOARDING_MINUTES = 2


class TripPhase(StrEnum):
    SCHEDULED = "scheduled"
    APPROACHING = "approaching"
    BOARDING = "boarding"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"


@dataclass(frozen=True)
class TripStatus:
    booking: Booking
    phase: TripPhase
    message: str
    delay_minutes: int
    minutes_to_pickup: int | None
    minutes_to_arrival: int | None
    pickup_eta: datetime
    arrival_eta: datetime
    progress: float
    position: Point
    geometry: RouteGeometry
    simulated: bool


def _minutes(value: float) -> int:
    return max(0, ceil(value))


def _trip_length(booking: Booking) -> float:
    shuttle = booking.shuttle
    departure = datetime.combine(booking.booking_date, shuttle.departure_time)
    arrival = datetime.combine(booking.booking_date, shuttle.arrival_time)
    return (arrival - departure).total_seconds() / 60


def compute_status(
    booking: Booking,
    simulation: TripSimulation | None,
    now: datetime,
) -> TripStatus:
    shuttle = booking.shuttle
    route = shuttle.route
    geometry = geometry_for(route.pickup_location)
    departure = datetime.combine(booking.booking_date, shuttle.departure_time)
    trip = _trip_length(booking)

    if simulation is not None:
        elapsed = (now - simulation.started_at).total_seconds() / 60
        t = simulation.start_minutes + elapsed * simulation.speed
        speed = simulation.speed
        delay = simulation.delay_minutes
    else:
        t = (now - departure).total_seconds() / 60
        speed = 1.0
        delay = 0

    pickup_at = delay
    boarded_at = delay + BOARDING_MINUTES
    arrives_at = trip + delay

    # Convert simulated minutes-from-now into real wall-clock ETAs.
    pickup_eta = now + timedelta(minutes=(pickup_at - t) / speed)
    arrival_eta = now + timedelta(minutes=(arrives_at - t) / speed)

    to_pickup = _minutes(pickup_at - t)
    to_arrival = _minutes(arrives_at - t)
    stop, destination = route.pickup_location, route.dropoff_location
    late = f", running {delay} minutes late" if delay > 0 else ""

    if t < -APPROACH_MINUTES:
        phase = TripPhase.SCHEDULED
        position = geometry.depot
        when = (
            f"in {to_pickup} minutes"
            if booking.booking_date == now.date() and to_pickup <= 120
            else f"on {booking.booking_date:%A, %B %-d} at {shuttle.departure_time:%-I:%M %p}"
        )
        message = f"Your shuttle from {stop} leaves {when}{late}."
    elif t < pickup_at:
        phase = TripPhase.APPROACHING
        position = point_along(
            [geometry.depot, geometry.pickup],
            (t + APPROACH_MINUTES) / (pickup_at + APPROACH_MINUTES),
        )
        minutes = "1 minute" if to_pickup == 1 else f"{to_pickup} minutes"
        message = f"Your shuttle is {minutes} from {stop}{late}."
    elif t < boarded_at:
        phase = TripPhase.BOARDING
        position = geometry.pickup
        message = f"Your shuttle is at {stop} now."
    elif t < arrives_at:
        phase = TripPhase.IN_TRANSIT
        position = point_along(geometry.path, (t - boarded_at) / (arrives_at - boarded_at))
        message = f"On the way. Arriving at {destination} in {to_arrival} minutes."
    else:
        phase = TripPhase.ARRIVED
        position = geometry.destination
        message = f"Arrived at {destination}."

    window = arrives_at + APPROACH_MINUTES
    progress = min(max((t + APPROACH_MINUTES) / window, 0.0), 1.0)

    return TripStatus(
        booking=booking,
        phase=phase,
        message=message,
        delay_minutes=delay,
        minutes_to_pickup=to_pickup if phase in (TripPhase.SCHEDULED, TripPhase.APPROACHING) else None,
        minutes_to_arrival=to_arrival if phase is not TripPhase.ARRIVED else None,
        pickup_eta=pickup_eta,
        arrival_eta=arrival_eta,
        progress=round(progress, 4),
        position=position,
        geometry=geometry,
        simulated=simulation is not None,
    )


class TrackingService:
    def __init__(self, db: Session, booking_service: BookingService):
        self.db = db
        self.booking_service = booking_service

    def _simulation(self, booking_id: int) -> TripSimulation | None:
        return self.db.get(TripSimulation, booking_id)

    def status(self, user_id: int, booking_id: int) -> TripStatus:
        booking = self.booking_service.get_booking(user_id, booking_id)
        return compute_status(booking, self._simulation(booking.id), clock.now())

    def next_trip_status(self, user_id: int) -> TripStatus | None:
        """The trip the user most likely means by "my shuttle": a trip
        being simulated, else the next upcoming booking."""

        bookings = self.booking_service.get_upcoming_bookings(user_id)
        simulated = self.db.scalars(
            select(TripSimulation.booking_id).where(
                TripSimulation.booking_id.in_([b.id for b in bookings])
            )
        ).first()

        if simulated is not None:
            return self.status(user_id, simulated)

        now = clock.now()
        for booking in bookings:
            status = compute_status(booking, None, now)
            if status.phase is not TripPhase.ARRIVED:
                return status

        return None

    def start_simulation(
        self,
        user_id: int,
        booking_id: int,
        start_minutes: float = -12,
        speed: float = 1.0,
    ) -> TripStatus:
        booking = self.booking_service.get_booking(user_id, booking_id)
        simulation = self._simulation(booking.id) or TripSimulation(booking_id=booking.id)
        simulation.started_at = clock.now()
        simulation.start_minutes = start_minutes
        simulation.speed = speed
        simulation.delay_minutes = 0
        self.db.add(simulation)
        self.db.commit()

        return self.status(user_id, booking_id)

    def set_delay(self, user_id: int, booking_id: int, minutes: int) -> TripStatus:
        booking = self.booking_service.get_booking(user_id, booking_id)
        simulation = self._simulation(booking.id)

        if simulation is None:
            simulation = TripSimulation(
                booking_id=booking.id,
                started_at=clock.now(),
                start_minutes=(clock.now() - datetime.combine(
                    booking.booking_date, booking.shuttle.departure_time
                )).total_seconds() / 60,
                speed=1.0,
            )
            self.db.add(simulation)

        simulation.delay_minutes = minutes
        self.db.commit()

        return self.status(user_id, booking_id)

    def stop_simulation(self, user_id: int, booking_id: int) -> None:
        booking = self.booking_service.get_booking(user_id, booking_id)
        simulation = self._simulation(booking.id)

        if simulation is not None:
            self.db.delete(simulation)
            self.db.commit()
