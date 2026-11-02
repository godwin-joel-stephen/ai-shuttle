import hashlib
import math
import re

from app.models.knowledge_chunk import EMBEDDING_DIMENSION


class FakeEmbedder:
    """Deterministic bag-of-words embedder: no model download, and texts
    that share words are similar, which is enough to test retrieval."""

    min_similarity = 0.0
    citation_min_similarity = 0.2

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSION
        vector[0] = 0.01  # avoid a zero vector for word-less text

        for word in re.findall(r"[a-z]+", text.lower()):
            index = int(hashlib.md5(word.encode()).hexdigest(), 16) % EMBEDDING_DIMENSION
            vector[index] += 1.0

        norm = math.sqrt(sum(v * v for v in vector))
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)
