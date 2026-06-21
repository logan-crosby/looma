"""Canonical in-memory data shapes shared across layers."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class NormalizedEvent:
    """One agent turn, vendor-agnostic (ARCHITECTURE.md section 2.2)."""

    event_hash: str
    source: str
    session_native_id: str
    project_root: Optional[str]
    git_remote: Optional[str]
    git_branch: Optional[str]
    seq: int
    ts: Optional[str]
    role: str
    agent_model: Optional[str]
    text: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw_json: str = ""


@dataclass
class SessionHandle:
    """A discoverable unit of agent history (ARCHITECTURE.md section 2.1)."""

    source: str
    native_id: str
    path: str
