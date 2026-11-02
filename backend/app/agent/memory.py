"""Conversation memory: LangGraph checkpoints stored in PostgreSQL.

Each conversation id is a LangGraph thread, so follow-ups such as "make it
earlier" see the earlier messages and tool results, and survive restarts.
"""

from functools import lru_cache

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from sqlalchemy import make_url

from app.core.config import settings


@lru_cache
def get_checkpointer() -> PostgresSaver:
    # psycopg wants a plain postgresql:// URL, not SQLAlchemy's
    # postgresql+psycopg:// form.
    url = make_url(settings.database_url).set(drivername="postgresql")

    pool = ConnectionPool(
        conninfo=url.render_as_string(hide_password=False),
        max_size=5,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        open=True,
    )
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()

    return checkpointer
