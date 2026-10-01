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


def test_get_upcoming_bookings_empty():
    db = SessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.get("/bookings?user_id=1")

        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_get_upcoming_bookings_with_booking():
    from datetime import time

    db = SessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    booking = Booking(
        user_id=1,
        child_id=1,
        shuttle_id=1,
        booking_date=date(2026, 10, 5),
        pickup_time=time(7, 30),
        status="confirmed",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    try:
        client = TestClient(app)
        response = client.get("/bookings?user_id=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        matched = next((b for b in data if b["id"] == booking.id), None)
        assert matched is not None
        assert matched["id"] == booking.id
        assert matched["booking_date"] == "2026-10-05"
        assert matched["pickup_time"] == "07:30:00"
        assert matched["status"] == "confirmed"
        assert matched["child_name"] == "Emma"
        assert matched["shuttle_name"] == "Morning Shuttle A"
        assert matched["route_name"] == "Home → School Morning Route"
        assert matched["pickup_location"] == "Home"
        assert matched["destination"] == "AI Shuttle Academy"
    finally:
        db.delete(booking)
        db.commit()
        app.dependency_overrides.clear()
        db.close()