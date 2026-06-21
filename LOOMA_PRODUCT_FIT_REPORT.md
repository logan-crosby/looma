# Looma Product-Fit Report

Date: 2026-06-21
The summary deliverable of the daily-loop cycle. Synthesizes
DAILY_USAGE_REPORT, TODAY_EVALUATION, RETENTION_REPORT, FIRST_RUN_REPORT,
AGENT_VALUE_REPORT, and LOOMA_V2_STRATEGY into the product-fit picture.

## Strongest user loop

**Sit down -> type `looma` -> see what you were doing, what changed, what's
blocked, what's next, here and across your other repos -> act.**

This is the daily reload-context loop. It is now one command (`today`, the bare
`looma` default), zero arguments, ~0.2s. It answers the four daily questions more
completely than anything else (0.89/4 vs resume 0.55, brief 0.61) and is the only
command built for the measured reality that a developer touches ~6 repos/day. The
weekly variant (`looma weekly`) closes the loop at the week scale.

Supporting loop (distinct questions, lower frequency): `ask` (targeted recall),
`explain` (one effort's story), `resume` (goal-driven reload).

## Strongest differentiator

**Grounded compression.** Looma turns coding-agent history into a typed,
git-anchored answer and hands it over in 1-3% of the tokens of the raw transcript
(32x-101x measured), with provenance and confidence. For a human it is "the
meaning, not the transcript"; for an agent it is a correct orientation that costs
almost no context window. Nothing else in the local-first space does this:
transcript search returns bytes; Looma returns meaning.

Second differentiator: **zero-setup, fully local**. No account, no key, no cloud;
~10-15s to first answer. The product you just run.

## Retention drivers

1. **Frictionless trigger** - bare `looma` runs the daily view; the habit costs
   nothing beyond the binary name.
2. **Cross-project pull** - the one place that shows all ~6 repos you touched,
   each with its next step, so context-switching is one command.
3. **Recall value compounds with time** - the longer a project runs, the less you
   remember and the more Looma is worth (multi-month efforts are where it shines).
4. **Stays current invisibly** - the daemon re-derives only changed repos (~27x
   cheaper), so the data is always fresh without thought.
5. **Agent integration** - once your agents call Looma over MCP, the daily loop
   extends beyond the human.

## Trust risks

1. **Title and memory-typing quality** (the dominant risk). 33% of WorkItems are
   "Untitled", ~80% of memories are typed "bug", and some decisions are
   conversational lines. Display filtering keeps the daily commands clean, but a
   user who sees a junk title once discounts the whole tool. Fix: LLM-default
   extraction (V2 #1).
2. **Thin "what changed/shipped"** - commits link for only 4/72 projects, so the
   shipped-work story leans on sessions + working tree. Fix: commit linkage
   (V2 #2).
3. **Junk in listings** - `unknown:<uuid>` buckets and the `/tmp` over-merge make
   the project list look noisy. Fix: identity hygiene (V2 #3).
4. **Wrong details destroy trust fast** - this cycle found and fixed a path
   truncation ("looma/cli.py" -> "ooma/cli.py") and an emoji leak into agent
   context. The lesson: correctness of the small stuff is a retention feature.

## Recommended V2 roadmap (ranked by impact)

1. **LLM-default extraction + merge/split judge** - crisp titles, correct typing.
   The ceiling on every answer.
2. **Commit linkage + working-tree "what shipped"** - make the daily
   differentiator authoritative.
3. **Identity hygiene** - hide unknown buckets, merge fragmented repos, stop the
   /tmp fuse. Cheap trust win.
4. **Streaming first ingest** - value in seconds; remove the only multi-minute
   wait.
5. **Default-on semantic retrieval** (bundled embed model).
6. **Command consolidation** - retire `work`, fold `timeline` into `explain`.
7. **More adapters; packaged daemon; post-install discovery.**

Never build: cloud/team/SaaS/web/auth/billing/dashboards, a chatbot wrapper,
manual task CRUD, social/sharing. They break the local-first, derived,
single-developer identity that is the fit.

## Product-fit verdict

Looma has a real, defensible daily loop: a frictionless, grounded, local reload
of "what was I doing, here and everywhere," that gets more valuable the longer
your projects run and extends cleanly to your agents. The fit is strong on the
loop and the differentiator; the open risk is answer *crispness*, which is an
extraction-quality problem with a known fix (LLM-default, V2 #1). Ship the V2
roadmap in the order above and the daily habit gets crisper, more complete, and
cleaner without ever needing an account.
