from datetime import date, time

from sqlalchemy import Date, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    child_id: Mapped[int] = mapped_column(
        ForeignKey("children.id"),
        nullable=False,
    )

    shuttle_id: Mapped[int] = mapped_column(
        ForeignKey("shuttles.id"),
        nullable=False,
    )

    booking_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    pickup_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="confirmed",
    )

    user = relationship(
        "User",
        back_populates="bookings",
    )

    child = relationship(
        "Child",
        back_populates="bookings",
    )

    shuttle = relationship(
        "Shuttle",
        back_populates="bookings",
    )