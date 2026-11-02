from app.rag.ingest import KNOWLEDGE_DIR, split_sections
from app.rag.retriever import search_knowledge
from tests.fake_embedder import FakeEmbedder


def test_policy_documents_split_into_titled_sections():
    sections = split_sections(KNOWLEDGE_DIR / "booking_policy.md")

    assert sections[0].title == "Booking Policy"
    assert [s.heading for s in sections] == [
        "Service days",
        "Booking window",
        "Same-day bookings",
        "Seat availability",
        "One booking per route per day",
    ]
    assert "Monday to Friday" in sections[0].content


def test_search_returns_matching_section_first(db):
    passages = search_knowledge(
        db, FakeEmbedder(), "how long do drivers wait at the pickup stop"
    )

    assert (passages[0].title, passages[0].heading) == ("Pickup Rules", "Arriving at the stop")
    assert len(passages) == 3
    assert passages[0].similarity >= passages[1].similarity


class StrictEmbedder(FakeEmbedder):
    min_similarity = 0.99


def test_unrelated_query_returns_nothing(db):
    assert search_knowledge(db, StrictEmbedder(), "can I bring my dog") == []
