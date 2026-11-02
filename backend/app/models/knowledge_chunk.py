from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


EMBEDDING_DIMENSION = 384


class KnowledgeChunk(Base):
    """One section of a policy document, embedded for semantic search."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    heading: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIMENSION),
        nullable=False,
    )

    __table_args__ = (
        # Approximate nearest-neighbour index for cosine similarity.
        Index(
            "ix_knowledge_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
