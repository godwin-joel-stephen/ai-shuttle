from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        self.db.flush()

        return booking

    def get_by_id(self, booking_id: int) -> Booking | None:
        statement = select(Booking).where(
            Booking.id == booking_id
        )

        return self.db.scalar(statement)