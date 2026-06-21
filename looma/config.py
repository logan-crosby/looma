"""Runtime configuration and well-known paths."""

import os
from pathlib import Path

# Confidence bands (ARCHITECTURE.md section 5.4).
BAND_HIGH = 0.75
BAND_LOW = 0.40

# Resume ambiguity thresholds (ARCHITECTURE.md section 10.1).
RESUME_HIGH = BAND_HIGH
RESUME_LOW = BAND_LOW
RESUME_MARGIN = 0.15

# WorkItem resolution thresholds (ARCHITECTURE.md section 4.4).
RESOLVE_HIGH = 0.62  # assign to existing WorkItem at/above this score
RESOLVE_LOW = 0.30   # below this -> brand new WorkItem; between -> RELATED link
# Second-pass agglomerative merge: sessions editing substantially the same files are
# the same effort. File overlap is the strongest, most reliable signal (Phase 1).
MERGE_FILE_JACCARD = 0.5   # >= this file overlap -> merge two WorkItems
RELATED_MIN = 0.2          # [RELATED_MIN, MERGE_FILE_JACCARD) -> a RELATED link, not a merge


def home() -> Path:
    return Path(os.path.expanduser("~"))


def claude_projects_dir() -> Path:
    return home() / ".claude" / "projects"


def default_db_path() -> Path:
    """Global store location. Override with LOOMA_DB for tests/isolation."""
    env = os.environ.get("LOOMA_DB")
    if env:
        return Path(env)
    return home() / ".looma" / "looma.db"


def band(confidence: float) -> str:
    if confidence >= BAND_HIGH:
        return "high"
    if confidence >= BAND_LOW:
        return "medium"
    return "low"
