# Looma V2 Strategy

Date: 2026-06-21
Basis: the daily-loop cycle (DAILY_USAGE_REPORT, TODAY_EVALUATION,
RETENTION_REPORT, FIRST_RUN_REPORT, AGENT_VALUE_REPORT). This is a product
strategy, not a feature list - ranked by expected user impact.

## 1. What users actually value

Grounded in the measured behaviour, not aspiration:

1. **The daily reload-context moment.** Sit down, run `looma`, see what you were
   doing / what changed / what's next - across the ~6 repos touched per day.
   `today` answers this at 0.89/4 vs resume 0.55 / brief 0.61, and it is now the
   bare-`looma` default.
2. **Returning to a project after a gap.** Multi-session efforts span weeks to
   months (shb_database: Oct 2025 -> May 2026). Nobody remembers them; resume /
   brief / explain reconstruct them.
3. **Grounded compression for agents.** Looma hands an agent a typed, correct
   orientation in 1-3% of the tokens it would spend re-reading transcripts
   (32x-101x). Meaning, not bytes.
4. **Zero setup, fully local.** No deps, no cloud, no key; data never leaves the
   machine. Time-to-first-answer ~10-15s on the quick path.
5. **The weekly retro.** "What did I actually ship this week" across all repos.

## 2. What users ignore

1. **Raw list commands** - `work` (a WorkItem dump) and `timeline` (a flat event
   list subsumed by `explain`). No synthesis, no daily pull.
2. **The confidence decimal.** The band (high/med/low) communicates trust; the
   0.41-vs-0.43 precision does not.
3. **Single-session / junk projects.** 55/72 buckets are one-offs and 46 are
   `unknown:<uuid>`; users never resume these.
4. **Internal tooling** (`benchmark`) - correct to keep, but not a user surface.

## 3. Highest-leverage improvements

Ranked by how much they move the four answers (today/ask/brief/explain):

1. **LLM-default extraction.** Titles and memory typing are the ceiling on *every*
   command's answer quality (33% Untitled, ~80% memories typed "bug",
   conversational decisions). The local LLM extractor already wins F1 0.96 vs 0.69
   and is auto-detected - making it the default-when-present (and bundling a small
   model) is the single biggest quality lever.
2. **Commit linkage + "what shipped".** "What changed" is the strongest daily
   differentiator, but commits link for only 4/72 projects. Better SHA extraction
   from transcripts + working-tree diffing turns `today`/`weekly` shipped-work
   from thin to authoritative.
3. **Identity hygiene.** Suppress `unknown:<uuid>` buckets, merge a repo split
   across remote-key and path-keys, and stop fusing distinct repos under a `/tmp`
   parent. Cleans every listing and the cross-project switch view.
4. **Streaming first ingest.** Process most-recent-first and show value in seconds
   while the rest indexes in the background - removes the only multi-minute wait.
5. **Default-on semantic retrieval** with a bundled embedding model (FTS+vec
   recall@3 1.00 out of the box, not opt-in).
6. **Command consolidation.** Deprecate `work`, merge `timeline` into `explain
   --timeline`. Five things to remember, not eighteen.

## 4. Features that should never be built

- **Cloud / team / SaaS / web app / dashboards / auth / billing.** They dilute the
  local-first, single-developer, zero-setup identity that is the whole point. The
  moment Looma needs an account, it stops being the thing you just run.
- **A chatbot wrapper ("ask Looma anything" with an LLM).** Looma is grounded
  memory, not a conversational agent. Retrieval + structure is the value; a chat
  layer invites hallucination and hides provenance.
- **Manual WorkItem/task CRUD.** Looma is *derived* from what you did, not a
  planner you maintain. A task tracker is a different, crowded product.
- **Social / sharing / "team memory."** Different product, different trust model,
  kills the privacy guarantee.
- **Editor plugins with always-on panels.** The CLI + MCP is the surface; an
  ambient panel is scope creep that competes with the agent integration.

## 5. V2 roadmap (ranked by expected user impact)

| # | Item | Drives | Effort |
|---|---|---|---|
| 1 | LLM-default extraction + merge/split judge | answer quality (all four) | M |
| 2 | Commit linkage + working-tree "what shipped" | daily "what changed" | M |
| 3 | Identity hygiene (hide unknown, merge repos, no /tmp fuse) | trust, every listing | S |
| 4 | Streaming first ingest (value in seconds) | time-to-value | M |
| 5 | Default-on semantic retrieval (bundled embed model) | retrieval | M |
| 6 | Command consolidation (retire work, timeline->explain) | retention | S |
| 7 | More adapters (Gemini, Windsurf, OpenCode) | reach | M |
| 8 | Packaged daemon (launchd/systemd) + post-install discovery | retention, time-to-value | S |

Sequencing: 3 and 6 are cheap trust/clarity wins - do them first. 1 and 2 are the
quality core. 4, 5, 8 are the polish that makes the daily habit effortless.

## 6. The one-line strategy

Make the thing users already value - **a grounded, zero-setup daily reload of
"what was I doing, here and everywhere"** - crisper (LLM extraction), more
complete (commit linkage), and cleaner (identity hygiene). Build nothing that
needs an account.
