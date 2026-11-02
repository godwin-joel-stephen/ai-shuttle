from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.booking import Booking
from app.models.shuttle import Shuttle


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        self.db.flush()

        return booking

    def get_by_id(self, booking_id: int) -> Booking | None:
        statement = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.shuttle).selectinload(Shuttle.route),
            )
        )

        return self.db.scalar(statement)

    def get_confirmed_on_route(
        self,
        user_id: int,
        route_id: int,
        booking_date: date,
    ) -> Booking | None:
        statement = (
            select(Booking)
            .join(Booking.shuttle)
            .where(
                Booking.user_id == user_id,
                Booking.booking_date == booking_date,
                Booking.status == "confirmed",
                Shuttle.route_id == route_id,
            )
            .options(
                selectinload(Booking.shuttle).selectinload(Shuttle.route),
            )
        )

        return self.db.scalar(statement)

    def get_upcoming_by_user_id(
        self,
        user_id: int,
        from_date: date | None = None,
    ) -> list[Booking]:
        statement = (
            select(Booking)
            .where(Booking.user_id == user_id)
            .options(
                selectinload(Booking.shuttle).selectinload(Shuttle.route),
            )
        )

        if from_date is not None:
            statement = statement.where(Booking.booking_date >= from_date)

        statement = statement.order_by(
            Booking.booking_date.asc(),
            Booking.pickup_time.asc(),
        )

        return list(self.db.scalars(statement).all())