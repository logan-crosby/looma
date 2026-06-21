"""SourceAdapter interface - the heterogeneity firewall (ARCHITECTURE.md 2.1)."""

from typing import Iterable, Iterator, Protocol

from ..models import NormalizedEvent, SessionHandle


class SourceAdapter(Protocol):
    id: str

    def discover(self) -> Iterable[SessionHandle]:
        """Yield discoverable session handles."""
        ...

    def read(self, handle: SessionHandle) -> Iterator[NormalizedEvent]:
        """Yield normalized events for one session."""
        ...
