from datetime import time

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.user import User
from app.models.child import Child
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
        # Child
        # ---------------------------------------------------------
        child = Child(
            user_id=user.id,
            name="Emma",
            school="AI Shuttle Academy",
            usual_pickup_location="Home",
        )

        session.add(child)

        # ---------------------------------------------------------
        # Routes
        # ---------------------------------------------------------
        morning_route = Route(
            name="Home → School Morning Route",
            pickup_location="Home",
            dropoff_location="AI Shuttle Academy",
        )

        afternoon_route = Route(
            name="School → Home Afternoon Route",
            pickup_location="AI Shuttle Academy",
            dropoff_location="Home",
        )

        session.add_all([
            morning_route,
            afternoon_route,
        ])

        session.flush()

        # ---------------------------------------------------------
        # Shuttles
        # ---------------------------------------------------------
        morning_shuttle_a = Shuttle(
            name="Morning Shuttle A",
            route_id=morning_route.id,
            departure_time=time(7, 30),
            arrival_time=time(8, 15),
            capacity=10,
        )

        morning_shuttle_b = Shuttle(
            name="Morning Shuttle B",
            route_id=morning_route.id,
            departure_time=time(7, 45),
            arrival_time=time(8, 30),
            capacity=10,
        )

        afternoon_shuttle = Shuttle(
            name="Afternoon Shuttle A",
            route_id=afternoon_route.id,
            departure_time=time(15, 30),
            arrival_time=time(16, 15),
            capacity=10,
        )

        session.add_all([
            morning_shuttle_a,
            morning_shuttle_b,
            afternoon_shuttle,
        ])

        session.flush()

        # ---------------------------------------------------------
        # User preference
        # ---------------------------------------------------------
        preference = Preference(
            user_id=user.id,
            usual_shuttle_id=morning_shuttle_a.id,
        )

        session.add(preference)

        session.commit()

        print("Seed data created successfully.")


if __name__ == "__main__":
    seed_database()