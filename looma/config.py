"""Runtime configuration and well-known paths."""

import os
from pathlib import Path

# Confidence bands - the human-readable label only (cli.py, ask.py); they do NOT
# gate promotion, ranking, or resume (resume gates on MATCH relevance, below).
# The score (confidence.py) weights commit linkage + session/agent breadth, which
# are structurally ~0 for solo, single-session, locally-committed work - so the
# real corpus distribution tops out near ~0.46, not 1.0. Calibrating the bands to
# that range keeps the label informative (separating thin single-session items
# from corroborated multi-session ones) instead of stamping ~95% of work "low".
# (V2.1, ARCHITECTURE.md section 5.4.)
BAND_HIGH = 0.30
BAND_LOW = 0.12

# Resume ambiguity thresholds (ARCHITECTURE.md section 10.1).
# These gate on MATCH RELEVANCE (how well a WorkItem answers the goal), not the
# item's intrinsic confidence. Gating on intrinsic confidence made resume return
# COLD even when the correct item ranked #1 with relevance 1.0, because solo-dev
# work is structurally capped below the confidence band (Phase 1 evaluation).
RESUME_HIGH = BAND_HIGH
RESUME_LOW = BAND_LOW
RESUME_MARGIN = 0.15
MATCH_STRONG = 0.45   # relevance at/above this with a clear margin -> CONFIDENT
MATCH_WEAK = 0.15     # relevance below this -> COLD (no real match)

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
