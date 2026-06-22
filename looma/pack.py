"""`looma pack` - the minimal, confidence-aware context package for another agent.

The smallest grounded preamble that lets a fresh agent act as if it had read the
whole project history: what is in flight, what was decided, what is blocked, what
changed, and which files matter. Built entirely from already-derived
WorkItems / memories / commits (reuses `brief.build`) - no new extraction.

Three properties make it usable as a per-session prefix:
  - token-efficient: a hard token budget; lowest-value items are dropped first.
  - confidence-aware: decisions/risks are confidence-gated and ranked; work
    items carry their confidence so the consuming agent can weight them.
  - dense: one fact per line, no decoration, ASCII only - cheap to parse.
"""

import json

from . import brief as brief_mod
from .sanitize import looks_like_code
from .util import to_ascii

# rough token estimate - 1 token ~= 4 chars of English/code (good enough to
# budget against; we never need exact tokenizer parity here).
def est_tokens(text: str) -> int:
    return (len(text) + 3) // 4


def _files(wi) -> list:
    try:
        return json.loads(wi.get("files") or "[]")
    except (json.JSONDecodeError, TypeError):
        return []


def relevant_files(active_work: list, dirty: list, limit: int = 8) -> list:
    """Hot files for the work in flight: those touched by active items (weighted
    by how many active items touch them), with uncommitted files first."""
    weight: dict = {}
    for rank, w in enumerate(active_work):
        # files come straight from WorkItem.files (real tool-call paths) - no
        # prose filtering; earlier (more active) items weigh more
        for f in _files(w):
            weight[f] = weight.get(f, 0) + (len(active_work) - rank)
    dirty_set = set(dirty or [])
    ranked = sorted(weight.items(), key=lambda kv: (kv[0] in dirty_set, kv[1]), reverse=True)
    out = [f for f, _ in ranked]
    # surface any uncommitted file not already present
    for f in dirty or []:
        if f not in out:
            out.insert(0, f)
    return out[:limit]


def build(store, project: dict, min_conf: float = 0.0, vstore=None) -> dict:
    """Assemble the pack data. Reuses brief.build, then confidence-gates and adds
    the relevant-files set. Selection (token budget) happens in format_pack."""
    b = brief_mod.build(store, project, vstore=vstore)

    def gate(items):
        # keep prose facts at or above the confidence floor, preserving order
        return [it for it in items
                if (it.get("confidence") or 0.0) >= min_conf and not looks_like_code(it["title"])]

    # most-trustworthy, most-recent work first - so a token budget keeps signal
    active = sorted(
        b["active_work"],
        key=lambda w: (w.get("confidence") or 0.0, w.get("last_active") or ""),
        reverse=True,
    )[:5]
    dirty = (b.get("git") or {}).get("dirty") or []
    return {
        "project": project,
        "git": b["git"],
        "summary": b["summary"],
        "active_work": active,
        "decisions": gate(b["decisions"]),
        "blockers": gate(b["blockers"]),
        "risks": gate(b["risks"]),
        "commits": b["commits"],
        "relevant_files": relevant_files(active, dirty),
        "next_step": b["next_step"],
    }


# section render order = priority. The budget trimmer fills sections in this
# order and stops when the budget is exhausted, so the cheapest-to-drop context
# (recent commits, then risks) goes last.
def _sections(p: dict) -> list:
    s, git = p["summary"], p["git"]
    head = [f"LOOMA CONTEXT PACK: {p['project']['display_name']} ({p['project']['canonical_key']})"]
    meta = []
    if git.get("branch"):
        meta.append(f"branch {git['branch']}")
    if git.get("dirty"):
        meta.append(f"{len(git['dirty'])} uncommitted")
    meta.append(f"{s['sessions']} sessions")
    meta.append(f"{s['active']}/{s['work_items']} active")
    head.append("  " + " | ".join(meta))

    def conf(w):
        return f"[{(w.get('confidence') or 0.0):.2f}]"

    secs = [("", head)]  # always-included header
    if p["active_work"]:
        secs.append(("ACTIVE WORK", [f"  #{w['id']} {to_ascii(w['title'])} {conf(w)}"
                                     for w in p["active_work"]]))
    if p["next_step"]:
        secs.append(("NEXT", ["  " + to_ascii(p["next_step"])]))
    if p["decisions"]:
        secs.append(("DECISIONS", [f"  - {e['title']}" for e in p["decisions"]]))
    if p["blockers"]:
        secs.append(("BLOCKERS", [f"  [ ] {e['title']}" for e in p["blockers"]]))
    if p["relevant_files"]:
        secs.append(("RELEVANT FILES", ["  " + ", ".join(p["relevant_files"])]))
    if p["risks"]:
        secs.append(("RISKS", [f"  (!) {e['title']}" for e in p["risks"]]))
    if p["commits"]:
        secs.append(("RECENT CHANGES",
                     [f"  {(c['sha'] or '')[:9]} {to_ascii(c.get('message') or '')[:60]}"
                      for c in p["commits"][:4]]))
    return secs


def format_pack(p: dict, budget: int = 900) -> str:
    """Render the densest pack that fits `budget` tokens. Sections are filled in
    priority order; once the budget is hit, remaining sections are dropped (and
    noted), so the output is bounded no matter how large the project is."""
    secs = _sections(p)
    out, used, dropped = [], 0, []
    for title, body in secs:
        block = (("\n" + title + "\n") if title else "") + "\n".join(body)
        cost = est_tokens(block)
        if title and used + cost > budget and out:
            dropped.append(title)
            continue
        out.append(block)
        used += cost
    text = "".join(out).lstrip("\n")
    if dropped:
        text += f"\n\n(omitted to fit {budget}-token budget: {', '.join(dropped)})"
    return text
