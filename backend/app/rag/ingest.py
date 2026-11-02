"""Load the policy documents in backend/knowledge into knowledge_chunks.

Each "## " section becomes one chunk: sections are short and
self-contained, so they make better retrieval units than fixed-size
windows, and the heading doubles as a readable citation.
"""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.embeddings import Embedder


KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"


@dataclass(frozen=True)
class Section:
    source: str
    title: str
    heading: str
    content: str


def split_sections(path: Path) -> list[Section]:
    title = path.stem.replace("_", " ").title()
    sections = []
    heading = None
    lines: list[str] = []

    def flush():
        if heading and "".join(lines).strip():
            sections.append(Section(path.stem, title, heading, "\n".join(lines).strip()))

    for line in path.read_text().splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            flush()
            heading, lines = line[3:].strip(), []
        else:
            lines.append(line)

    flush()
    return sections


def ingest_knowledge(db: Session, embedder: Embedder, directory: Path = KNOWLEDGE_DIR) -> int:
    """Replace all chunks with the current documents. Returns the count."""

    sections = [
        section
        for path in sorted(directory.glob("*.md"))
        for section in split_sections(path)
    ]
    # Embed the heading with the body so a section about "Service days"
    # matches questions that only use the heading's words.
    vectors = embedder.embed_documents(
        [f"{s.title}: {s.heading}\n{s.content}" for s in sections]
    )

    db.execute(delete(KnowledgeChunk))
    db.add_all(
        KnowledgeChunk(
            source=s.source,
            title=s.title,
            heading=s.heading,
            content=s.content,
            embedding=vector,
        )
        for s, vector in zip(sections, vectors)
    )
    db.commit()

    return len(sections)
