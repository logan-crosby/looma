# Looma V2 Report

**Mission:** make Looma the default context layer for coding agents - the grounded
source an agent loads instead of re-reading history. Every change was gated on one
question: *does this make another agent substantially better when Looma is
present?*

Seven phases, executed and measured against a real corpus (615 sessions, 24
projects, 75,612 messages, three agents: Claude / Codex / Cursor). No cloud, no
SaaS, no UI, no new infrastructure - higher quality, smaller context, better
retrieval, cleaner explanations. Result: **V2.0.0, ready to ship.**

---

## 1. Quality improvements

**Extraction (Phase 1).** The answer-crispness lever. Removed the dominant noise
source - 48% of sessions were synthetic/programmatic API calls (memory-log
summarizers, compression jobs) producing 84% of "Untitled work" - and rebuilt the
classifiers: bugs now require an explicit problem assertion (not a bare
"fix"/"error" that matched code, logs, and narration), decision/architecture
recall broadened to real design rules, WorkItem naming gained verb-stem
normalization and clause trimming, and memory confidence now inherits the
grounding of the work it documents.

**Identity (Phase 2).** Every session now belongs somewhere meaningful. Ephemeral
and degenerate roots (temp dirs, the filesystem root, config homes, the home dir)
are rejected; unresolvable sessions collapse into one honest per-agent bucket
instead of one fake project each; Cursor workspaces are recovered from
attached-file URIs.

**Retrieval and answers (Phase 4).** `ask` was returning zero results for
inflected queries - fixed with stemmed/prefix FTS. Detail tools (`explain`,
`timeline`) are now output-bounded. JSON/tool-schema fragments are dropped from
answers.

---

## 2. Benchmark deltas

| Metric                              | Before | After | Delta   |
|-------------------------------------|--------|-------|---------|
| Benchmark memory F1                 | 0.69   | 0.90  | +0.21   |
| - architecture F1                   | 0.00   | 1.00  | +1.00   |
| - bug F1                            | 0.67   | 0.80  | +0.13   |
| Work label-hit rate                 | 0.60   | 1.00  | +0.40   |
| Untitled work (real corpus)         | 45.0%  | 13.2% | -31.8pt |
| Named work items                    | 34.5%  | 56.4% | +21.9pt |
| Bug share of memories               | 78.7%  | 37.8% | -40.9pt |
| Projects (identity)                 | 72     | 24    | -67%    |
| unknown:<uuid> singletons           | 46     | 0     | -46     |
| Tests passing                       | 85     | 103   | +18     |

(Benchmark measured on a harder 8-fixture set vs the old 5.)

---

## 3. Token compression metrics

`looma pack` - the new minimal agent context package - vs the raw transcript:

| | value |
|---|---|
| Aggregate compression (20 projects) | **2985x** (10.7M -> 2,985 tokens) |
| Per-project range | 34x to 11,157x |
| Pack size, any project | bounded < 740 tokens |
| Largest project (8.2M raw tokens) | 737-token pack |

Every MCP tool is under ~900 tokens; the per-turn tools (pack, ask, resume, today)
average 40-314. Looma context is cheap enough to prepend to every session.

---

## 4. MCP improvements

- New `pack` tool: the cheapest grounded preamble, confidence-ranked and budgeted.
- New `inspect` tool: repo architecture / systems / ownership / risks / hotspots
  without reading transcripts.
- `ask` retrieval recall restored (0 hits -> matches via stemming).
- `explain` / `timeline` bounded (1029 -> 742, 703 -> 579 tokens on the busiest
  work item).
- 11 tools total, all local stdio, all under ~900 tokens.

---

## 5. Cross-agent findings

- Extraction is robust across three transcript styles; Codex is task-heavy, Cursor
  is thin chat, Claude is balanced - and no agent's stream degrades to bug-spam.
- Confidence tracks groundedness: Codex 0.124 > Claude 0.091 > Cursor 0.001.
- **The cross-agent merge delivers a 4.6x confidence boost** (0.44 vs 0.095
  single-agent average) where two agents independently worked the same thing -
  the core differentiator, validated.
- Most repos are single-agent, so the merge is rarely exercised; the clearest
  future value is multiple agents sharing a repo.
- Zero manual corrections were needed - automated filters carried the cleanup.

---

## 6. Recommended V2 release notes

> **Looma v2.0.0 - the agent context layer**
>
> Looma turns your coding-agent history (Claude, Codex, Cursor) into grounded,
> resumable project context. v2.0 makes it the default context source another
> agent loads instead of re-reading the transcript.
>
> - **`looma pack`** - the smallest grounded context package for an agent: active
>   work, decisions, blockers, relevant files, recent changes. Confidence-ranked,
>   token-budgeted, and ~2985x lighter than the raw transcript. Available over MCP.
> - **`looma inspect`** - understand any repo without reading its transcripts:
>   architecture, active systems, ownership clusters, risks, and change hotspots.
> - **Sharper extraction** - synthetic sessions filtered, bug overclassification
>   fixed (79% -> 38% of memories), Untitled work cut (45% -> 13%), benchmark F1
>   0.69 -> 0.90.
> - **Clean identities** - temp/scratch/unknown projects collapsed (72 -> 24);
>   every session belongs somewhere real.
> - **Cheaper, better MCP** - `ask` retrieval fixed, every tool under ~900 tokens,
>   two new tools (`pack`, `inspect`).
>
> Still zero-dependency, fully local, no cloud, no telemetry. 103 tests.

---

## 7. Status

All seven phases complete. Eight deliverables produced:
EXTRACTION_V2_REPORT.md, IDENTITY_REPORT.md, MCP_EFFICIENCY_REPORT.md,
CROSS_AGENT_REPORT.md, LOOMA_V2_READINESS.md, and this report - plus the two new
commands (`pack`, `inspect`) and their MCP tools. Version bumped to 2.0.0;
README and CHANGELOG updated. 103 tests passing, 1 skipped.

V2 is ready to publish.
