# Looma v1 report

The v1 milestone for solo developers: ingest multiple agents, reconstruct active
work, answer questions, resume accurately, explain decisions, show history, stay
current, and feed external agents - while remaining local-first, git-anchored,
benchmarked, and confidence-aware. All seven phases are complete.

## Benchmark improvements

| Benchmark | Before | After | Command |
|-----------|--------|-------|---------|
| Extraction F1 (golden set) | heuristic **0.69** | local LLM **0.96** (precision 0.67 -> 1.00) | `looma benchmark --compare` |
| Retrieval recall@3 (vocab-mismatch) | FTS-only **0.62** | FTS+vectors **1.00** (MRR 0.54 -> 1.00) | `looma benchmark --retrieval` |
| Graph: unresolved RELATED (real data) | **158** | **3** | Phase 1 resolution fix |
| Graph: work items / avg size (real data) | 316 / 1.18 | 159 / **2.35** | Phase 1 resolution fix |

## Architecture changes (this milestone)

- **Phase 1 - resolution.** Added an agglomerative second pass that merges WorkItems
  with file-overlap >= 0.5 (the dominant under-merging cause: 145/158 RELATED pairs
  had file-Jaccard >= 0.7). RELATED is now reserved for moderate [0.2, 0.5) overlap.
- **Phase 2 - retrieval.** Real `SqliteVecStore` (sidecar `.vec` db) + a stdlib
  embedding client; `get_vector_store` activates only when sqlite-vec + a local embed
  server are present, else `NullVectorStore` -> FTS. Hybrid fusion wired into
  `resume`/`ask`. Zero-dependency mode preserved.
- **Phase 3 - timeline.** `looma timeline` orders a WorkItem's decisions, commits,
  bugs, and sessions by real timestamps.
- **Phase 4 - MCP.** `looma mcp`: stdlib JSON-RPC 2.0 over stdio; tools resume_work,
  ask, timeline, list_work, recall.
- **Phase 5 - adapters.** Codex + Cursor behind `SourceAdapter`; `ingest_messages`
  runs all detected adapters and reports per-source counts; project identity unchanged.
- **Phase 6 - daemon.** `looma daemon`: mtime-gated polling, incremental idempotent
  ingest, rebuild only on change; crash-safe.
- **Phase 7 - hardening.** Forward-compatible column migrations, health degradation
  warnings, docs.

## Supported agents

- **Claude Code** - `~/.claude/projects/*.jsonl`
- **Codex** - `~/.codex/sessions/**/rollout-*.jsonl`
- **Cursor** - `globalStorage/state.vscdb` (cursorDiskKV)

Sessions from any of these on the same repo (resolved by git remote / root / path)
merge into the same project and, when they touch the same files, the same WorkItems.

## Retrieval metrics

Hybrid graph + FTS5 + optional vectors. On the vocabulary-mismatch retrieval set,
adding semantic vectors lifts recall@3 from 0.62 to 1.00. Lexical FTS remains the
zero-dependency default and the fallback when no embedding server is present.

## Health metrics (real data, 12 projects)

```
conversion rate (promoted/candidates):  0.35
merge rate (multi-session work items):   0.06
false-positive rate (corrections/valid): 0.00
avg work item size (sessions/item):      2.35
orphan candidates:                       0
unresolved related items:                3
(no degradation warnings)
```

`looma status --health` also emits advisory warnings (fragmentation, over-merging,
under-merging, aggressive promotion, noisy extraction) before users feel them.

## Known limitations

- Default heuristic extraction is noisy on some transcripts; the local LLM extractor
  (auto-detected) fixes this but needs a local model server.
- Semantic vectors require sqlite-vec + a local embed server + a Python whose sqlite3
  supports loadable extensions (some pyenv builds do not; Homebrew/python.org do).
- Cursor `project_root` is best-effort; Codex/Cursor lack a stored git branch.
- WorkItem titles still come from the heuristic even when memories use the LLM.
- First full ingest of a large history is git-bound (cached; daemon keeps it warm).
- Gemini, Windsurf, OpenCode adapters not yet implemented.

## Recommended roadmap for v2

1. **LLM-route WorkItem titles** (benchmark showed kind-acc 0.60 -> 0.80) and add an
   LLM merge-judge for borderline resolution.
2. **Bundle a tiny embedding model** path or document a one-command embed-server setup
   so semantic retrieval is on by default where supported.
3. **Gemini / Windsurf / OpenCode adapters** (one per cycle, behind `SourceAdapter`).
4. **Cursor project resolution** via `workspace.json` linkage to remove "unknown" projects.
5. **Evidence spans for LLM memories** (parity with heuristic) for click-through trust.
6. **Packaged daemon** (launchd/systemd unit) for always-on freshness.
7. **Grow the golden sets** (more fixtures/domains) to keep benchmarks honest as
   extraction evolves.

---

Local-first. Git-anchored. Benchmarked. Confidence-aware. 72 tests.
