from app.db.database import SessionLocal
from app.models.booking import Booking


def reset_demo_database():
    with SessionLocal() as session:
        deleted_count = session.query(Booking).delete()
        session.commit()

    print(f"Deleted {deleted_count} booking(s).")


if __name__ == "__main__":
    reset_demo_database()