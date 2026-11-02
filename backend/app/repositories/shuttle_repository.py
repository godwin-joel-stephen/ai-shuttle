from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.shuttle import Shuttle


class ShuttleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, shuttle_id: int) -> Shuttle | None:
        statement = select(Shuttle).where(
            Shuttle.id == shuttle_id
        )

        return self.db.scalar(statement)

    def list_by_route(self, route_id: int) -> list[Shuttle]:
        statement = (
            select(Shuttle)
            .where(Shuttle.route_id == route_id)
            .order_by(Shuttle.departure_time.asc())
        )

        return list(self.db.scalars(statement).all())

    def has_available_seat(
        self,
        shuttle_id: int,
        booking_date: date,
    ) -> bool:
        shuttle = self.get_by_id(shuttle_id)

        if shuttle is None:
            return False

        booking_count = self.db.scalar(
            select(func.count(Booking.id)).where(
                Booking.shuttle_id == shuttle_id,
                Booking.booking_date == booking_date,
                Booking.status == "confirmed",
            )
        )

        return booking_count < shuttle.capacity