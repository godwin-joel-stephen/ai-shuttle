"""Delete every booking, then add the demo rider's past rides (see
app/db/ride_history.py) so F10's learned habits have history.

    python -m scripts.reset_demo_db               # with ride history
    python -m scripts.reset_demo_db --no-history  # no habits: the saved 7:30
"""

import argparse

from sqlalchemy import select

from app.core import clock
from app.db.database import SessionLocal
from app.db.ride_history import add_past_rides, demo_rides
from app.models.booking import Booking
from app.models.preference import Preference
from app.models.user import User
from app.models.user_location import UserLocation


def reset_demo_database(history: bool = True):
    with SessionLocal() as session:
        # Trip simulations go with their bookings (ON DELETE CASCADE).
        deleted_count = session.query(Booking).delete()
        session.query(UserLocation).delete()
        # Unpin, so the usual is learned again.
        session.query(Preference).update({Preference.usual_pinned: False})
        session.commit()
        print(f"Deleted {deleted_count} booking(s).")

        if history:
            user_id = session.scalar(select(User.id).where(User.email == "godwin@example.com"))
            count = add_past_rides(session, user_id, demo_rides(clock.today()))
            print(f"Added {count} past ride(s) for habit learning.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-history", action="store_true", help="don't add past rides")
    reset_demo_database(history=not parser.parse_args().no_history)
