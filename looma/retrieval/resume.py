"""WorkItem-first Resume engine with uncertainty handling (ARCHITECTURE.md 10).

Resolves an optional goal to a WorkItem, decides confident vs ambiguous vs cold
per section 10.1 (never silently collapses low-confidence work), and assembles a
bundle from the WorkItem's graph star.
"""

import json

from .. import config, gitutil
from ..sanitize import looks_like_code
from .match import match_work_items

# modes
CONFIDENT = "confident"
AMBIGUOUS = "ambiguous"
COLD = "cold"
NO_GOAL = "no_goal"
EMPTY = "empty"


def _clean_entities(rows):
    """Drop memories whose title is a raw code/diff/log line, not human prose.

    The heuristic extractor still promotes diff lines and source fragments
    (Phase 1: ~28% of memories). Filtering them at read time keeps the resume
    bundle and next-step honest until extraction quality lands (Phase 4)."""
    return [r for r in rows if not looks_like_code(r.get("title") or "")]


def _next_step(open_todos, bugs, dirty, files):
    """Infer the single most actionable next step.

    Priority: a real open todo > uncommitted local changes > a real open bug >
    continue the most-recently-touched file. Code/diff-line memories are already
    filtered out by _clean_entities, so suggestions read as prose."""
    if open_todos:
        return f"finish: {open_todos[0]['title']}"
    if dirty:
        head = ", ".join(dirty[:3])
        more = f" (+{len(dirty) - 3} more)" if len(dirty) > 3 else ""
        return f"commit or continue uncommitted changes: {head}{more}"
    if bugs:
        return f"resolve: {bugs[0]['title']}"
    if files:
        return f"continue editing {files[0]}"
    return None


def _bundle_for(store, project: dict, wi: dict, dirty=None) -> dict:
    pid = project["id"]
    wid = wi["id"]
    decisions = _clean_entities([
        e for e in store.work_item_entities(wid)
        if e["kind"] in ("decision", "architecture")
    ])
    todos = _clean_entities(store.work_item_entities(wid, "todo"))
    bugs = _clean_entities(store.work_item_entities(wid, "bug"))
    sessions = store.work_item_sessions(pid, wid)
    commits = store.work_item_commits(pid, wid)
    try:
        files = json.loads(wi.get("files") or "[]")
    except (json.JSONDecodeError, TypeError):
        files = []

    open_todos = [t for t in todos if (t.get("status") or "open") == "open"]
    nxt = _next_step(open_todos, bugs, dirty or [], files)
    if nxt is None:
        # last resort: continue the effort itself, if its title is real prose
        title = wi.get("title") or ""
        if title and not looks_like_code(title) and title.lower() != "untitled work":
            nxt = f"continue: {title}"

    return {
        "work_item": wi,
        "decisions": decisions,
        "todos": open_todos,
        "bugs": bugs,
        "sessions": sessions,
        "files": files,
        "commits": commits,
        "next_step": nxt,
    }


def resume(store, project: dict, goal: str = "", vstore=None) -> dict:
    pid = project["id"]
    root = project.get("root_path")
    git_state = {
        "branch": gitutil.current_branch(root) if root else None,
        "head": gitutil.head_sha(root) if root else None,
        "dirty": gitutil.dirty_files(root) if root else [],
    }

    dirty = git_state["dirty"]
    all_wis = store.project_work_items(pid)
    if not all_wis:
        return {"mode": EMPTY, "project": project, "git": git_state}

    if not goal.strip():
        chosen = _most_useful(all_wis)
        return {
            "mode": NO_GOAL, "project": project, "git": git_state,
            "bundle": _bundle_for(store, project, chosen, dirty=dirty), "alternatives": [],
        }

    matches = match_work_items(store, pid, goal, vstore=vstore)
    if not matches:
        return {
            "mode": COLD, "project": project, "git": git_state, "reason": "no_match",
            "alternatives": all_wis[:3],
        }

    # Gate on MATCH RELEVANCE (how well the item answers the goal), not the item's
    # intrinsic confidence. Confidence stays available as a quality signal in the
    # bundle, but it must not turn a relevance-1.0 top hit into a COLD resume.
    r1 = matches[0].get("relevance") or 0.0
    r2 = (matches[1].get("relevance") or 0.0) if len(matches) > 1 else 0.0

    if r1 < config.MATCH_WEAK:
        # a match surfaced but it is too weak to assert as the answer
        return {
            "mode": COLD, "project": project, "git": git_state, "reason": "low_relevance",
            "bundle": _bundle_for(store, project, matches[0], dirty=dirty),
            "alternatives": matches[1:3],
        }

    if r1 >= config.MATCH_STRONG and (r1 - r2) >= config.RESUME_MARGIN:
        return {
            "mode": CONFIDENT, "project": project, "git": git_state,
            "bundle": _bundle_for(store, project, matches[0], dirty=dirty), "alternatives": [],
        }

    # ambiguous: never collapse - show the top pick's bundle PLUS the alternatives
    return {
        "mode": AMBIGUOUS, "project": project, "git": git_state,
        "bundle": _bundle_for(store, project, matches[0], dirty=dirty),
        "alternatives": matches[1:3],
    }


def _most_useful(wis):
    """Pick the WorkItem most worth resuming when no goal is given.

    A resumable item has actual content (files to continue). Prefer content,
    then active lifecycle, then recency - so we never surface an empty "Untitled
    work" item over a content-rich one just because it was touched last."""
    def has_files(w):
        try:
            return 1 if json.loads(w.get("files") or "[]") else 0
        except (json.JSONDecodeError, TypeError):
            return 0

    def key(w):
        active = 1 if (w.get("lifecycle") == "active") else 0
        return (has_files(w), active, w.get("last_active") or "", w.get("confidence") or 0.0)
    return sorted(wis, key=key, reverse=True)[0]
