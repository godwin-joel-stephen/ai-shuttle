from datetime import time

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Shuttle(Base):
    __tablename__ = "shuttles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id"),
        nullable=False,
    )

    departure_time: Mapped[time] = mapped_column(
        nullable=False,
    )

    arrival_time: Mapped[time] = mapped_column(
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        nullable=False,
    )

    route = relationship(
        "Route",
        back_populates="shuttles",
    )

    preferred_by = relationship(
        "Preference",
        back_populates="usual_shuttle",
    )

    bookings = relationship(
        "Booking",
        back_populates="shuttle",
    )