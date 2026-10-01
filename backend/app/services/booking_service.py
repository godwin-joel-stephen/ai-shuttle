from datetime import date

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.repositories.booking_repository import BookingRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.shuttle_repository import ShuttleRepository
from app.repositories.user_repository import UserRepository


class BookingService:
    def __init__(
        self,
        db: Session,
        user_repository: UserRepository,
        preference_repository: PreferenceRepository,
        shuttle_repository: ShuttleRepository,
        booking_repository: BookingRepository,
    ):
        self.db = db
        self.user_repository = user_repository
        self.preference_repository = preference_repository
        self.shuttle_repository = shuttle_repository
        self.booking_repository = booking_repository

    def _resolve_user(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError(f"User {user_id} not found.")

        return user

    def _resolve_child(self, user_id: int):
        user = self._resolve_user(user_id)

        if not user.children:
            raise ValueError(
                f"User {user_id} has no children."
            )

        return user.children[0]

    def _resolve_usual_shuttle(self, user_id: int):
        preference = self.preference_repository.get_by_user_id(user_id)

        if preference is None:
            raise ValueError(
                f"User {user_id} has no preferences."
            )

        if preference.usual_shuttle_id is None:
            raise ValueError(
                f"User {user_id} has no usual shuttle."
            )

        shuttle = self.shuttle_repository.get_by_id(
            preference.usual_shuttle_id
        )

        if shuttle is None:
            raise ValueError(
                f"Usual shuttle "
                f"{preference.usual_shuttle_id} not found."
            )

        return shuttle

    def book_usual_shuttle(
        self,
        user_id: int,
        booking_date: date,
    ) -> Booking:
        user = self._resolve_user(user_id)
        child = self._resolve_child(user_id)
        shuttle = self._resolve_usual_shuttle(user_id)

        if not self.shuttle_repository.has_available_seat(
            shuttle.id,
            booking_date,
        ):
            raise ValueError(
                f"Shuttle {shuttle.id} is not available "
                f"on {booking_date}."
            )

        booking = Booking(
            user_id=user.id,
            child_id=child.id,
            shuttle_id=shuttle.id,
            booking_date=booking_date,
            pickup_time=shuttle.departure_time,
            status="confirmed",
        )

        self.booking_repository.create(booking)

        self.db.commit()

        return booking

    def get_upcoming_bookings(
        self,
        user_id: int,
        from_date: date | None = None,
    ) -> list[Booking]:
        self._resolve_user(user_id)

        if from_date is None:
            from_date = date.today()

        return self.booking_repository.get_upcoming_by_user_id(
            user_id=user_id,
            from_date=from_date,
        )