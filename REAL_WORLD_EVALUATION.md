# Looma Real-World Evaluation (Phase 1)

Date: 2026-06-21
Looma version under test: v1.0.0 (heuristic extractor, vectors off - the
zero-dependency default path every new user gets on first run).

This is the gate report for the v1.5 refinement cycle. It measures Looma against
a real, unsanitized local corpus instead of synthetic fixtures, identifies the
failure modes that actually degrade the four user-facing answers (`resume`,
`ask`, `brief`, `explain`), and ranks fixes by frequency so later phases work on
the right problems.

## 1. Method

- Corpus: the full local Claude Code transcript history under
  `~/.claude/projects/` (all adapters), ingested into an isolated eval DB
  (`/tmp/looma-eval/eval.db`, `LOOMA_DB` override) so the user's real
  `~/.looma/looma.db` was never touched.
- Extractor: `heuristic` (no LLM server running) - deliberately the default
  first-run experience, not the best-case LLM path.
- Vectors: `off` - again the default.
- Harness: `/tmp/looma-eval/harness.py` (aggregate metrics over every project)
  and `/tmp/looma-eval/deep.py` (per-project `work` / `resume` / `resume+goal` /
  `ask` capture for projects the author knows ground-truth for: mddocs, looma,
  world-cup-2026-picks, lab-agents/CERES, shb_database, fundrd, and the /tmp
  OSS-contribution bucket).
- Judgement: the author hand-verified output for the projects above against
  first-hand knowledge of what that work actually was.

## 2. Corpus scale

| Metric | Value |
|---|---|
| Project buckets created | 72 |
| Sessions ingested | 597 |
| Messages ingested | 73,274 |
| WorkItems built | 277 |
| Entities (memories) | 960 |
| Candidate memories | 2,505 |

Distinct **real repositories** represented: well over 20. Personal/work repos
(mddocs, looma, world-cup-2026-picks, fundrd, lab-agents/CERES, resume-builder,
portfolio, papers-rag, shb_database, continue) plus 20+ open-source repos worked
on in throwaway clones under `/tmp` (mem0, ragflow, mlx, mlx-lm, litellm, agno,
sweet-cookie, inngest, vox, bslog, osc-progress, and more). The evaluation
therefore satisfies the ">= 20 real repositories" bar - but, as Section 4 shows,
many of those repos did **not** survive ingestion as usable project buckets.

## 3. Headline quality metrics

| Signal | Result | Target health |
|---|---|---|
| Usable project buckets (real root + has work) | 15 / 72 (21%) | should be ~ # of real repos |
| `unknown:<uuid>` junk buckets (no cwd resolved) | ~33 | 0 |
| Largest over-merge bucket (`path:/private/tmp`) | 92 WorkItems, 298 sessions | should be many distinct repos |
| Generic WorkItem titles ("Work in X/", "Untitled work") | 133 / 277 (48%) | < 10% |
| WorkItems stuck at `candidate` lifecycle (conf < 0.40) | 246 / 277 (89%) | most real efforts should reach `active` |
| `resume <goal>` returning CONFIDENT on a true match | ~0% (almost always COLD) | high for clear goals |
| `next_step` populated on no-goal resume | 54% | ~100% for active work |
| Entities classified `bug` | 765 / 960 (80%) | bugs are a minority of real memories |
| Entities that are raw diff lines (start `+`/`-`) | 271 / 960 (28%) | ~0% |
| Entities containing raw code symbols | 256 / 960 (27%) | low |
| `ask` results ordered by relevance | No (ordered by confidence) | relevance-first |

## 4. Top 10 failure modes (frequency-ranked)

