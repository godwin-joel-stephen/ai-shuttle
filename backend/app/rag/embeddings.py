"""Text embeddings for policy retrieval.

Runs a small open-source model (BAAI/bge-small-en-v1.5, 384 dimensions)
locally via ONNX, so policy search costs nothing per query and no policy
text or user question leaves the server for embedding.
"""

from functools import lru_cache
from pathlib import Path
from typing import Protocol

from fastembed import TextEmbedding

from app.models.knowledge_chunk import EMBEDDING_DIMENSION


_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "fastembed"


class Embedder(Protocol):
    # Similarity scales differ per model, so each embedder carries its own
    # calibrated thresholds: below min_similarity a passage is noise the
    # agent shouldn't see; below citation_min_similarity it's related but
    # not an answer, so it isn't cited.
    min_similarity: float
    citation_min_similarity: float

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class LocalEmbedder:
    MODEL = "BAAI/bge-small-en-v1.5"

    # Calibrated on the policy corpus: real policy questions scored
    # 0.72-0.81, unrelated ones (pets, wifi, weather) 0.52-0.56, and
    # "parking at the office" -> pickup points (related, not an answer) 0.68.
    min_similarity = 0.60
    citation_min_similarity = 0.70

    def __init__(self):
        # Downloaded once (~130 MB) into backend/.cache, then loaded locally.
        self.model = TextEmbedding(self.MODEL, cache_dir=str(_CACHE_DIR))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self.model.passage_embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        # bge models expect queries and passages to be embedded differently.
        return next(iter(self.model.query_embed(text))).tolist()


@lru_cache
def get_embedder() -> Embedder:
    embedder = LocalEmbedder()
    assert len(embedder.embed_query("dimension check")) == EMBEDDING_DIMENSION
    return embedder
