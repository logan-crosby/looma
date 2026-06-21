# Launch posts

Three variants for the same launch. All honest about alpha status and Claude-only
scope. Pick one per channel; do not overstate. Attach `docs/demo/looma-demo.gif`.

Positioning reminder: resumable project context / work reconstruction / git-anchored
project understanding / local-first project memory. Not "AI memory", not "second
brain", not "RAG".

---

## Version A - short and punchy (general)

> You close your laptop mid-feature. Three days later: "wait, where was I?"
>
> Looma reconstructs it. From your Claude Code history it rebuilds the active work,
> the decisions, the blockers, the commits and files in flight - and the next step.
>
> `looma resume "auth"`
>
> Local-first. No cloud. No API keys. Early alpha, open source. [link]

---

## Version B - technical audience

> Built Looma: it turns Claude Code session history into resumable, git-anchored
> project context.
>
> Pipeline: transcripts -> normalized events -> WorkItems -> candidate memories ->
> confidence scoring -> resume bundle. SQLite + FTS5, standard-library Python, zero
> deps. Commits/branches/files are validated against git - never invented.
>
> `looma resume "auth"` returns the WorkItem with its constraints, open todos,
> affecting bugs, recent commits and files, plus a confidence score - and when it
> isn't sure, it says so instead of guessing.
>
> Alpha, Claude Code only for now. Local-first, no API keys. [link]

---

## Version C - open-source audience

> Open-sourcing Looma (alpha): local-first project memory for coding agents.
>
> It reconstructs what you were working on - active work, decisions, blockers,
> commits, files in flight, next steps - from your Claude Code history. Runs
> entirely on your machine: no cloud, no API keys, no telemetry. Zero third-party
> dependencies; just Python + SQLite.
>
> It's early and honest about it: extraction is heuristic today (a local LLM engine
> is the next milestone), and only Claude Code is wired up so far. Codex/Cursor/
> Gemini/Windsurf/OpenCode adapters, MCP, and semantic retrieval are on the roadmap.
>
> Feedback and PRs welcome. [link]

---

## Thread continuation (optional, after A or B)

> 1/ Why not just search transcripts? Search answers "which message mentioned
> Redis?". Looma answers "what's the active work, what did we decide and why, which
> commits implement it, what's still unfinished?" - by organizing history around
> WorkItems and anchoring them to git.
>
> 2/ Everything is local. Your transcript contents never leave the machine. The
> store is plain SQLite you can delete with `looma reset`.
>
> 3/ Alpha caveats, stated plainly: Claude Code only, heuristic extraction (LLM
> engine next), no UI/MCP yet. Roadmap + what-works-today in the README. [link]
