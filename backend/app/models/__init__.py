from app.models.user import User
from app.models.preference import Preference
from app.models.route import Route
from app.models.shuttle import Shuttle
from app.models.booking import Booking
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.trip_simulation import TripSimulation

__all__ = [
    "User",
    "Preference",
    "Route",
    "Shuttle",
    "Booking",
    "KnowledgeChunk",
    "TripSimulation",
]