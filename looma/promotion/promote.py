"""Promotion rules - CandidateMemory -> ValidatedMemory (ARCHITECTURE.md 5, checklist H).

Promote a candidate if it is connected to a commit, OR connected to an active
WorkItem, OR referenced in multiple sessions. Single-session weak candidates stay
in staging (the noise the graph is meant to keep out). User corrections
(force-promote / force-reject) override, per section 5.4 / 13.2.
"""

# entity kind -> graph relation pointing at the WorkItem (ARCHITECTURE.md 7.1)
KIND_REL = {
    "decision": "CONSTRAINS",
    "architecture": "CONSTRAINS",
    "todo": "BLOCKS",
    "bug": "AFFECTS",
}


def should_promote(
    commit_linked: bool,
    work_item_active: bool,
    n_sessions: int,
    force_promote: bool = False,
    force_reject: bool = False,
) -> bool:
    if force_reject:
        return False
    if force_promote:
        return True
    return bool(commit_linked or work_item_active or n_sessions >= 2)
