from datetime import date

from sqlalchemy import func, select

from app.agent.fake_llm import FakeLLM
from app.db.database import SessionLocal
from app.graph.booking_graph import create_booking_graph
from app.models.booking import Booking


def test_booking_graph_creates_booking():
    db = SessionLocal()

    try:
        before_count = db.scalar(
            select(func.count(Booking.id))
        )

        llm = FakeLLM(
            reference_date=date(2026, 9, 30),
        )

        graph = create_booking_graph(
            db,
            llm,
        )

        result = graph.invoke(
            {
                "user_id": 1,
                "user_input": "Book my usual shuttle for tomorrow.",
            }
        )

        assert result["intent"] == "book_usual_shuttle"
        assert result["booking_date"] == date(2026, 10, 1)

        booking_id = result["booking_id"]

        after_count = db.scalar(
            select(func.count(Booking.id))
        )

        assert after_count == before_count + 1

        booking = db.get(Booking, booking_id)

        assert booking is not None
        assert booking.user_id == 1
        assert booking.child_id == 1
        assert booking.shuttle_id == 1
        assert booking.booking_date == date(2026, 10, 1)
        assert booking.pickup_time.isoformat() == "07:30:00"
        assert booking.status == "confirmed"

    finally:
        db.query(Booking).delete()
        db.commit()
        db.close()
