from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    usual_shuttle_id: Mapped[int | None] = mapped_column(
        ForeignKey("shuttles.id"),
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="preferences",
    )

    usual_shuttle = relationship(
        "Shuttle",
        back_populates="preferred_by",
    )