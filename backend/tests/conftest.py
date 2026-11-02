import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.db.database import SessionLocal  # noqa: E402
from app.models.booking import Booking  # noqa: E402
from app.models.shuttle import Shuttle  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.query(Booking).delete()
        session.commit()
        session.close()


@pytest.fixture
def user_id(db) -> int:
    return db.scalar(
        select(User.id).where(User.email == "godwin@example.com")
    )


@pytest.fixture
def shuttles(db) -> dict[str, Shuttle]:
    return {
        shuttle.name: shuttle
        for shuttle in db.scalars(select(Shuttle)).all()
    }
