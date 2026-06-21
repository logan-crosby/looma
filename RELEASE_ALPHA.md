# Looma - public alpha (v0.1.0a1)

Looma turns your Claude Code history into resumable, git-anchored project context -
**WorkItem-centered** and entirely on your machine. Local-first project memory: no
cloud, no API keys.

## What works

- **One-command setup and ingest.** `looma init` then `looma ingest --once`
  indexes your Claude Code transcripts into a local SQLite store. Verified on real
  history at scale (hundreds of sessions across a dozen projects).
- **WorkItem-first model.** Sessions, files, commits, decisions, todos, and bugs
  are organized around WorkItems (a feature, bugfix, refactor, migration, or
  investigation), not raw chat lines.
- **Git-anchored ground truth.** File paths come from tool calls; commit SHAs are
  validated against the repo (`git cat-file`) and cached persistently. WorkItems
  link to real branches and commits.
- **Confidence on everything.** Every WorkItem and memory carries a `conf 0.NN
  (band)` derived from file overlap, commit linkage, multi-session, multi-agent,
  and temporal persistence.
- **Trustworthy resume.** `looma resume "<goal>"` reconstructs project context and
  is honest about uncertainty: a low-confidence or near-tie match is shown as a
  starting point with alternatives, never silently collapsed into one answer.
- **First-run UX.** Friendly empty states, clear errors when there is no Claude
  history, the DB path is always shown, and counts are reported after ingest.
- **Safety tooling.** `looma doctor` checks the environment; `looma reset` requires
  `--confirm`; `.gitignore` keeps the store out of version control.
- **Fully local.** No hosted API, no cloud, no API key. Standard-library Python +
  SQLite/FTS5; zero third-party dependencies.

## What is heuristic (deliberately, for the alpha)

- **WorkItem titles and kinds** are derived from regex intent phrases over
  sanitized user turns, falling back to file-derived names ("Work in src/").
- **Candidate memories** come from cue-word heuristics (decision / todo / bug /
  architecture) with code, diff, log, and injected-skill text filtered out. This
  surfaces genuinely useful items (real TODOs, real architecture notes) but still
  lets the occasional lint/log line through. This is the seam the planned local-LLM
  extractor replaces.
- **WorkItem-resolution similarity** uses lexical label overlap in place of
  embeddings (the embedding term is stubbed for the alpha).

## Known limitations

- **Claude Code only.** Other agents (Codex, Cursor, Gemini, OpenCode, Windsurf)
  are designed (see ARCHITECTURE.md) but not yet implemented.
- **Full ingest is git-bound.** The first sweep of a large `~/.claude` can take a
  few minutes (per-SHA git validation, now cached). `--limit N` and
  `--project <path>` make demos fast (~9s for 25 sessions).
- **Heuristic precision.** Expect some generic titles and false-positive "bugs"
  until the LLM extractor lands; confidence + promotion down-rank them.
- **No vector search yet.** Retrieval is FTS5 + graph; the `VectorStore` interface
  is stubbed.
- **Single store, single machine.** No sync, no UI, no MCP server yet.

## Next milestones

1. **Local-LLM extractor** (Phase 2): replace heuristic title/candidate extraction
   for far higher precision; keep it local (Ollama/llama.cpp).
2. **sqlite-vec** behind the existing `VectorStore` interface for semantic recall.
3. **Human Correction Layer + Ledger** commands (merge/split/rename/promote/reject)
   - the tables already exist; wire the CLI and the constraint-aware rebuild.
4. **Graph Health Metrics** (`looma status --health`).
5. **More adapters** (Codex, Cursor/Windsurf, Gemini, OpenCode), then the MCP server
   so any agent can pull resume bundles.

## Try it in 5 minutes

```bash
pip install -e .
looma doctor                 # verify your environment
looma init
looma ingest --once --limit 25   # fast first taste; drop --limit for everything
cd <a repo with Claude history>
looma work
looma resume "auth"
```

See `README.md` for the full quickstart, `SAMPLE_OUTPUT.md` for real output, and
`IMPLEMENTATION_NOTES.md` for the real-vs-stubbed breakdown.
