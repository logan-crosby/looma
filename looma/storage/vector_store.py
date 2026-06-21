"""VectorStore interface + a dependency-free stub.

ARCHITECTURE.md allows sqlite-vec only if it is simple in the current stack;
for the Phase 1 slice we keep the core dependency-free and stub semantic
retrieval behind this interface. FTS5 carries lexical retrieval in the meantime.
Swapping in sqlite-vec later means implementing this interface, nothing else.
"""

from typing import Protocol


class VectorStore(Protocol):
    def add(self, kind: str, ref_id: int, text: str) -> None: ...

    def search(self, kind: str, query: str, limit: int = 10) -> list[tuple[int, float]]:
        """Return [(ref_id, score)] best-first."""
        ...

    def reset(self) -> None: ...


class NullVectorStore:
    """No-op stub. Semantic search is disabled; lexical (FTS5) handles retrieval.

    Real, not silently lying: search() returns an empty list so callers fall back
    to lexical ranking deterministically.
    """

    enabled = False

    def add(self, kind: str, ref_id: int, text: str) -> None:
        return None

    def search(self, kind: str, query: str, limit: int = 10) -> list[tuple[int, float]]:
        return []

    def reset(self) -> None:
        return None
