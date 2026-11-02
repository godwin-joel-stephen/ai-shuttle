import os
import sys
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, make_url, text

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _use_test_database() -> None:
    """Point the app at `<db>_test` so tests never touch demo data.

    Must run before anything imports app.core.config, which reads
    DATABASE_URL once at import time.
    """
    dev_url = make_url(
        os.environ.get("DATABASE_URL")
        or dotenv_values(BACKEND_DIR / ".env")["DATABASE_URL"]
    )
    # Idempotent: test modules also import this file as `tests.conftest`,
    # which runs it a second time.
    if dev_url.database.endswith("_test"):
        return
    test_url = dev_url.set(database=f"{dev_url.database}_test")

    admin = create_engine(
        dev_url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    with admin.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": test_url.database},
        )
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    admin.dispose()

    os.environ["DATABASE_URL"] = test_url.render_as_string(hide_password=False)


_use_test_database()

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
