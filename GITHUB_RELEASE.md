# GitHub repository metadata + release copy

Everything needed to set up the repo and publish the v0.1.0-alpha.1 release.

## Repository metadata

**Repository name:** `looma`

**Short description (the GitHub "About" field):**

> Looma turns coding-agent history into resumable project context.

**Longer description (README hook / social):**

> Local-first project memory for coding agents. From your Claude Code history,
> Looma reconstructs the active work, decisions, blockers, commits, and files in
> flight - so you can pick up exactly where you left off. No cloud, no API keys.

**Topics / tags:**

```
claude-code
developer-tools
local-first
sqlite
productivity
git
agent-memory
python
```

**Social preview text (for the GitHub social image / link unfurl):**

> Looma - resumable project context from your coding-agent history. Local-first,
> git-anchored, no API keys. `looma resume "auth"`.

**Website field:** (leave blank for now, or link the README anchor)

## GitHub Release - copy/paste

**Tag:** `v0.1.0-alpha.1`  (mark as **pre-release**)

**Release title:** `Looma v0.1.0-alpha.1 - first public alpha`

**Release body:**

---

**Looma turns coding-agent history into resumable project context.**

Instead of searching transcripts, Looma reconstructs the active work, decisions,
blockers, commits, files in flight, and next likely steps - organized around
WorkItems and anchored to git. It runs entirely on your machine: no cloud, no API
keys, no telemetry.

```bash
pip install -e .
looma doctor
looma init
looma ingest --once         # or --limit 25 for a fast first taste
looma resume "auth"
```

### Works today
- Claude Code history ingestion (idempotent)
- WorkItem extraction + resolution
- Confidence scoring, surfaced everywhere
- Git-anchored context reconstruction (validated commits, branches, files)
- WorkItem-first resume bundles with honest uncertainty handling
- Local SQLite + FTS5; CLI: `init / ingest / work / resume / ask / status / doctor / reset`

### Known limitations (it's an alpha)
- Claude Code only (other agents are on the roadmap)
- Extraction is heuristic today; a local-LLM engine is the next milestone
- No semantic search / UI / MCP yet

### Roadmap
Local-LLM extraction, benchmark framework, cross-agent adapters (Codex, Cursor,
Gemini, Windsurf, OpenCode), MCP integration, timeline views, human correction
workflows, graph health metrics, semantic retrieval, local UI.

Local-first. MIT licensed. Feedback and PRs welcome - see CONTRIBUTING.md.

Full notes: [CHANGELOG.md](CHANGELOG.md) · [RELEASE_ALPHA.md](RELEASE_ALPHA.md)

---

## gh CLI one-liners (optional)

```bash
# set description + topics after the repo exists
gh repo edit devYRPauli/looma \
  --description "Looma turns coding-agent history into resumable project context." \
  --add-topic claude-code --add-topic developer-tools --add-topic local-first \
  --add-topic sqlite --add-topic productivity --add-topic git \
  --add-topic agent-memory --add-topic python
```
