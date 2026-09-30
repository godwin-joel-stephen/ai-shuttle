from datetime import date, timedelta

from app.db.database import SessionLocal
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.services.booking_service import BookingService


db = SessionLocal()

service = BookingService(
    db,
    UserRepository(db),
    PreferenceRepository(db),
    ShuttleRepository(db),
    BookingRepository(db),
)

tomorrow = date.today() + timedelta(days=1)

try:
    booking = service.book_usual_shuttle(
        user_id=1,
        booking_date=tomorrow,
    )

    print("BOOKING CREATED")
    print("Booking ID:", booking.id)
    print("User ID:", booking.user_id)
    print("Child ID:", booking.child_id)
    print("Shuttle ID:", booking.shuttle_id)
    print("Booking Date:", booking.booking_date)
    print("Pickup Time:", booking.pickup_time)
    print("Status:", booking.status)

finally:
    db.close()