# Changelog

All notable changes to Looma are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); this project uses pre-1.0 alpha
versions.

## [1.6.0] - 2026-06-21

The daily loop. Driven by a usage analysis (DAILY_USAGE_REPORT.md); product-fit
summary in LOOMA_PRODUCT_FIT_REPORT.md.

### Added
- **`looma today`** (and bare `looma`) - the daily driver: what you're working on,
  what changed recently (sessions + commits + working tree), what's blocked, what
  to do next, plus the other repos you touched recently with their next step.
  Benchmarked at 0.89/4 daily completeness vs resume 0.55 / brief 0.61.
- **`looma weekly`** - cross-project retrospective: worked on, shipped (commits),
  decisions, unresolved blockers. Understand your week in under 2 minutes.
- MCP `today` and `weekly` tools (9 tools total).

### Changed
- **Bare `looma` runs `today`** - the daily habit costs zero keystrokes beyond
  the binary name.
- **`init` is now optional** - every command auto-creates and migrates the store,
  so a brand-new machine works without it.
- `doctor` ends with a concrete next step; the empty daily view shows a quickstart;
  first ingest prints a progress hint with a `--limit` fast-path.
- MCP tool output is ASCII-folded centrally (no transcript emoji/smart-quotes in
  another agent's context).

### Fixed
- `dirty_files` truncated every modified path by one character ("looma/cli.py" ->
  "ooma/cli.py") because the porcelain status field's leading space was stripped.
  Fixed with a NUL-delimited parse. This corrupted "what changed" everywhere.
- `looks_like_code` now also drops diff hunks (@@) and comment/heading lines.

## [1.5.0] - 2026-06-21

Refinement cycle: make Looma feel indispensable. Driven by a real-corpus
evaluation (REAL_WORLD_EVALUATION.md). See LOOMA_V1_5_REPORT.md.

### Added
- **`looma brief`** - 60-second project orientation (summary, active work, recent
  decisions, current risks, open blockers, recent commits, suggested next work).
- **`looma explain <work>`** - why a WorkItem exists, how it evolved, which
  decisions shaped it, what changed. MCP `brief` + `explain` tools too.

### Changed
- **Resume gates on match relevance**, not intrinsic confidence (solo-dev work no
  longer goes COLD on a perfect match). Matching now scores file paths + linked
  memories; real next-step inference; no-goal resume picks the most resumable
  item. goal-match MRR 0.67 -> 1.00; COLD-on-true-match 4/6 -> 0/6; next-step
  real-rate 0.54 -> 0.72.
- **WorkItem titles**: intent extraction rejects code/SQL/JSX; "Work on <salient
  segment>" replaces "Work in <dir>/". Garbage titles 15 -> 0; dir titles 80+ -> 0.
- **Lifecycle**: a single substantive session is now `active`. Active rate
  11% -> 46%.
- **Incremental rebuild**: daemon re-derives only changed repos (one-project
  rebuild 3.1s vs ~85s full, ~27x).
- **`ask`** ranks by coverage-weighted relevance blended with confidence.
- Code/diff-line memories filtered from resume/brief/explain; non-ASCII folded.

### Fixed
- Crash in `deterministic.session_artifacts` when `project_root` is None
  (rootless/unknown projects) - the real cause of the original ingest rc=1. Full
  corpus now rebuilds cleanly (277 -> 325 work items).

## [1.0.0] - 2026-06-21

First "complete v1" milestone for solo developers. See LOOMA_V1_REPORT.md.

### Added (v1 milestone)
- **Multi-agent ingestion**: Codex + Cursor adapters alongside Claude Code; sessions
  merge across agents on the same repo. Per-source ingest reporting.
- **Hybrid retrieval**: optional sqlite-vec semantic vectors fused with FTS + graph
  (FTS stays the zero-dependency default). Retrieval recall@3 0.62 -> 1.00.
- **Resolution fix**: agglomerative file-overlap merge - unresolved RELATED 158 -> 3,
  work items 316 -> 159 on real data.
- `looma timeline` (WorkItem evolution), `looma mcp` (stdlib MCP server),
  `looma daemon` (auto-stay-current), `looma status --health` degradation warnings,
  `looma benchmark --retrieval`.
- Forward-compatible column migrations for pre-v1 databases.

### Earlier in this line: extraction quality, trust, and evaluation

### Added
- **Auto-detected local LLM extraction.** `LOOMA_EXTRACTOR=auto` (now the default)
  detects a reachable local model server and uses the LLM extractor, else falls back
  to the stdlib heuristic - so the LLM is the best-supported path when available while
  the zero-dependency default is preserved (local HTTP over stdlib urllib, no new dep).
  `looma doctor` reports the model server; `ingest`/`reprocess` report which extractor ran.
- **Evaluation system.** `looma benchmark` and `looma benchmark --compare` report
  precision/recall/F1 for extraction over a golden fixture set.
- **Extractor interface** with `HeuristicExtractor` (default) and a fully-local
  `LocalLLMExtractor` (llama.cpp/Ollama, no hosted API), opt-in via `LOOMA_EXTRACTOR=llm`,
  with per-session fallback to the heuristic.
- **Human Correction Layer:** `looma correct merge|split|rename|promote|reject|
  false-positive|undo|log`. Corrections are ledgered, replayable, override automated
  inference, and survive deterministic rebuilds (anchored to stable keys).
- **Graph health metrics:** `looma status --health` (conversion rate, merge rate,
  false-positive rate, avg work item size, orphan candidates, unresolved related items).

### Benchmark
- Local LLM extractor (Qwen2.5-7B Q3_K_M) beats the heuristic on the golden set:
  **F1 0.96 vs 0.69** (precision 1.00 vs 0.67), so it is kept as an opt-in upgrade.

### Tests
- 53 tests (was 44): benchmark scoring, corrections (merge/rename/reject/undo with
  replay), health metrics.

## [0.1.0-alpha.1] - 2026-06-21

First public alpha.

### What Looma does

Looma turns coding-agent history into **resumable project context**. Instead of
searching transcripts, it reconstructs the active work, decisions, blockers,
commits, files in flight, and next likely steps - organized around WorkItems and
anchored to git. Local-first: no cloud, no API keys, no telemetry.

### Added (works today)

- Claude Code history ingestion (`~/.claude/projects/*.jsonl`), idempotent on a
  content hash, defensive against malformed lines.
- Project identity resolution (git remote -> git root -> path) as a cross-agent key.
- Deterministic extraction of files, commits (git-validated), and commands.
- WorkItem generation and multi-signal resolution (feature / bugfix / refactor /
  migration / investigation).
- Heuristic candidate-memory extraction (decisions, todos, bugs, architecture).
- Confidence scoring (file overlap, commit linkage, multi-session, multi-agent,
  temporal persistence), surfaced in every command.
- Promotion of corroborated candidates into validated, graph-linked memory.
- WorkItem-first `resume` with explicit uncertainty handling (confident /
  ambiguous / low-confidence), never silently collapsing weak matches.
- CLI: `init`, `ingest` (`--once`, `--limit N`, `--project <path>`), `work`,
  `resume`, `ask`, `status`, `doctor`, `reset --confirm`, `reprocess`, `--verbose`.
- Local SQLite storage with FTS5 lexical retrieval; persistent git-SHA cache.
- 44 unit tests.

### Known limitations

- **Claude Code only.** Other agents are designed but not yet implemented.
- **Extraction is heuristic.** WorkItem titles and candidate memories use regex/
  cue-word heuristics; expect occasional generic titles or false-positive "bugs".
  Confidence + promotion down-rank them; a local-LLM extractor is the next milestone.
- **No semantic search yet.** Retrieval is FTS5 + graph; the `VectorStore` is stubbed.
- **No UI, no MCP server, single local store.**
- First full ingest of a large history is git-bound (cached; `--limit` for demos).

### Roadmap

Local-LLM extraction engine, benchmark framework, cross-agent adapters (Codex,
Cursor, Gemini, Windsurf, OpenCode), MCP integration, timeline views, human
correction workflows, graph health metrics, semantic retrieval, local UI.

[0.1.0-alpha.1]: https://github.com/devYRPauli/looma/releases/tag/v0.1.0-alpha.1
