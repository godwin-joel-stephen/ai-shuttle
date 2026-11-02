"""Point the app at a separate database (tests, evaluations).

Kept free of app imports on purpose: it must run before anything imports
app.core.config, which reads DATABASE_URL once at import time. That is
also why it lives directly under `app` and not in `app.db`: importing
anything from `app.db` runs app/db/__init__.py, which connects with the
original settings, so the switch would come too late.
"""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, make_url, text


_BACKEND_DIR = Path(__file__).resolve().parents[1]


def use_isolated_database(suffix: str) -> str:
    """Switch DATABASE_URL to `<database>_<suffix>`, creating it if needed.

    Idempotent, so running it twice (e.g. a conftest imported again as a
    module) doesn't append the suffix twice. Returns the database name.
    """

    url = make_url(
        os.environ.get("DATABASE_URL")
        or dotenv_values(_BACKEND_DIR / ".env")["DATABASE_URL"]
    )
    if url.database.endswith(f"_{suffix}"):
        return url.database

    isolated = url.set(database=f"{url.database}_{suffix}")

    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": isolated.database},
        )
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{isolated.database}"'))
    admin.dispose()

    os.environ["DATABASE_URL"] = isolated.render_as_string(hide_password=False)
    return isolated.database


def assert_isolated(engine_url, suffix: str) -> None:
    """Refuse to continue on anything but the isolated database: tests and
    evaluations drop and reseed every table."""

    if not engine_url.database.endswith(f"_{suffix}"):
        raise RuntimeError(
            f"Refusing to run against database {engine_url.database!r}; "
            f"expected one ending in '_{suffix}'."
        )
