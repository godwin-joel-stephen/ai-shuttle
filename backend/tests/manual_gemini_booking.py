from datetime import date

from app.agent.factory import create_llm
from app.db.database import SessionLocal
from app.graph.booking_graph import create_booking_graph


def main() -> None:
    db = SessionLocal()

    try:
        llm = create_llm(
            reference_date=date(2026, 10, 1),
        )

        graph = create_booking_graph(
            db=db,
            llm=llm,
        )

        result = graph.invoke(
            {
                "user_id": 1,
                "user_input": "Book my usual shuttle for tomorrow.",
            }
        )

        print("Intent:", result["intent"])
        print("Booking date:", result["booking_date"])
        print("Booking ID:", result["booking_id"])
        print("Response:", result["response"])

    finally:
        db.close()


if __name__ == "__main__":
    main()