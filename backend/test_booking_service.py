from datetime import date, timedelta

from app.db.database import SessionLocal
from app.graph.booking_graph import create_booking_graph
from app.models.booking import Booking


db = SessionLocal()

tomorrow = date.today() + timedelta(days=1)

try:
    graph = create_booking_graph(db)

    result = graph.invoke(
        {
            "user_id": 1,
            "booking_date": tomorrow,
        }
    )

    booking_id = result["booking_id"]

    assert result["response"] == (
        f"Shuttle booked successfully. Booking ID: {booking_id}."
    )

    booking = db.get(Booking, booking_id)

    print("BOOKING CREATED")
    print("Booking ID:", booking.id)
    print("User ID:", booking.user_id)
    print("Child ID:", booking.child_id)
    print("Shuttle ID:", booking.shuttle_id)
    print("Booking Date:", booking.booking_date)
    print("Pickup Time:", booking.pickup_time)
    print("Status:", booking.status)
    print("Response:", result["response"])

finally:
    db.close()