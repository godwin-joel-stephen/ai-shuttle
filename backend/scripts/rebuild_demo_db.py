"""Drop every table, recreate the schema and reseed the demo data.

Use after model changes (create_all never alters existing tables).
For a quick reset between demo runs, use reset_demo_db.py instead.
"""

from sqlalchemy import text

from app.db.database import engine
from app.db.init_db import init_db
from app.db.seed import seed_database


def rebuild_demo_database():
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    init_db()
    seed_database()


if __name__ == "__main__":
    rebuild_demo_database()
