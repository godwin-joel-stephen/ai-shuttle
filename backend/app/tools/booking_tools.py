from datetime import date

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository
from app.services.booking_service import BookingService


def book_shuttle(
    db: Session,
    user_id: int,
    booking_date: date,
):
    service = BookingService(
        db=db,
        user_repository=UserRepository(db),
        preference_repository=PreferenceRepository(db),
        shuttle_repository=ShuttleRepository(db),
        booking_repository=BookingRepository(db),
    )

    return service.book_usual_shuttle(
        user_id=user_id,
        booking_date=booking_date,
    )


def create_booking_tool(db: Session):

    @tool
    def book_shuttle_tool(
        user_id: int,
        booking_date: date,
    ):
        """Book the user's usual shuttle for a specific date."""

        return book_shuttle(
            db=db,
            user_id=user_id,
            booking_date=booking_date,
        )

    return book_shuttle_tool