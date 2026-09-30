from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pickup_location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    dropoff_location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    shuttles = relationship(
        "Shuttle",
        back_populates="route",
    )