from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.embeddings import Embedder


@dataclass(frozen=True)
class Passage:
    source: str
    title: str
    heading: str
    content: str
    similarity: float
    # Confident enough to cite as the source of an answer.
    citable: bool


def search_knowledge(
    db: Session,
    embedder: Embedder,
    query: str,
    limit: int = 3,
) -> list[Passage]:
    """Policy sections similar enough to the query to be relevant, best
    first. An empty list means the policies don't cover it."""

    distance = KnowledgeChunk.embedding.cosine_distance(
        embedder.embed_query(query)
    )
    rows = db.execute(
        select(KnowledgeChunk, distance.label("distance"))
        .order_by(distance)
        .limit(limit)
    ).all()

    return [
        Passage(
            source=chunk.source,
            title=chunk.title,
            heading=chunk.heading,
            content=chunk.content,
            similarity=round(1 - dist, 3),
            citable=1 - dist >= embedder.citation_min_similarity,
        )
        for chunk, dist in rows
        if 1 - dist >= embedder.min_similarity
    ]
