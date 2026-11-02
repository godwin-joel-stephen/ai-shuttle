"""Re-embed backend/knowledge/*.md after editing a policy document."""

from app.db.database import SessionLocal
from app.rag.embeddings import get_embedder
from app.rag.ingest import ingest_knowledge


if __name__ == "__main__":
    with SessionLocal() as session:
        count = ingest_knowledge(session, get_embedder())

    print(f"Ingested {count} policy sections.")
