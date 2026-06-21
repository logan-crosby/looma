# Implementation notes - Phase 1 slice + alpha hardening (real vs stubbed)

This is the narrow Claude-only vertical slice from the Phase 1 checklist, hardened
into a public alpha. It runs end to end on real history with no hosted API. Below is
an honest account of what is genuinely implemented versus heuristic or stubbed, plus
known limitations.

Verified at real scale: `looma init` + `looma ingest --once` ingested hundreds of
sessions and tens of thousands of messages across a dozen projects, producing
hundreds of WorkItems and promoted memories with real git-linked commits, and
answered `looma work` / `looma resume "auth"` inside a real repo. All 44 unit tests
pass. See `SAMPLE_OUTPUT.md` for representative output.

## Alpha hardening (added on top of the Phase 1 slice)

- **Packaging.** `pip install -e .` exposes the `looma` binary; pyproject carries
  name/description/MIT-license/python-version/classifiers/entrypoint.
- **First-run UX.** Friendly empty states; clear error when no Claude history
  exists; DB path always shown; ingest reports sessions/messages/projects/work-items.
- **New commands.** `looma doctor` (env diagnostics), `looma reset --confirm`
  (safe DB deletion), `ingest --limit N`, `ingest --project <path>`, `--verbose`
  timing on every command.
- **Performance.** Git SHA validation is cached two ways: an in-process `lru_cache`
  and a persistent `git_sha_cache` table (survives rebuilds). SHA candidates are
  only taken from git commands or recognizable git output, never arbitrary hex
  tokens in logs - this both speeds ingest and improved commit linkage (1 -> 33
  commits). `--limit 25` ingests in ~9s vs ~5 min for everything.
- **Safety/privacy.** `.gitignore` excludes the store; reset/doctor print the
  "transcripts stay local" guarantee and warn before deletion.

## Real (fully implemented)

- **Local-first storage.** SQLite system of record, schema = ARCHITECTURE.md 6.1
  (all Phase 1 tables; correction_ledger / correction_constraints /
  graph_health_snapshots are created and the confidence ledger-override hook reads
  the constraints table, but no command writes corrections yet). FTS5 for lexical
  retrieval. No third-party packages.
- **Claude Code adapter.** Discovers `~/.claude/projects/<encoded-cwd>/*.jsonl`,
  parses JSONL defensively (malformed lines skipped, never fatal), flattens
  text/tool_use/tool_result blocks, preserves `raw_json`, derives project root and
  branch from the records' own `cwd`/`gitBranch`. Idempotent on a content-hash
  `event_hash`.
- **Project identity.** git remote (normalized to `host/org/repo`) -> git root ->
  path, with aliases. Demonstrably resolved 6 distinct GitHub remotes from real
  cwds.
- **Deterministic extraction.** File paths from tool-call arguments (ground truth)
  validated under the repo root; commit SHAs from git commands validated with
  `git cat-file`; commands from Bash calls; commit->file links from `git show`.
- **Two-phase, idempotent pipeline.** `ingest_messages` (incremental, content-hash
  dedup) then `rebuild` (drops derived tables, regenerates everything from stored
  messages). `looma reprocess` = rebuild alone. Re-running is a no-op on messages
  and deterministic on the graph (proven by `test_rebuild_is_idempotent`).
- **WorkItem resolution.** Multi-signal clustering (ARCHITECTURE.md 4.4) with file
  overlap weighted highest, branch + label + alias terms; HIGH -> merge, mid ->
  separate + RELATED edge, low -> new. Sessions, files, commits, and promoted
  memories attach to WorkItems through the graph star (CONTRIBUTES_TO / MODIFIED_FOR
  / IMPLEMENTS / CONSTRAINS / BLOCKS / AFFECTS / PART_OF / RELATED).
- **Confidence (ARCHITECTURE.md 5.4).** Exact weighted formula
  (0.30 file + 0.25 commit + 0.20 session-breadth + 0.15 agent-breadth +
  0.10 temporal), clamped, with the ledger-override hook. Surfaced as `[conf 0.NN
  band]` in `work`, `resume`, and `ask`.
