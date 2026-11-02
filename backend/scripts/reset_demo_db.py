from app.db.database import SessionLocal
from app.models.booking import Booking
from app.models.user_location import UserLocation


def reset_demo_database():
    with SessionLocal() as session:
        # Trip simulations go with their bookings (ON DELETE CASCADE).
        deleted_count = session.query(Booking).delete()
        session.query(UserLocation).delete()
        session.commit()

    print(f"Deleted {deleted_count} booking(s).")


if __name__ == "__main__":
    reset_demo_database()