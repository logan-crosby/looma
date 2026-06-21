"""Confidence scoring - ARCHITECTURE.md section 5.4.

confidence = clamp01(
    0.30*file_overlap + 0.25*commit_linkage + 0.20*session_breadth
  + 0.15*agent_breadth + 0.10*temporal_persistence )
then ledger overrides pin user-confirmed -> 1.0, user-rejected -> 0.0.

Some components are legitimately zero in the Phase 1 slice (e.g. candidate
file_overlap), which is allowed by the checklist.
"""

import math

from .util import clamp01

W_FILE = 0.30
W_COMMIT = 0.25
W_SESSION = 0.20
W_AGENT = 0.15
W_TEMPORAL = 0.10


def _breadth(n: int, k: float = 1.0) -> float:
    # saturating: 0 distinct-beyond-first -> 0; grows toward 1
    return 1.0 - math.exp(-k * max(0, n - 1))


def _temporal(days: float, tau: float = 7.0) -> float:
    if not days or days <= 0:
        return 0.0
    return 1.0 - math.exp(-days / tau)


def score(
    file_overlap: float,
    has_commit: bool,
    n_sessions: int,
    n_agents: int,
    span_days: float,
) -> float:
    raw = (
        W_FILE * clamp01(file_overlap)
        + W_COMMIT * (1.0 if has_commit else 0.0)
        + W_SESSION * _breadth(n_sessions)
        + W_AGENT * _breadth(n_agents)
        + W_TEMPORAL * _temporal(span_days)
    )
    return round(clamp01(raw), 4)


def apply_ledger_override(store, node_type: str, ref_id: int, value: float) -> float:
    """Pin confidence from durable user corrections (ARCHITECTURE.md 5.4, 13.2).

    Schema-backed and live even though Phase 1 has no command to write corrections:
    if a constraint exists, it wins.
    """
    if store.constraint_for("FORCE_PROMOTE", node_type, ref_id):
        return 1.0
    if store.constraint_for("FORCE_REJECT", node_type, ref_id):
        return 0.0
    if store.constraint_for("FALSE_POSITIVE", node_type, ref_id):
        return 0.0
    return value


def cohesion(file_sets: list[set]) -> float:
    """Average pairwise Jaccard across member sessions' file sets."""
    sets = [s for s in file_sets if s]
    if not sets:
        return 0.0
    if len(sets) == 1:
        return 0.3  # some evidence from a single populated session
    total = count = 0.0
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            a, b = sets[i], sets[j]
            union = len(a | b)
            total += (len(a & b) / union) if union else 0.0
            count += 1
    return total / count if count else 0.0
