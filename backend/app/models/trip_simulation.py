from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TripSimulation(Base):
    """Replays a booking's trip as if it were happening now.

    Real shuttles aren't moving during a demo, so the simulator maps the
    booking's timeline onto the present: `started_at` (real time) maps to
    `start_minutes` relative to departure, and simulated time runs `speed`
    times faster than real time. `delay_minutes` pushes the shuttle late.
    """

    __tablename__ = "trip_simulations"

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    start_minutes: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    speed: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    delay_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
