"""Graph health metrics (ARCHITECTURE.md 15, goal Phase D).

Read-only over existing tables. Surfaced by `looma status --health` so degradation
is visible before users feel it.
"""


def compute(store) -> dict:
    c = store.conn

    def one(sql, *p):
        return c.execute(sql, p).fetchone()[0]

    total_cand = one("SELECT COUNT(*) FROM candidate_memories")
    promoted = one("SELECT COUNT(*) FROM candidate_memories WHERE state='promoted'")
    validated = one("SELECT COUNT(*) FROM entities")
    work_items = one("SELECT COUNT(*) FROM work_items")
    contrib = one("SELECT COUNT(*) FROM edges WHERE rel='CONTRIBUTES_TO'")
    multi = one("""SELECT COUNT(*) FROM (SELECT dst_node FROM edges WHERE rel='CONTRIBUTES_TO'
                   GROUP BY dst_node HAVING COUNT(*) >= 2)""")
    orphans = one("SELECT COUNT(*) FROM candidate_memories WHERE work_item_id IS NULL")
    related = one("SELECT COUNT(*) FROM edges WHERE rel='RELATED'")
    fp = one("""SELECT COUNT(*) FROM correction_ledger
                WHERE action_type IN ('false_positive','reject')""")

    def ratio(a, b):
        return round(a / b, 3) if b else 0.0

    return {
        "conversion_rate": ratio(promoted, total_cand),
        "merge_rate": ratio(multi, work_items),
        "false_positive_rate": ratio(fp, validated),
        "avg_work_item_size": ratio(contrib, work_items),
        "orphan_candidates": orphans,
        "unresolved_related_items": related,
        "_raw": {"candidates": total_cand, "promoted": promoted, "validated": validated,
                 "work_items": work_items},
    }


def warnings(h: dict) -> list[str]:
    """Advisory degradation signals (early warning before users feel it)."""
    out = []
    wi = (h.get("_raw") or {}).get("work_items", 0)
    cand = (h.get("_raw") or {}).get("candidates", 0)
    if wi and h["avg_work_item_size"] < 1.2:
        out.append("fragmentation: work items rarely span multiple sessions")
    if h["avg_work_item_size"] > 10:
        out.append("possible over-merging: very large average work item size")
    if h["false_positive_rate"] > 0.2:
        out.append("high correction rate: promotion may be too aggressive")
    if wi and h["unresolved_related_items"] > max(10, wi * 0.5):
        out.append("many unresolved RELATED links: resolution may be under-merging")
    if cand > 20 and h["conversion_rate"] < 0.1:
        out.append("low promotion: extraction may be noisy (try the local LLM extractor)")
    return out


def format_health(h: dict) -> str:
    lines = [
        "graph health",
        f"  conversion rate (promoted/candidates):  {h['conversion_rate']:.2f}",
        f"  merge rate (multi-session work items):   {h['merge_rate']:.2f}",
        f"  false-positive rate (corrections/valid): {h['false_positive_rate']:.2f}",
        f"  avg work item size (sessions/item):      {h['avg_work_item_size']:.2f}",
        f"  orphan candidates:                       {h['orphan_candidates']}",
        f"  unresolved related items:                {h['unresolved_related_items']}",
    ]
    warns = warnings(h)
    if warns:
        lines.append("  warnings:")
        lines.extend(f"    - {w}" for w in warns)
    else:
        lines.append("  (no degradation warnings)")
    return "\n".join(lines)
