from sqlalchemy import text

from app import models
from app.db.base import Base
from app.db.database import engine


def init_db() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)

    # create_all never alters existing tables; add F10's column in place
    # so the demo database keeps its bookings.
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE preferences ADD COLUMN IF NOT EXISTS "
            "usual_pinned boolean NOT NULL DEFAULT false"
        ))


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully")
