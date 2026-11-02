import sys
from pathlib import Path

import pytest
from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.isolated_database import use_isolated_database  # noqa: E402

# Never touch demo data: tests run against `<database>_test`.
use_isolated_database("test")

from datetime import datetime, timedelta  # noqa: E402

from sqlalchemy import select  # noqa: E402

from app.core import clock  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.database import SessionLocal, engine  # noqa: E402
from app.db.seed import seed_database  # noqa: E402
from app.rag.ingest import ingest_knowledge  # noqa: E402
from tests.fake_embedder import FakeEmbedder  # noqa: E402


# Every test runs at this moment: a Monday morning before the first
# shuttle, so "tomorrow" is a service day and no cut-off has passed.
FIXED_NOW = datetime(2026, 11, 2, 6, 0)
TODAY = FIXED_NOW.date()
TOMORROW = TODAY + timedelta(days=1)
from app.models.booking import Booking  # noqa: E402
from app.models.shuttle import Shuttle  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_location import UserLocation  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def test_database():
    # Rebuild from the models every run so schema changes need no migration.
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()

    with SessionLocal() as session:
        ingest_knowledge(session, FakeEmbedder())


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    monkeypatch.setattr(clock, "now", lambda: FIXED_NOW)


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        # Trip simulations go with their bookings (ON DELETE CASCADE).
        session.query(Booking).delete()
        session.query(UserLocation).delete()
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
