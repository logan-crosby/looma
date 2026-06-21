# Looma v1 readiness

Evaluation of the v1 milestone for solo developers. Verdict: **ready** - every v1
success criterion is met, with benchmarks, and the project stays local-first,
git-anchored, and confidence-aware.

## Success criteria

| Capability                          | Status | Evidence |
|-------------------------------------|--------|----------|
| Ingest multiple agents              | yes    | Claude + Codex + Cursor adapters; real data parsed (Codex 168 sessions, Cursor 131 composers); cross-agent merge test |
| Reconstruct active work             | yes    | WorkItem-first model; file-overlap merge (RELATED 158->3 on real data) |
| Answer project questions            | yes    | `looma ask` (FTS + vectors) |
| Resume work accurately              | yes    | `looma resume` with uncertainty handling |
| Explain decisions                   | yes    | promoted decision/architecture memories, in resume + `ask`/`recall` |
| Show project history                | yes    | `looma timeline` (time-ordered decisions/commits/bugs/sessions) |
| Stay updated continuously           | yes    | `looma daemon` (watch + incremental idempotent ingest) |
| Provide context to external agents  | yes    | `looma mcp` (stdio MCP server, 5 tools) |
| Local-first / git-anchored          | yes    | no cloud, no API keys; commits/files validated against git |
| Benchmarked / confidence-aware      | yes    | extraction + retrieval benchmarks; confidence everywhere |

## Install experience

- `pip install -e .` exposes `looma`; **zero third-party runtime dependencies**.
- `looma doctor` checks Python, FTS5, data dir, DB, Claude history, git, and the
  optional local model server.
- Optional accelerators are auto-detected and degrade cleanly: local LLM extractor
  (`LOOMA_EXTRACTOR=auto`), semantic vectors (sqlite-vec + local embed server). When
  absent, Looma runs fully on the stdlib heuristic + FTS5.

## Retrieval quality

- Hybrid: graph traversal + FTS5 + optional semantic vectors.
- Retrieval benchmark (vocabulary-mismatched queries): FTS-only recall@3 **0.62** ->
  FTS+vectors **1.00** (MRR 0.54 -> 1.00). Vectors solve vocabulary mismatch
  ("user authentication" -> "OAuth login flow") that lexical search misses.

## Benchmark results

- Extraction (golden set, P/R/F1): heuristic **F1 0.69** vs local LLM **F1 0.96**
  (precision 1.00). `looma benchmark --compare`.
- Retrieval: see above. `looma benchmark --retrieval`.

## Adapter coverage

- Claude Code (JSONL), Codex (rollout JSONL), Cursor (globalStorage vscdb). Behind
  one `SourceAdapter` interface; project identity is cwd-based and shared, so the
  same repo unifies across agents. Gemini/Windsurf/OpenCode deferred (roadmap).
- Known gaps: Cursor `project_root` is best-effort (only user bubbles carry
  `workspaceUris`); sessions without it fall to an "unknown" project. Codex/Cursor
  do not store a git branch (file overlap drives merging, so this is non-fatal).

## Correction reliability

- `looma correct merge|split|rename|promote|reject|false-positive|undo`, ledgered to
  `correction_ledger` + `correction_constraints`, anchored to stable keys (session-id
  sets / (kind, normalized title)) so they survive reprocessing.
- Tested: merge reduces+survives a second rebuild; rename pins; reject removes a
  promoted memory; undo restores. Corrections override automated inference.

## MCP usability

- `looma mcp`: JSON-RPC 2.0 over stdio, stdlib only. `initialize`, `tools/list`, and
  `tools/call` for `resume_work`, `ask`, `timeline`, `list_work`, `recall`. Tested
  end-to-end (protocol handshake + tool dispatch + graceful errors).

## Hardening

- Forward-compatible migrations (`ALTER ... ADD COLUMN` for pre-v1 DBs); idempotent.
- Recovery: `looma reprocess` rebuilds the graph from raw events + ledger;
  `looma reset --confirm` for a clean slate (transcripts untouched).
- Performance: persistent git-SHA cache; daemon mtime-gate keeps idle polls cheap.
- 72 tests pass (1 skipped where sqlite3 lacks loadable extensions).

## Residual risks

- Default heuristic extraction is noisy on some transcripts (the LLM extractor fixes
  this when a local model server is available).
- Large first ingest is git-bound (cached; `--limit` for demos; daemon keeps it warm).
- Semantic vectors need sqlite-vec + a local embed server and a Python whose sqlite3
  supports loadable extensions (Homebrew/python.org builds do; some pyenv builds do not).
