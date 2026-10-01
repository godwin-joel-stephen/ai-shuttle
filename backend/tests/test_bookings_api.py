from datetime import date

from fastapi.testclient import TestClient

from app.agent.fake_llm import FakeLLM
from app.api.bookings import get_llm
from app.db.database import SessionLocal, get_db
from app.main import app
from app.models.booking import Booking


def test_create_booking():
    db = SessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    def override_get_llm():
        return FakeLLM(
            reference_date=date(2026, 9, 30),
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm] = override_get_llm

    try:
        client = TestClient(app)

        response = client.post(
            "/bookings",
            json={
                "user_id": 1,
                "message": "Book my usual shuttle for tomorrow.",
            },
        )

        assert response.status_code == 200

        data = response.json()
        booking_id = data["booking_id"]

        assert booking_id > 0
        assert data["message"].startswith(
            "Shuttle booked successfully."
        )

        booking = db.get(Booking, booking_id)

        assert booking is not None
        assert booking.user_id == 1
        assert booking.booking_date == date(2026, 10, 1)

    finally:
        if "booking_id" in locals():
            booking = db.get(Booking, booking_id)

            if booking is not None:
                db.delete(booking)
                db.commit()

        app.dependency_overrides.clear()
        db.close()