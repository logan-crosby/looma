# Changelog

All notable changes to Looma are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); this project uses pre-1.0 alpha
versions.

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
