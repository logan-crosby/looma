# Looma v1.5 Report

Date: 2026-06-21
From: v1.0.0 (solo-developer milestone)
Objective: stop adding capabilities; make Looma feel indispensable. Every change
had to improve the answer returned by `looma resume`, `looma ask`, `looma brief`,
or `looma explain`. No cloud/team/auth/billing/SaaS/dashboard/web work.

## Summary

This cycle evaluated Looma against a real local corpus, then fixed what the
evaluation found - in priority order of how often it hurt the four answers. The
headline result: **resume now reliably tells a developer what they were doing,
what changed, what remains, and what to do next**, and two new commands (`brief`,
`explain`) give the at-a-glance and the deep-dive. All measured on real data, not
fixtures. 77 tests pass.

## Phases delivered

1. **Real-world evaluation** ([REAL_WORLD_EVALUATION.md](REAL_WORLD_EVALUATION.md))
   - 72 project buckets, 597 sessions, 73k messages, 20+ real repos.
   - Top-10 failure modes / confusion points / missing capabilities,
     frequency-ranked into the fix plan the later phases followed.

2. **Resume quality** - the #1 fix. Resume gated on a WorkItem's intrinsic
   confidence, so solo-dev work went COLD even when the correct item ranked #1.
   Now it gates on match relevance; matching also scores file paths and linked
   memories; next-step is inferred (todo > uncommitted > bug > file > continue),
   not bug-parroted; no-goal resume picks the most resumable item.
   - goal-match MRR 0.67 -> **1.00**; COLD-when-a-true-match-exists 4/6 -> **0/6**;
     next-step real-rate 0.54 -> **0.72**.

3. **`looma brief`** - 60-second orientation: summary, active work, recent
   decisions, current risks, open blockers, recent commits, suggested next work.

4. **WorkItem quality** - intent extraction rejects code/SQL/JSX; "Work on
   <salient segment>" replaces "Work in <dir>/"; a single substantive session is
   now `active`.
   - code-derived garbage titles 15 -> **0**; uninformative dir titles 80+ -> **0**;
     active-lifecycle rate 11% -> **46%**.

5. **`looma explain <work>`** - why an effort exists, how it evolved, which
   decisions shaped it, what changed (timeline + graph).

6. **Daily workflow** - incremental rebuild: the daemon re-derives only changed
   repos. One-project rebuild **3.1s vs ~85s full (~27x)**; per-command latency
   0.16-0.21s on an 884MB store.

7. **V1.5 readiness** ([V1_5_READINESS.md](V1_5_READINESS.md)) - benchmark
   history, remaining weaknesses, and a v1.5-vs-v2 split.

Plus: a robustness fix (a `project_root is None` crash that silently broke
rootless projects and was the real cause of the original ingest rc=1; the full
corpus now rebuilds cleanly, 277 -> 325 work items), and `ask` now ranks by
coverage-weighted relevance blended with confidence (was pure confidence).
Everything is exposed over MCP (resume_work, brief, ask, timeline, explain,
list_work, recall).

## Scorecard (all on the real corpus)

| Dimension | v1.0.0 | v1.5 |
|---|---|---|
| Resume goal-match MRR | 0.67 | 1.00 |
| Resume COLD on a true match | 4/6 | 0/6 |
| Resume next-step real-rate | 0.54 | 0.72 |
| WorkItem garbage titles | 15 | 0 |
| WorkItem "Work in dir/" titles | 80+ | 0 |
| WorkItem active rate | 11% | 46% |
| Daemon rebuild (1 project) | ~85s | 3.1s |
| Commands answering the 4 questions | 2 (resume, ask) | 4 (+brief, +explain) |
| Tests | 72 | 77 |

## Honest remaining weaknesses

- 33% of WorkItems are still "Untitled" (thin/contentless sessions).
- ~33 `unknown:<uuid>` buckets and a 92-item `/tmp` over-merge pollute the
  project list; one repo can fragment across remote-key and path-key buckets.
- Memory typing is still ~80% "bug"; display filtering keeps resume/brief/explain
  clean, but raw `ask` over memory still surfaces noise.
- Heuristic titles are prose now, but verbose; crisp titles + correct typing are
  an LLM-extractor job.

Recommended split (detail in V1_5_READINESS.md): **v1.5** = identity hygiene,
first-message title fallback, coverage-weighted ask (done). **v2** = LLM-default
extraction + merge-judge, default-on semantic retrieval, more adapters, packaged
daemon, larger golden sets.

## Verdict

The cycle's goal is met where it matters daily: resume is trustworthy, and brief
and explain make a project legible fast. The foundation - git-anchored identity,
incremental rebuild, confidence, fully local - is solid. The remaining work is
scoped and recorded.

Stopping condition met: real-world evaluation completed, resume quality improved,
brief and explain shipped, WorkItem quality improved, readiness report generated.