1. **Generic / meaningless WorkItem titles (48% of all items).** Titles like
   "Work in packages/", "Work in src/", "Untitled work", "Add Small
   Enhancement", "Fix Before Proceeding". These are the first thing the user
   sees in `resume`, `work`, and `ask`, and they carry zero information. Root
   cause: when `_intent` finds no user-intent phrase it falls back to the
   dominant directory; and `_intent` itself often misfires (see #2).

2. **Titles extracted from code / JSX / docstrings, not user intent.**
   Examples observed: `Create TABLE IF NOT EXISTS Projects`,
   `Create Store And Run Migrations").set_defaults`,
   `Build Safe FTS5 OR Query From Free Text`,
   `Create Account And Start Picking Right Away." : "Sign In`,
   `Fix "), Code, Diffs, Stack Traces`. The intent regex matches imperative
   verbs anywhere - including inside fenced code, JSX string literals, SQL, and
   architecture docs the user pasted. ~Cosmetically distinct from #1 but same
   user-visible damage.

3. **Bug over-extraction: 80% of all memories are labelled `bug`.** Only 26
   decisions and 74 todos exist across 960 memories. The decision/architecture
   content the user most wants in `resume` and `ask` is drowned out by 765
   "bugs", most of which are not bugs.

4. **Raw diff/code lines stored as memories (27-28%).** Memory titles such as
   `+ if (Date.now() - start > timeoutMs) throw new Error('waitFor timed out')`
   and `+"""Confidence scoring - ARCHITECTURE.md section 5.4.` The sanitizer
   does not strip leading diff markers or reject code-only lines before
   promotion.

5. **`resume <goal>` is almost always COLD even for correct goals.** Root cause:
   the confident/ambiguous/cold decision gates on the WorkItem's *intrinsic*
   confidence (`RESUME_LOW = 0.40`), but 89% of items are below 0.40 because the
   confidence formula puts 60% of its weight on session-breadth + agent-breadth
   + commit-linkage - signals a solo developer working in one session with
   uncommitted code structurally cannot earn. The model penalizes the exact
   workflow it is meant to serve.

6. **`next_step` is wrong or missing.** Populated only 54% of the time, and when
   populated it frequently parrots a mis-extracted "bug" that is really a diff
   line or a numbered list item (e.g. `investigate bug: 7. Define a small stable
   regression suite...`). It never reasons about what actually remains.

7. **`ask` ranks by confidence, discarding match relevance.** After FTS finds
   candidates, results are re-sorted purely by `confidence` desc. A barely
   relevant conf-0.25 bug outranks a precise conf-0.00 architecture decision.
   For "what changed in the sync logic" the top hits were unrelated Vercel
   deploy errors.

8. **`unknown:<uuid>` project explosion (~33 buckets).** Sessions whose events
   carry no resolvable `cwd` each become their own throwaway project keyed by
   session UUID, with zero work items. Two-thirds of all project buckets are
   unusable noise, polluting `status` and project pickers.

9. **Over-merge into a `/tmp` mega-bucket (92 WorkItems / 298 sessions).** Many
   distinct OSS repos worked on in deleted `/tmp` clones collapse into a single
   `path:/private/tmp` project because the clone is gone and identity falls back
   to the parent temp path. The opposite of #8: distinct efforts fused into one
   unusable blob.

10. **Identity fragmentation: one repo, several buckets.** `shb_database`
    appears as `github.com/donandrade/shb_database` (57 WI), plus
    `path:.../Desktop/shb_database` and `path:.../Downloads/shb_database-feature-...`.
    A repo cloned twice, or used before a remote was set, splits into
    remote-keyed and path-keyed buckets that never join.

## 5. Top 10 confusion points (where the user is misled)

1. A 48%-generic `work` list reads as "Looma does not understand my project."
2. COLD-on-everything makes `resume <goal>` feel broken even when the right item
   exists in the top match.
3. "80% bugs" makes every project look like it is on fire.
4. Duplicate WorkItems with identical titles (e.g. two `Create Store And Run
   Migrations").set_defaults`) imply Looma is double-counting effort.
5. `next_step` quoting a diff line looks like a parsing bug to the user.
6. The `/tmp` mega-bucket lists 92 unrelated work items under one name.
7. `unknown:<uuid>` buckets in `status` look like data corruption.
8. `ask` returning unrelated high-confidence bugs erodes trust in retrieval.
9. `ask` returning 0 hits for an obviously-present topic (mddocs "marks")
   reads as "Looma didn't ingest my work."
10. `candidate` lifecycle on 89% of items implies nothing is "real" yet, even
    for shipped, committed work.

## 6. Top 10 missing capabilities

1. **A `brief` command** - no way to understand a project in 60 seconds
   (Phase 3).
2. **An `explain <workitem>` command** - no way to see why an item exists or how
   it evolved (Phase 5).
3. **Intent extraction that ignores code/docs** and reads the real task ask
   (Phase 4).
4. **Relevance-aware retrieval ranking** in `ask` and `resume` (Phase 2).
5. **A solo-dev-aware confidence/lifecycle model** so single-session committed
   work can become `active` (Phase 2/4).
6. **Real next-step inference** from unfinished todos + open threads + last
   activity, not bug-parroting (Phase 2).
7. **Better memory typing** - distinguish decision/architecture/todo from the
   flood of "bug", and drop code/diff lines pre-promotion (Phase 4 support).
8. **Identity hygiene**: suppress `unknown:<uuid>` buckets, and don't fuse
   distinct repos under a temp parent path (Phase 4/6).
9. **Cross-bucket repo merge** (remote-key <-> path-key for the same repo)
   (Phase 4).
10. **WorkItem de-duplication** by title + file overlap (Phase 4).

## 7. Prioritized fix plan (drives Phases 2-6)

Ordered by user-facing frequency x impact on the four answers:

| Rank | Fix | Phase | Answers improved |
|---|---|---|---|
| 1 | Solo-dev confidence + lifecycle so real work reaches `active`; resume gates on match relevance not intrinsic confidence | 2 | resume |
| 2 | Real next-step inference (todos/open threads), stop bug-parroting | 2 | resume |
| 3 | Relevance-first ranking in ask + resume | 2 | ask, resume |
| 4 | Intent extraction that ignores code/docs/JSX; drop generic titles | 4 | resume, ask, brief, explain |
| 5 | Memory typing + diff/code rejection (cut the 80% bug flood) | 4 | ask, brief, explain |
| 6 | `looma brief` | 3 | brief |
| 7 | `looma explain <workitem>` | 5 | explain |
| 8 | WorkItem de-dup + cross-bucket repo merge | 4 | all |
| 9 | Identity hygiene: hide unknown buckets, don't fuse /tmp | 4/6 | all |
| 10 | Daemon/startup/ingest speed | 6 | all (latency) |

The single highest-leverage change is **title/intent quality (rank 4)** because
generic titles cascade into weak match relevance (capping at ~0.28), which
causes COLD resumes and bad ask ranking. But the fastest trust win is **rank 1-2
(resume)**, which the user named the top priority. Phase 2 begins there; Phase 4
fixes the upstream title/memory quality that makes Phase 2's ranking honest.

## 8. What already works

- Git-remote identity is reliable: real repos (mddocs, looma, world-cup, fundrd,
  lab-agents, shb_database, continue) keyed correctly by normalized remote.
- Zero orphan entities (every memory links to a WorkItem).
- Ingestion is robust at scale (73k messages, 597 sessions, no crashes).
- File-overlap merge keeps most same-effort sessions together.
- FTS retrieval surfaces the right *documents*; only the *ranking* is wrong.

These are the foundations Phases 2-6 build on.
