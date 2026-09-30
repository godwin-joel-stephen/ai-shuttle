from datetime import date

from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.models.booking import Booking
from app.tools.booking_tools import book_shuttle


def test_book_shuttle_persists_booking():
    db = SessionLocal()

    try:
        before_count = db.scalar(
            select(func.count(Booking.id))
        )

        booking = book_shuttle(
            db=db,
            user_id=1,
            booking_date=date(2026, 10, 1),
        )

        db.refresh(booking)

        after_count = db.scalar(
            select(func.count(Booking.id))
        )

        assert after_count == before_count + 1

        assert booking.id is not None
        assert booking.user_id == 1
        assert booking.child_id == 1
        assert booking.shuttle_id == 1
        assert booking.booking_date == date(2026, 10, 1)
        assert booking.status == "confirmed"

    finally:
        db.query(Booking).delete()
        db.commit()
        db.close()