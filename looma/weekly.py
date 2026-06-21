"""`looma weekly` - the week in under two minutes.

A cross-project retrospective over a recency window: what you worked on, what
shipped (commits), the decisions you made, and what is still blocked - grouped by
repo. Built from existing WorkItems / memories / commits; adds nothing new.
"""

from datetime import datetime, timedelta

from .sanitize import looks_like_code
from .util import to_ascii


def _window_start(store, days):
    mx = store.conn.execute("SELECT MAX(ended_at) FROM sessions").fetchone()[0]
    if not mx:
        return None, None
    end = mx[:19]
    start = (datetime.fromisoformat(end) - timedelta(days=days)).isoformat()
    return start, end[:10]


def _active_projects(store, since):
    rows = store.conn.execute(
        """SELECT p.id, p.canonical_key, p.display_name, MAX(se.ended_at) last_active,
                  COUNT(se.id) n
           FROM sessions se JOIN projects p ON p.id=se.project_id
           WHERE se.ended_at>=? AND p.canonical_key NOT LIKE 'unknown:%'
           GROUP BY p.id ORDER BY last_active DESC""",
        (since,),
    ).fetchall()
    return [dict(r) for r in rows]


def _clean_titles(rows, limit, drop_resolved=False):
    import re
    resolved = re.compile(r"(?i)^\s*(?:i\s+)?(?:fixed|resolved|implemented|done)\b")
    out, seen = [], set()
    for r in rows:
        t = to_ascii((r["title"] or "").strip())
        k = t.lower()
        if not t or k in seen or looks_like_code(t):
            continue
        if drop_resolved and resolved.search(t):
            continue
        seen.add(k)
        d = dict(r)
        d["title"] = t
        out.append(d)
        if len(out) >= limit:
            break
    return out


def build(store, days=7, vstore=None) -> dict:
    since, end = _window_start(store, days)
    if since is None:
        return {"empty": True, "days": days}
    projects = _active_projects(store, since)

    per_project = []
    all_commits = []
    all_decisions = []
    all_blockers = []
    for p in projects:
        pid = p["id"]
        commits = [dict(r) for r in store.conn.execute(
            "SELECT sha, message, ts FROM commits WHERE project_id=? AND ts>=? ORDER BY ts DESC",
            (pid, since)).fetchall()]
        # work items touched in the window
        touched = [w for w in store.project_work_items(pid)
                   if (w.get("last_active") or "") >= since]
        decisions = _clean_titles(store.conn.execute(
            """SELECT e.title FROM entities e JOIN work_items w ON w.id=e.work_item_id
               WHERE e.project_id=? AND e.kind IN ('decision','architecture')
                 AND w.last_active>=? ORDER BY w.last_active DESC""", (pid, since)).fetchall(), 4)
        blockers = _clean_titles(store.conn.execute(
            """SELECT e.title FROM entities e JOIN work_items w ON w.id=e.work_item_id
               WHERE e.project_id=? AND e.kind IN ('todo','bug') AND e.status='open'
                 AND w.last_active>=? ORDER BY w.last_active DESC""", (pid, since)).fetchall(),
            4, drop_resolved=True)
        per_project.append({
            "project": p, "commits": commits, "touched": touched,
            "decisions": decisions, "blockers": blockers,
        })
        for c in commits:
            all_commits.append({**c, "project": p["display_name"]})
        for d in decisions:
            all_decisions.append({**d, "project": p["display_name"]})
        for b in blockers:
            all_blockers.append({**b, "project": p["display_name"]})

    return {
        "empty": False, "days": days, "since": since[:10], "end": end,
        "projects": projects, "per_project": per_project,
        "commits": all_commits, "decisions": all_decisions, "blockers": all_blockers,
    }


def format_weekly(w: dict) -> str:
    if w.get("empty"):
        return f"LOOMA WEEKLY - no activity in the last {w['days']} days (run `looma ingest --once`)."
    L = []
    L.append(f"LOOMA WEEKLY - {w['since']} to {w['end']} ({w['days']} days)")
    L.append(f"  {len(w['projects'])} repos active | {len(w['commits'])} commits | "
             f"{len(w['decisions'])} decisions | {len(w['blockers'])} open blockers")

    L.append("\nWORKED ON")
    for pp in w["per_project"][:8]:
        p = pp["project"]
        n_touched = len(pp["touched"])
        bits = f"{p['n']} sessions"
        if pp["commits"]:
            bits += f", {len(pp['commits'])} commits"
        if n_touched:
            bits += f", {n_touched} work items"
        L.append(f"  {p['display_name']}: {bits}")

    L.append("\nSHIPPED (commits)")
    if w["commits"]:
        for c in w["commits"][:12]:
            L.append(f"  [{c['project'][:14]:14}] {(c['sha'] or '')[:9]} {to_ascii(c.get('message') or '')[:52]}")
    else:
        L.append("  (no commits linked in window)")

    L.append("\nDECISIONS")
    if w["decisions"]:
        for d in w["decisions"][:8]:
            L.append(f"  [{d['project'][:14]:14}] {d['title'][:64]}")
    else:
        L.append("  (none captured)")

    L.append("\nUNRESOLVED BLOCKERS")
    if w["blockers"]:
        for b in w["blockers"][:10]:
            L.append(f"  [{b['project'][:14]:14}] {b['title'][:64]}")
    else:
        L.append("  (none)")
    return "\n".join(L)
