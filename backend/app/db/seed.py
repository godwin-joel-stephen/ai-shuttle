from datetime import time

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.user import User
from app.models.preference import Preference
from app.models.route import Route
from app.models.shuttle import Shuttle


def seed_database():
    with SessionLocal() as session:
        # Prevent duplicate seed data
        existing_user = session.scalar(
            select(User).where(User.email == "godwin@example.com")
        )

        if existing_user:
            print("Seed data already exists.")
            return

        # ---------------------------------------------------------
        # User
        # ---------------------------------------------------------
        user = User(
            name="Godwin Joel",
            email="godwin@example.com",
        )

        session.add(user)
        session.flush()

        # ---------------------------------------------------------
        # Routes
        # ---------------------------------------------------------
        morning_route = Route(
            name="Home → Office Morning Route",
            pickup_location="Home",
            dropoff_location="Office",
        )

        evening_route = Route(
            name="Office → Home Evening Route",
            pickup_location="Office",
            dropoff_location="Home",
        )

        session.add_all([
            morning_route,
            evening_route,
        ])

        session.flush()

        # ---------------------------------------------------------
        # Shuttles
        # ---------------------------------------------------------
        # Every 15 minutes so "Earlier" / "Later" always has a neighbour.
        morning_shuttles = [
            Shuttle(
                name=f"Morning Shuttle {letter}",
                route_id=morning_route.id,
                departure_time=departure,
                arrival_time=arrival,
                capacity=10,
            )
            for letter, departure, arrival in [
                ("A", time(7, 0), time(7, 45)),
                ("B", time(7, 15), time(8, 0)),
                ("C", time(7, 30), time(8, 15)),
                ("D", time(7, 45), time(8, 30)),
                ("E", time(8, 0), time(8, 45)),
            ]
        ]

        evening_shuttles = [
            Shuttle(
                name="Evening Shuttle A",
                route_id=evening_route.id,
                departure_time=time(17, 30),
                arrival_time=time(18, 15),
                capacity=10,
            ),
            Shuttle(
                name="Evening Shuttle B",
                route_id=evening_route.id,
                departure_time=time(18, 0),
                arrival_time=time(18, 45),
                capacity=10,
            ),
        ]

        session.add_all(morning_shuttles + evening_shuttles)

        session.flush()

        # ---------------------------------------------------------
        # User preference
        # ---------------------------------------------------------
        preference = Preference(
            user_id=user.id,
            usual_shuttle_id=morning_shuttles[2].id,
        )

        session.add(preference)

        session.commit()

        print("Seed data created successfully.")


if __name__ == "__main__":
    seed_database()
