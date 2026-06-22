# Looma v2.0.0 - the agent context layer

Looma turns your coding-agent history (Claude Code, Codex, Cursor) into grounded,
resumable project context, fully locally. v2.0 repositions Looma as the default
context source another agent loads instead of re-reading the raw transcript - and
backs that with a sharper extractor, clean project identities, and cheaper
retrieval.

## New

- **`looma pack`** - the minimal, confidence-aware context package for an agent:
  active work, decisions, blockers, relevant files, and recent changes. It is
  token-budgeted and roughly 2985x lighter than the raw transcript (bounded under
  ~900 tokens for any repo), so it is cheap enough to prepend to every session.
  Available over MCP.
- **`looma inspect`** - understand a repository without reading its transcripts:
  architecture summary, active systems, ownership clusters, risks, and recent
  change hotspots. Available over MCP.

## Improved

- **Extraction quality.** Synthetic/programmatic sessions (memory-log
  summarizers, compression jobs) are no longer treated as real work. Bug
  classification now requires an explicit problem assertion instead of any
  mention of "fix" or "error". Decision and architecture capture is broader, and
  memory confidence is calibrated to the work it documents. On a real
  615-session corpus: untitled work fell 45% to 13%, the bug share of memories
  fell 79% to 38%, named work items rose 34% to 56%. Benchmark memory F1 went
  0.69 to 0.90.
- **Project identity.** Temp directories, scratch paths, config homes, and
  session-id placeholders no longer become projects. Every session now resolves
  to a real repository or one clearly labeled "Unsorted" bucket per agent.
  Project count dropped from 72 to 24 with no real repo lost.
- **MCP retrieval.** `ask` now matches inflected queries (it previously returned
  nothing for terms like "extraction" or "migration"), and the detail tools are
  output-bounded. Every MCP tool stays under ~900 tokens; the per-turn tools
  average well under 350.

## Validated

- Cross-agent corroboration works: a work item independently touched by two
  agents scored 4.6x the confidence of single-agent work.

## Notes

- Fully local. No cloud, no network, no telemetry, zero runtime dependencies
  (Python standard library plus optional sqlite-vec for semantic search).
- 103 tests passing.
- MCP server (`looma mcp`) now exposes 11 tools: today, weekly, resume_work,
  brief, pack, inspect, ask, timeline, explain, list_work, recall.

Full details in CHANGELOG.md and the V2 reports (LOOMA_V2_REPORT.md,
LOOMA_V2_READINESS.md).
