from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Child(Base):
    __tablename__ = "children"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    school: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    usual_pickup_location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="children",
    )

    bookings = relationship(
        "Booking",
        back_populates="child",
    )