- **Promotion (ARCHITECTURE.md 5 / checklist H).** Promote on commit-link OR active
  WorkItem OR multi-session; single-session weak candidates stay in staging and
  never enter the graph. Promotion writes ValidatedMemory + the typed edge.
- **Resume with uncertainty (ARCHITECTURE.md 10.1).** WorkItem-first. Confident vs
  ambiguous vs cold decided on top-two confidences + margin; low-confidence and
  near-tie results are shown with explicit caveats and alternatives, never silently
  collapsed. Bundle includes project/branch/head, decisions, todos, bugs, recent
  sessions, commits, files, and an inferred next step.
- **Graph.** nodes/edges populated with the full v3 edge taxonomy and traversed by
  the resume engine (e.g. `work_item_sessions` / `work_item_commits` go through
  edges, not just FKs).

## Heuristic (works, but deliberately simple for Phase 1)

- **WorkItem titles + kinds** come from regex intent phrases ("implement/fix/
  refactor/... X") over sanitized user turns, falling back to a file-derived title
  ("Work in src/"). Good when a session has a clear instruction; generic otherwise.
- **Candidate memories** are pattern heuristics (decision / todo / bug /
  architecture cue words) over sanitized turns, with code/diff/markdown-instruction
  lines filtered out. This surfaces genuinely useful items (real TODOs, real
  "Vite SPA -> Next.js" architecture notes) but still lets some lint/log lines
  through as "bugs". This is the intended seam for the Phase 2 local-LLM extractor.
- **Injected-text sanitation** (`sanitize.py`) strips system-reminders, slash-
  command scaffolding, and skill boilerplate that Claude folds into user turns.
  Phrase-based, so it is best-effort, not exhaustive.

## Stubbed (behind an interface, swappable later)

- **Semantic / vector retrieval.** `VectorStore` is a `NullVectorStore` stub
  (`storage/vector_store.py`); `search()` returns empty so callers fall back to
  FTS5 deterministically. Per the checklist, sqlite-vec was not pulled in to keep
  the core dependency-free; implementing the interface is the only change needed.
  The WorkItem-resolution "embedding cosine" term is likewise approximated by
  lexical label similarity.

## Out of scope (by instruction)

Codex / Cursor / Gemini / OpenCode / Windsurf adapters; UI; MCP server; DuckDB;
Kuzu; the Human Correction Layer commands and Graph Health Metrics (their tables
exist; the write/compute paths are Phase 2-3).

## Known limitations / honest caveats

- **Ingest is git-bound.** First full ingest over the author's entire `~/.claude`
  took ~4:50 because of per-SHA `git cat-file` validation; restricting SHA scanning
  to git commands + an `lru_cache` cut a rebuild to ~48s. On a single project it is
  fast. Large-history users will want the incremental watcher (Phase 4).
- **Candidate precision is heuristic.** Expect some false-positive "bugs" from lint
  output and some generic titles. This is the deterministic-slice trade-off and is
  exactly what promotion + confidence are meant to down-rank, and what the Phase 2
  LLM extractor will replace.
- **Ephemeral temp-dir sessions** (work done in a system temp directory) show up as
  their own low-value projects; real per-repo use is clean. Filtering ephemeral
  roots is a later refinement.
- **One session maps to one WorkItem** in this slice (the dominant signal); the
  architecture allows many-to-many later.

## Run / test

```bash
cd looma
pip install -e .            # or run via `python3 -m looma`
looma doctor
looma init
looma ingest --once         # or --limit 25 for a fast taste
cd <a repo with Claude history> && looma resume "auth"
python3 -m unittest discover -s tests -t .   # 44 tests
```

Tests cover: idempotent ingestion, malformed-JSONL handling, project identity,
WorkItem creation/merge, confidence scoring, promotion rules, ambiguous resume,
CLI empty states, ingest `--limit`/`--project`, the SHA-validation cache, doctor,
and reset confirmation.
