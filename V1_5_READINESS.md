# Looma v1.5 Readiness

Date: 2026-06-21
Baseline: v1.0.0 (solo-developer milestone).
Driver: [REAL_WORLD_EVALUATION.md](REAL_WORLD_EVALUATION.md) - a real-corpus
evaluation (72 project buckets, 597 sessions, 73k messages, 20+ real repos).

This report records what the v1.5 refinement cycle measured and changed, what is
still weak, and what should enter v1.5 versus wait for v2. The cycle's rule was:
every change must improve the answer returned by `looma resume`, `looma ask`,
`looma brief`, or `looma explain`. Nothing else was built.

## 1. Benchmark history

| Benchmark | v1.0.0 | v1.5 | Notes |
|---|---|---|---|
| Extraction F1 (heuristic) | 0.69 | 0.69 | unchanged; candidate patterns untouched |
| Extraction F1 (local LLM) | 0.96 | 0.96 | unchanged; LLM path is the real precision fix |
| Retrieval recall@3 (FTS) | 0.62 | 0.62 | unchanged |
| Retrieval recall@3 (FTS+vec) | 1.00 | 1.00 | unchanged |
| Resume goal-match MRR | 0.67 | **1.00** | file/memory-aware, relevance-gated |
| Resume COLD when a true match exists | 4/6 | **0/6** | gates on relevance, not intrinsic confidence |
| Resume next-step real-rate (all projects) | 0.54 | **0.72** | real inference + noise filtering |
| Resume next-step real-rate (substantial) | ~0.54 | **0.73-0.91** | depends on corpus coverage |
| WorkItem code-derived garbage titles | 15 (5%) | **0** | intent rejects code/SQL/JSX |
| WorkItem uninformative "Work in dir/" | 80+ | **0** | salient-segment fallback |
| WorkItem active-lifecycle rate | 11% | **46%** | single substantive session -> active |
| Daemon rebuild (one project changed) | ~85s | **3.1s** | incremental per-project rebuild (~27x) |
| Per-command latency (884MB store) | n/a | **0.16-0.21s** | already invisible |

All measured on the real local corpus (`/tmp/looma-eval`), not synthetic
fixtures. 77 tests pass.

## 2. What v1.5 shipped

- **Resume that answers the four questions.** Relevance-gated (no more
  COLD-on-a-perfect-match), file-path + linked-memory aware matching (a generic
  title no longer caps relevance), real next-step inference, no-goal resume picks
  the most resumable item, and code/diff-line memories are filtered at read time.
- **`looma brief`** - 60-second orientation (summary, active work, decisions,
  risks, blockers, recent commits, suggested next work).
- **`looma explain <work>`** - why an effort exists, how it evolved, which
  decisions shaped it, what changed.
- **WorkItem quality** - intent extraction ignores code/SQL/JSX; "Work on
  <salient segment>" replaces "Work in <dir>/"; solo single-session work reaches
  `active`.
- **Incremental rebuild** - the daemon re-derives only changed repos.
- **Robustness** - fixed a `project_root is None` crash that silently broke
  rootless projects during rebuild (the original ingest rc=1); the full corpus
  now rebuilds cleanly (277 -> 325 work items).
- **`ask` ranks by relevance** blended with confidence (was pure confidence).
- All of the above are exposed over the MCP server (tools: resume_work, brief,
  ask, timeline, explain, list_work, recall).

## 3. Remaining weaknesses (measured, honest)

1. **33% of WorkItems are still "Untitled"** - thin/contentless sessions with no
   captured files and no extractable intent. Real repos title well; junk/thin
   buckets do not.
2. **~33 `unknown:<uuid>` project buckets** - sessions with no resolvable cwd
   each become a throwaway project. They pollute `status` and project pickers.
3. **`/tmp` over-merge** - 92 WorkItems from 298 sessions collapse into one
   `path:/private/tmp` bucket when clones are deleted.
4. **Identity fragmentation** - one repo can split across a remote-key and one or
   more path-keys (e.g. shb_database x3).
5. **Memory typing is still bug-heavy** (~80% of memories classified `bug`).
   Display-time filtering keeps resume/brief/explain clean, but `ask` over raw
   memory still surfaces noise. The real fix is the LLM extractor or better
   classification, not more display filters.
6. **Heuristic titles are verbose.** With code removed they are real prose, but
   still sometimes full conversational sentences ("Create New Test Files As And
   When Needed Please"). The local LLM extractor produces crisp titles; the
   heuristic is at its ceiling.
7. **`ask` relevance is FTS-coarse** (positional), not coverage-weighted like
   resume's matcher now is.

## 4. Recommendations

### Enter v1.5 (high impact, low risk, fits the four-answer rule)

- **Identity hygiene** (weaknesses 2-4): suppress `unknown:<uuid>` buckets from
  default listings; don't fuse distinct repos under a shared temp parent; merge
  remote-key and path-key buckets for the same repo. Directly improves every
  command's project picker and the `/tmp` blob.
- **Coverage-weighted `ask` ranking** (weakness 7): reuse resume's soft-sim
  coverage scorer in `ask` so retrieval ranking matches resume's quality.
- **Title fallback from first user message** (weakness 1): when a WorkItem has no
  files and no intent match, derive a short title from the session's first real
  user line. Cuts the 33% "Untitled".

### Wait for v2 (needs the LLM path or larger design)

- **LLM-routed titles + merge-judge** (weaknesses 5-6): crisp titles and correct
  decision/bug/todo typing are fundamentally an LLM job; the heuristic is at its
  ceiling. Make the local LLM extractor the default when present, and add an
  LLM merge/split judge.
- **Default-on semantic retrieval** with a bundled embedding model (so FTS+vec
  recall@3 1.00 is the out-of-box experience, not opt-in).
- **More adapters** (Gemini, Windsurf, OpenCode) and Cursor project resolution
  via workspace.json.
- **Packaged daemon** (launchd/systemd) so "stays current automatically" needs
  zero manual start.
- **Grow the golden sets** for extraction + retrieval + resume so regressions are
  caught automatically.

## 5. Readiness verdict

v1.5's stated goal - make Looma feel indispensable for solo developers - is met
on the dimension that matters most day to day: **resume now reliably answers what
you were doing, what changed, what remains, and what to do next**, and `brief` /
`explain` give the at-a-glance and the deep-dive. The remaining weaknesses are
concentrated in junk/thin project buckets and in memory typing - both real, both
scoped above into v1.5 (hygiene) and v2 (LLM typing). The foundation (git-anchored
identity, incremental rebuild, confidence, local-first) is solid.
