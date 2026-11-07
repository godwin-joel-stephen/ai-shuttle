from sqlalchemy import Boolean, ForeignKey, false
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

    # Pinned: the rider chose this shuttle, so it beats the learned habit.
    # Unpinned, it is only the fallback when there is no habit yet.
    usual_pinned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    user = relationship(
        "User",
        back_populates="preferences",
    )

    usual_shuttle = relationship(
        "Shuttle",
        back_populates="preferred_by",
    )