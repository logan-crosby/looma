"""Hybrid lexical retrieval for `looma ask` (ARCHITECTURE.md 9, FTS5-backed).

Searches validated memories (entities) and WorkItems; falls back to message
snippets. Semantic retrieval is stubbed (NullVectorStore), so this is FTS-only
for the slice - every result still carries provenance + confidence + band.
"""

from .. import config
from ..sanitize import looks_like_code
from .match import fts_query

# Relevance dominates ranking; confidence is a light tie-breaker. Ranking purely
# by confidence (the old behaviour) let an unrelated conf-0.25 bug outrank a
# precise conf-0.0 decision (Phase 1 evaluation).
_W_REL = 0.75
_W_CONF = 0.25


def _rel_from_rank(i: int) -> float:
    """Map a 0-based bm25 position to a 0-1 relevance (1.0, 0.5, 0.33, ...)."""
    return 1.0 / (1 + i)


def ask(store, project_id: int, query: str, limit: int = 8, vstore=None) -> list[dict]:
    q = fts_query(query)
    results: list[dict] = []
    seen_ent: set[int] = set()

    # semantic hits first (when a vector store is active) - catches vocabulary mismatch
    if vstore is not None and getattr(vstore, "available", False):
        for ref_id, vscore in vstore.search("entity", query, limit=limit):
            r = store.conn.execute(
                """SELECT e.kind, e.title, e.confidence, w.title AS wi_title
                   FROM entities e LEFT JOIN work_items w ON w.id=e.work_item_id
                   WHERE e.id=? AND e.project_id=?""", (ref_id, project_id)).fetchone()
            if r and not looks_like_code(r["title"]):
                seen_ent.add(ref_id)
                conf = r["confidence"] or 0.0
                results.append({"type": "memory", "kind": r["kind"], "title": r["title"],
                                "confidence": conf, "band": config.band(conf),
                                "work_item": r["wi_title"], "_rel": float(vscore)})
    if not q:
        return results[:limit]

    # validated memories
    try:
        rows = store.conn.execute(
            """SELECT e.id, e.kind, e.title, e.confidence, e.work_item_id,
                      w.title AS wi_title
               FROM fts_entities f
               JOIN entities e ON e.id = f.rowid
               LEFT JOIN work_items w ON w.id = e.work_item_id
               WHERE f.fts_entities MATCH ? AND e.project_id = ?
               ORDER BY bm25(fts_entities) LIMIT ?""",
            (q, project_id, limit),
        ).fetchall()
        for i, r in enumerate(rows):
            if r["id"] in seen_ent or looks_like_code(r["title"]):
                continue
            conf = r["confidence"] or 0.0
            results.append({
                "type": "memory", "kind": r["kind"], "title": r["title"],
                "confidence": conf, "band": config.band(conf),
                "work_item": r["wi_title"], "_rel": _rel_from_rank(i),
            })
    except Exception:
        pass

    # work items
    try:
        rows = store.conn.execute(
            """SELECT w.id, w.title, w.kind, w.confidence
               FROM fts_workitems f JOIN work_items w ON w.id = f.rowid
               WHERE f.fts_workitems MATCH ? AND w.project_id = ?
               ORDER BY bm25(fts_workitems) LIMIT ?""",
            (q, project_id, limit),
        ).fetchall()
        for i, r in enumerate(rows):
            conf = r["confidence"] or 0.0
            results.append({
                "type": "workitem", "kind": r["kind"], "title": r["title"],
                "confidence": conf, "band": config.band(conf), "work_item": r["title"],
                "_rel": _rel_from_rank(i),
            })
    except Exception:
        pass

    results.sort(key=lambda x: _W_REL * x.get("_rel", 0.0) + _W_CONF * x["confidence"], reverse=True)
    return results[:limit]
