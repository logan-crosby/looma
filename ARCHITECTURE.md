# AI Project Memory OS - Technical Architecture (v3)

Local-first system that turns coding-agent sessions (Claude Code, Codex, Cursor,
Gemini CLI, OpenCode, Windsurf) into a queryable, git-anchored model of a
project's ongoing work. The unit of value is reconstructed, actionable, and
*trustworthy* project context, not transcript search.

Status: design / MVP blueprint, final pre-implementation pass. ASCII only. CLI
binary is `looma`. Recommended defaults are marked [DEFAULT]; real forks are marked
[FORK] with the alternative.

> v3 change (this revision): operational correctness, user trust, and long-term
> graph quality. Adds (a) first-class **confidence** on work items, validated
> entities, and candidates, derived from the same signals as promotion and
> surfaced everywhere; (b) a **Human Correction Layer** whose actions are durable
> graph evidence that future resolution must respect; (c) a **Correction Ledger**
> making the graph reproducible from `raw events + ledger`; (d) **Graph Health
> Metrics** to detect degradation early; (e) an uncertainty-aware **Resume** that
> never silently collapses low-confidence work. Binary renamed `memos -> looma`.
> See section 0.1 for the diff, section 21 for implementation impact.

---

## 0. Design thesis

A transcript search tool answers "which message mentioned Redis?". This system
answers "what is the active work on auth, how sure are we, what did we decide and
why, which commits implement it, and what is still blocking it?". Five commitments:

1. Model **work**, not just memory: a WorkItem is the first-class spine.
2. **Gate memory by signal**: extraction produces candidates; only corroborated
   facts are promoted into the graph.
3. **Quantify trust**: every work item, validated entity, and candidate carries a
   `confidence` derived from evidence, surfaced in CLI and retrieval.
4. **Anchor to git ground truth**: SHAs, paths, PRs come from the repo, never the LLM.
5. **Keep humans in the loop**: user corrections are durable, ledgered evidence that
   overrides automated resolution and makes the graph reproducible and auditable.

### 0.1 Architecture diff (v2 -> v3)

| Concern              | v2                                          | v3                                                              |
|----------------------|---------------------------------------------|----------------------------------------------------------------|
| Trust signal         | internal `promotion_score` only             | first-class **`confidence` [0,1]** on work_items/entities/candidates, surfaced |
| Promotion            | threshold on promotion_score                | threshold on the same **confidence**; score formula is now the spec'd one (5.4) |
| Human input          | none (fully automated)                      | **Human Correction Layer**: merge/split/rename/false-positive/promote/reject (13) |
| Constraints          | resolver used signals only                  | resolver honors **MUST_LINK / CANNOT_LINK / pins** from corrections (13.2)|
| Auditability         | append-only flags                           | **Correction Ledger**; graph = f(raw events + ledger) (14)     |
| Observability        | none                                        | **Graph Health Metrics** + `looma status --health` (15)        |
| Resume on ambiguity  | returned single best WorkItem               | **surfaces uncertainty + alternatives, never collapses** (10.1)|
| CLI binary           | `memos`                                     | **`looma`**                                                    |

Unchanged and carried forward: ingestion adapters (2), project identity (3), the
extraction->candidate->resolution->promotion refinery (4-5), WorkItem-first graph
(7), hybrid retrieval mechanics (9), local-first SQLite substrate (6).

---

## 1. System overview

```
 agent transcript files (6 formats, on disk)
        |
   [ 1. Ingestion ]  watchers + per-source adapters -> NormalizedEvent stream
        v
   [ 2. Extraction ] deterministic + LLM -> CandidateMemory + work_signals
        v
   [ 3. Resolution ] (a) entity dedup  (b) WorkItem resolution
        |              <-- honors correction constraints (MUST/CANNOT_LINK, pins)
        v
   [ 4. Promotion ]  confidence scoring -> ValidatedMemory + active WorkItems
        |              <-- honors force-promote / force-reject / false-positive
        v
   [ 5. Storage ]    SQLite: messages | candidate_memories | entities | work_items
        |              | nodes/edges | correction_ledger | health snapshots
        |              + sqlite-vec + FTS5 + git mirror
        v
   [ 6. Enrichment ] git correlation, WorkItem-scoped summaries
        v
   [ 7. Retrieval ]  WorkItem-centric hybrid, confidence-aware
        v
   resume | work | timeline | ask | correct | status --health  (CLI / MCP)
        |
   [ Human Correction Layer ] --writes--> Correction Ledger --feeds--> Resolution/Promotion
```

The correction layer is a feedback loop: user actions are appended to the ledger
and become hard inputs to the next resolution/promotion pass.

---

## 2. Ingestion layer (unchanged from v2)

Per-source adapters turn native records into a canonical `NormalizedEvent`.

| Source      | Location                                                        | Format                          |
|-------------|-----------------------------------------------------------------|---------------------------------|
| Claude Code | `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`            | JSONL, one record per turn      |
| Codex       | `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl`        | JSONL rollout records           |
| Gemini CLI  | `~/.gemini/history/<project>/`, `~/.gemini/tmp/`                | JSON/JSONL session logs         |
| Cursor      | `.../Cursor/User/workspaceStorage/<hash>/state.vscdb`           | SQLite; chat in `ItemTable`     |
| Windsurf    | `.../Windsurf/User/workspaceStorage/<hash>/state.vscdb`         | SQLite (VS Code fork)           |
| OpenCode    | `~/.opencode/` or `~/.local/share/opencode/`                    | JSON session store              |

JSONL sources tail by byte offset; SQLite sources open read-only `immutable=1` and
diff by message id. `raw_json` + per-adapter `schema_version` retained so the graph
can be rebuilt from stored turns (sections 14, 19).

`NormalizedEvent`: `{event_id, source, session_native_id, project_root, git_remote,
seq, ts, role, agent_model, text, tool_calls[], raw_json}`. Idempotent on
content-hash `event_id`; resumable via per-file cursors.

---

## 3. Project identity (unchanged)

First hit wins: (1) normalized `git remote` -> `host/org/repo` [DEFAULT key],
(2) git root path, (3) encoded-cwd. `project_aliases` unifies worktrees/clones.
WorkItems are always project-scoped; resolution never crosses projects.

---

## 4. Extraction -> CandidateMemory (unchanged from v2)

Deterministic extractors (files validated against repo tree + tool args, commits via
`git cat-file -e`, branches, PRs, commands, code blocks) emit git ground truth and
strong resolution signals. The LLM extractor emits, per window, evidence-bound
candidate memories (decisions/todos/bugs/architecture) plus `work_signals` (the raw
"this window is about effort X" hints). [DEFAULT] local 8B-class model behind one
`Extractor` interface; extraction outputs are **content-hash cached** (this cache is
what makes the pipeline deterministic for reproducibility, section 14).

### 4.4 WorkItem resolution (now constraint-aware)

For each `work_signal`, score against existing WorkItems:

```
score = w1*cosine(summaries) + w2*jaccard(files) + w3*shared_branch_or_commit
      + w4*temporal_continuity + w5*alias_overlap        // w2 (files) weighted highest
```

- score >= HIGH (~0.8): assign, append alias. LOW<score<HIGH: new WorkItem + weak
  `RELATED` link. score<LOW: new WorkItem.
- **Correction constraints override scores** (section 13.2): a `MUST_LINK` forces
  assignment regardless of score; a `CANNOT_LINK` forbids a merge the scores would
  otherwise make; a name pin freezes the title. Constraints are consulted before the
  numeric decision, so the resolver can never undo a human correction.

---

## 5. Promotion - CandidateMemory -> ValidatedMemory

Only promoted (ValidatedMemory) facts become graph nodes. Git objects are always
nodes (ground truth) and act as the strongest promotion signal.

### 5.1-5.3 (unchanged from v2)

Candidate staging vs validated graph nodes; promote instantly if commit-linked or
attached to an active WorkItem, else when confidence crosses threshold T; promotion
is append-only and auditable; supersession is marked not deleted. **Force-promote /
force-reject / false-positive corrections (13) override the automated decision.**

### 5.4 Confidence scoring (NEW - the trust number)

`confidence` is a single normalized `[0,1]` value computed from the spec'd signals.
It replaces v2's opaque `promotion_score` as the canonical field, and the promotion
threshold now reads `confidence >= T`.

```
raw = 0.30 * file_overlap        // shared-file / cluster-cohesion evidence
    + 0.25 * commit_linkage      // 1.0 if >=1 IMPLEMENTS commit, else 0
    + 0.20 * session_breadth     // 1 - exp(-k*(distinct_sessions - 1))   [saturating]
    + 0.15 * agent_breadth       // 1 - exp(-k*(distinct_agents  - 1))    [saturating]
    + 0.10 * temporal_persistence// re-reference span / age, decayed       [survives time]

confidence = clamp01(raw), THEN apply ledger overrides:
    user CONFIRM / force-promote / merge-target -> confidence = 1.0  (pinned)
    user REJECT  / false-positive               -> confidence = 0.0  (quarantined)
```

Component emphasis differs per object (same formula, different signal availability):
- `candidate_memories.confidence`: driven by commit/session/agent/temporal; file
  overlap minor. Drives promotion.
- `work_items.confidence`: file-overlap (resolution cohesion) dominant + commit
  linkage + session/agent breadth. Expresses "are we sure this is one real effort".
- `entities.confidence`: inherits the candidate's confidence at promotion, then rises
  as more evidence (commits, sessions, agents) attaches.

Bands (tunable): **high >= 0.75, medium 0.40-0.75, low < 0.40**. Bands drive
surfacing in CLI and resume. Confidence is recomputed on every evidence touch and on
every reprocess, so it always reflects current evidence + the latest corrections.

Surfacing (required):
- CLI: a tag/bar on every work item and memory, e.g. `[conf 0.82 high]` or `[####.]`.
- Retrieval/`ask`: each returned fact carries its confidence and band.
- Resume: results grouped by band; low-confidence handled per section 10.1.

---

## 6. Storage layer

[DEFAULT] SQLite system of record (`sqlite-vec` + FTS5 in-file). [FORK] DuckDB
attached read-only for timeline analytics. [FORK] graph as nodes/edges + recursive
CTEs for MVP; Kuzu behind `GraphStore` later.

### 6.1 Schema (v3 deltas marked NEW)

```sql
-- identity / sessions / turns (unchanged): projects, project_aliases, sessions, messages

-- WorkItem spine (+ confidence)
CREATE TABLE work_items (
  id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES projects(id),
  kind TEXT,                          -- feature|bugfix|refactor|migration|investigation
  title TEXT, summary TEXT,
  status TEXT,                        -- proposed|active|blocked|done|abandoned
  lifecycle TEXT,                     -- candidate|active|done|abandoned
  aliases JSON, files JSON,
  confidence REAL DEFAULT 0,          -- NEW [0,1], see 5.4
  name_locked INTEGER DEFAULT 0,      -- NEW set by rename correction
  first_seen TEXT, last_active TEXT
);

-- staging tier (+ confidence; promotion_score retired in favor of confidence)
CREATE TABLE candidate_memories (
  id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES projects(id),
  kind TEXT, title TEXT, body TEXT, status TEXT, attrs JSON,
  session_refs JSON, agent_refs JSON, first_seen TEXT, last_seen TEXT,
  confidence REAL DEFAULT 0,          -- NEW (was promotion_score)
  state TEXT DEFAULT 'candidate',     -- candidate|promoted|rejected|false_positive
  promoted_entity_id INTEGER,
  work_item_id INTEGER REFERENCES work_items(id)
);

-- ValidatedMemory (+ confidence)
CREATE TABLE entities (
  id INTEGER PRIMARY KEY, project_id INTEGER,
  kind TEXT, title TEXT, body TEXT, status TEXT, attrs JSON,
  work_item_id INTEGER REFERENCES work_items(id),
  promoted_from_candidate_id INTEGER,
  confidence REAL DEFAULT 0,          -- NEW [0,1], see 5.4
  created_at TEXT, updated_at TEXT
);
CREATE TABLE entity_evidence (entity_id INTEGER, message_id INTEGER,
  char_start INTEGER, char_end INTEGER);

-- git ground truth (unchanged): commits, files, commit_files, branches, prs
-- graph (unchanged shape): nodes(node_type includes 'workitem'), edges(rel, weight, attrs)

-- NEW: correction ledger (append-only, authoritative, replayable)
CREATE TABLE correction_ledger (
  id INTEGER PRIMARY KEY,
  project_id INTEGER REFERENCES projects(id),
  action_type TEXT,                   -- merge|split|rename|false_positive|promote|reject
  actor TEXT,                         -- 'user' | 'system'
  ts TEXT,
  affected JSON,                      -- node refs: [{type,id}] involved
  payload JSON,                       -- params: new_name, split partition, target ids
  rationale TEXT,
  inverse_of INTEGER                  -- ledger id this undoes (nullable)
);

-- NEW: derived constraints the resolver/promoter must honor (materialized from ledger)
CREATE TABLE correction_constraints (
  id INTEGER PRIMARY KEY, project_id INTEGER,
  ctype TEXT,                         -- MUST_LINK|CANNOT_LINK|PIN_NAME|FORCE_PROMOTE|FORCE_REJECT|FALSE_POSITIVE
  a_ref JSON, b_ref JSON,             -- node refs (b null for unary)
  payload JSON, source_ledger_id INTEGER, active INTEGER DEFAULT 1
);

-- NEW: graph health snapshots (time series)
CREATE TABLE graph_health_snapshots (
  id INTEGER PRIMARY KEY, project_id INTEGER, ts TEXT,
  conversion_rate REAL, merge_rate REAL, false_positive_rate REAL,
  avg_work_item_size REAL, orphan_candidate_count INTEGER,
  unresolved_related_count INTEGER, metrics JSON
);

-- retrieval indexes (unchanged + fts/vec on work_items)
CREATE VIRTUAL TABLE fts_workitems USING fts5(title, summary, aliases);
CREATE VIRTUAL TABLE vec_workitems USING vec0(embedding float[384]);
-- vec_entities, vec_chunks, fts_messages, fts_entities as before
```

---

## 7. Knowledge graph design (WorkItem hub - unchanged from v2)

Nodes: `Project, WorkItem, Decision, Todo, Bug, Architecture, Session, Commit, File,
Branch, PR`. Memory nodes appear only after promotion. The star:

```
   Decision --CONSTRAINS-->  [ WorkItem ]  <--BLOCKS-- Todo
   Bug --AFFECTS--------->   [ WorkItem ]  <--IMPLEMENTS-- Commit
   Session --CONTRIBUTES_TO->[ WorkItem ]  <--MODIFIED_FOR-- File
   WorkItem --PART_OF--> Project ; PR --DELIVERS--> WorkItem
   Decision --SUPERSEDES--> Decision ; WorkItem --RELATED--> WorkItem
```

Edges carry `weight`; node-level `confidence` lets traversal and rendering filter or
shade by trust. `RELATED` edges are the queue the health metric "unresolved
related-work-item count" watches (15).

---

## 8. Enrichment: WorkItem-scoped summaries (unchanged)

On session close, per touched WorkItem: `changed` (git diff + deterministic
extractors), `why` (decisions/architecture), `unfinished` (open BLOCKS todos,
active WorkItems, failing commands). Summaries embedded; update edges.

---

## 9. Retrieval (WorkItem-centric, confidence-aware)

1. Intent classify (resume / decision-lookup / locate-code / timeline).
2. Resolve to WorkItem(s): `vec_workitems` + `fts_workitems` (aliases catch loose
   phrasing). Rank by cosine + alias match + lifecycle + recency + git-recency, and
   return each with its **confidence**.
3. Graph-expand 1 hop along intent-relevant star edges (validated nodes only).
4. Backfill with vec/FTS over validated entities; fuse with RRF; boost by recency,
   status, centrality.
5. Every returned fact carries provenance + confidence + band. High-scoring
   candidates may be shown separately as "unconfirmed".

---

## 10. Resume Work algorithm (WorkItem-first)

Input: cwd (-> project) + optional goal.

```
1. Resolve project; capture git state (branch, head, dirty files).
2. Resolve goal -> ranked WorkItem candidates, each with confidence (section 9.2).
3. Decide single vs ambiguous (section 10.1).
4. For the chosen WorkItem(s) traverse the star (validated nodes only):
     decisions via CONSTRAINS (active, non-superseded)
     todos via BLOCKS (open) ; bugs via AFFECTS (open)
     commits via IMPLEMENTS (recent) ; sessions via CONTRIBUTES_TO (recent, any agent)
     files via MODIFIED_FOR (union current dirty tree) ; prs via DELIVERS
5. Rank each list; cap by token budget; emit bundle with confidence on the header.
```

### 10.1 Uncertainty handling (NEW - never silently collapse)

After step 2, let `c1, c2` be the top two candidates' confidences:

- **Confident** (`c1 >= high` AND `c1 - c2 >= margin`): return the single WorkItem
  bundle, header tagged with its confidence.
- **Ambiguous** (`c1 < high` OR `c1 - c2 < margin`): return an **ambiguous bundle** -
  do NOT merge the candidates into one result. List the top N WorkItems side by side
  with their confidence and distinguishing evidence (files, recent sessions), and ask
  the user to pick or to issue a `merge`/`split` correction.
- **Cold** (`c1 < low`): say so explicitly ("no confident match for 'X'"), show the
  project's most-recently-active WorkItems as starting points, and suggest creating
  one. Never fabricate a confident answer from weak signal.

```
RESUME: "continue building authentication service"   [AMBIGUOUS - 2 candidates]

  A) Implement OAuth Login        [conf 0.61 medium]  files: auth/oauth.py, auth/routes.py
       recent: 2026-06-18 (claude) Google provider wiring
  B) Add Redis Session Cache      [conf 0.58 medium]  files: auth/session.py, cache/redis.py
       recent: 2026-06-17 (cursor) session store, commit a1b2

  These are kept separate (confidence below the collapse threshold and within margin).
  Pick one:  looma resume --work A   |   merge if same effort:  looma correct merge A B
```

This is the trust guarantee: low-confidence or near-tie work is shown as distinct
options with evidence, never blended into one misleading bundle.

---

## 11. Project timeline (unchanged)

Per WorkItem: decision -> contributing sessions -> implementing commits -> delivering
PR -> affecting bug fixes -> status changes, with SUPERSEDES forks. DuckDB analytical
view. "History of feature X" resolves X to a WorkItem and renders its lane.

---

## 12. Cross-agent memory (unchanged)

One store, one project identity, agent-agnostic WorkItems. CONTRIBUTES_TO edges from
any of the six agents converge on one WorkItem; `agent_refs` feeds the multi-agent
confidence component - cross-tool agreement is itself trust evidence.

---

## 13. Human Correction Layer (NEW)

Users curate the graph; their actions are durable evidence that outranks automation.

### 13.1 Operations

| Command                              | Effect                                                                 |
|--------------------------------------|------------------------------------------------------------------------|
| `looma correct merge A B`            | Fuse two WorkItems: union aliases/files/edges, keep one canonical id    |
| `looma correct split W --into ...`   | Partition one WorkItem into two by sessions/files/aliases               |
| `looma correct rename W "Title"`     | Set title; set `name_locked=1` (auto-rename disabled)                   |
| `looma correct false-positive N`     | Mark a node a false positive: remove from graph, quarantine             |
| `looma correct promote C`            | Force a candidate memory into ValidatedMemory regardless of confidence  |
| `looma correct reject C`             | Force a candidate to `rejected`, excluded permanently                   |

Every operation: (1) appends a `correction_ledger` row (actor=`user`), (2) mutates
the graph immediately, (3) materializes `correction_constraints` consumed by future
passes. All are invertible (`looma correct undo <ledger_id>` writes an inverse row).

### 13.2 Corrections as constraints (constrained clustering)

User corrections translate into hard constraints the resolver (4.4) and promoter
(5) must honor, ranked above any numeric score:

- `merge A B` -> **MUST_LINK(A,B)**: future signals matching either go to the merged
  item; resolver may never split them automatically.
- `split W -> W1,W2` -> **CANNOT_LINK(W1,W2)** plus a partition rule: resolver must
  never re-merge them; new signals are routed by the partition.
- `rename` -> **PIN_NAME**: title frozen.
- `false-positive N` -> **FALSE_POSITIVE(N)**: node stays out of the graph on every
  rebuild unless the user reverses it.
- `promote C` / `reject C` -> **FORCE_PROMOTE / FORCE_REJECT**: pins confidence to
  1.0 / 0.0 (section 5.4).

Because constraints are consulted before scoring, a reprocess can re-derive
everything else from raw events while leaving human decisions intact. This is what
"future resolution passes must respect user corrections" means operationally.

---

## 14. Correction Ledger and reproducibility (NEW)

The `correction_ledger` is the authoritative, append-only log of curation. Combined
with raw events it fully determines the graph:

```
graph_state  =  Promote( Resolve( CachedExtract( raw_events ) ),  apply = correction_constraints )
```

- `raw_events` (messages, retained verbatim) are the immutable substrate.
- `CachedExtract` is deterministic via the content-hash extraction cache (4), so LLM
  nondeterminism does not break reproducibility; clearing the cache re-pins to the
  same hashes.
- Resolution and promotion are deterministic functions of (extractions + constraints).
- Replaying ledger constraints in `ts` order reconstructs the exact curated graph.

Consequences:
- `looma reprocess` rebuilds the entire graph from `raw_events + ledger` with no
  transcript re-ingestion; safe to re-run when thresholds change (idempotent).
- Full audit: any node's presence/name/merge is traceable to a ledger row with actor,
  timestamp, and rationale.
- The ledger may also record `actor='system'` entries (auto-merges, auto-promotions)
  for audit; these are derivable, so only the `user` rows are *required* for
  reproducibility.

---

## 15. Graph Health Metrics (NEW)

Periodic `graph_health_snapshots` (and on-demand `looma status --health`) to catch
degradation before users feel it.

| Metric                         | Definition                                                    | Degradation signal                |
|--------------------------------|---------------------------------------------------------------|-----------------------------------|
| candidate->validated conversion| validated / (validated + live candidates), windowed           | too low: extractor noisy; too high: gate too loose |
| work item merge rate           | merges / work_items_created                                   | high: resolver under-merging (fragmentation) |
| false positive rate            | user `false_positive` + `reject` / validated nodes            | rising: promotion too aggressive  |
| average work item size         | mean nodes (or contributing sessions) per active WorkItem     | shrinking: fragmentation; ballooning: over-merging |
| orphan candidate count         | candidates with no WorkItem link, aged > X days               | rising: resolver missing efforts  |
| unresolved related count       | active `RELATED` edges never merged/split                     | rising: ambiguity backlog needing curation |

Snapshots are a time series, so trends (not just absolutes) trigger alerts; defaults
ship as warning thresholds and are surfaced in `looma status --health`. These metrics
also inform threshold tuning (HIGH/T/margin) with real data rather than guesses.

---

## 16. Interfaces

- MCP server (primary): `resume_work(project?, goal?)`, `ask(query)`,
  `list_work(project, status?)`, `timeline(work_item)`, `recall(entity)`,
  `correct(action, refs, rationale?)`.
- CLI (`looma`): see section 17.
- Local daemon: watcher + ingestion + resolution + promotion + summary + health
  snapshotter.

---

## 17. CLI examples (`looma`)

```
looma resume                       # resume the most-recently-active WorkItem here
looma resume "auth service"        # WorkItem-first; may return an ambiguous bundle (10.1)
looma resume --work A              # force a specific WorkItem from an ambiguous result
looma work                         # list WorkItems with confidence + status
looma work --status active         # filter
looma ask "what did we decide about Redis caching?"   # facts carry confidence + provenance
looma timeline "OAuth Login"       # feature evolution lane
looma status                       # ingestion / project overview
looma status --health              # graph health metrics (section 15)
looma reprocess                    # rebuild graph from raw events + correction ledger
looma correct merge A B            # human correction layer (section 13)
looma correct split W --into "OAuth Login","Redis Session Cache"
looma correct rename W "Implement OAuth Login"
looma correct false-positive <node>
looma correct promote <candidate> ; looma correct reject <candidate>
looma correct undo <ledger_id>
looma ingest --once
```

Every listing line shows confidence, e.g.:
`A  Implement OAuth Login   [feature] [active] [conf 0.82 high]  files: auth/oauth.py +3`

---

## 18. Privacy, performance, failure posture (unchanged)

Local-first end to end (local extractor + embedder; remote opt-in per project +
redaction pass). Idempotent, resumable ingestion. Defensive adapters with raw_json +
schema versions. Deterministic extraction free/always-on; LLM extraction windowed,
content-hash cached, tool-noise skipped. Promotion gate + confidence bands cap graph
growth and keep traversal/embedding cost bounded.

---

## 19. MVP roadmap

- Phase 0 - Skeleton (done): schema, NormalizedEvent, project identity, Claude
  adapter, FTS5 over messages.
- Phase 1 - WorkItems + candidates + git + **confidence**: deterministic + LLM
  extractors -> candidates; entity dedup + WorkItem resolution; promotion with the
  5.4 confidence formula surfaced in CLI. Exit: correct WorkItems with confidences;
  single-session noise stays in staging.
- Phase 2 - Graph + resume + **uncertainty + corrections**: nodes/edges star;
  WorkItem-first resume with 10.1 ambiguity handling; Human Correction Layer +
  Ledger (13-14); `reprocess` rebuild. Exit: a wrong merge is fixable and survives
  reprocess.
- Phase 3 - Cross-agent + timeline + **health**: 5 more adapters; DuckDB attach;
  timeline; MCP server; Graph Health Metrics + `status --health` (15). Exit: a
  Cursor session and a Claude commit attach to one WorkItem; health snapshot renders.
- Phase 4 - Hardening: watcher daemon, incremental long-session extraction, candidate
  GC, optional rerank, secret redaction, Kuzu swap if needed, minimal local UI.

---

## 20. Migration plan from v2

Pre-implementation, so additive schema + reprocess (no risky backfill).

1. Additive schema: add `confidence` to `work_items`/`entities`/`candidate_memories`
   (rename the planned `promotion_score` to `confidence`); add `name_locked`; add
   `correction_ledger`, `correction_constraints`, `graph_health_snapshots`. Nothing
   dropped.
2. Backfill `confidence` by running the 5.4 formula over existing candidates/entities
   /work_items (deterministic from current evidence).
3. No ledger backfill needed (empty initially). `reprocess` already rebuilds from raw
   events; it now also applies the (empty) constraint set.
4. Rollback: additive only; ignore the new columns/tables and confidence defaults to 0.

---

## 21. Implementation impact assessment

| Change                    | Touches                                              | Effort | Phase | Risk / notes                                   |
|---------------------------|-----------------------------------------------------|--------|-------|------------------------------------------------|
| Confidence columns        | 3 tables + migration (additive)                     | S      | 1     | Low; defaults to 0                             |
| Confidence scoring (5.4)  | promotion engine (replace score calc), recompute hooks| M     | 1     | Low-med; isolate weights as tunable constants  |
| Surface confidence        | CLI formatter, retrieval result schema, resume header| S     | 1-2   | Low; additive to output                        |
| Resume uncertainty (10.1) | resume engine branch on c1/c2 + margin; ambiguous bundle renderer | M | 2 | Med; needs `margin`/band tuning; pure logic    |
| Correction Layer (13)     | new `correct` CLI/MCP verbs, graph mutators (merge/split/rename/fp/promote/reject) | L | 2 | **Highest**: split/merge mutate edges; keep invertible via ledger |
| Correction constraints    | resolver (4.4) + promoter (5) read constraints before scoring | M | 2 | Med; constrained-clustering gate; ordering matters |
| Correction Ledger (14)    | new table, append on every correction, undo via inverse rows | S-M | 2 | Low-med; append-only simplifies                |
| Reproducible reprocess    | `reprocess` applies ledger constraints in ts order  | M      | 2     | Med; relies on extraction cache for determinism|
| Graph Health Metrics (15) | snapshotter job, 6 metric queries, `status --health`| M      | 3     | Low; read-only over existing tables            |
| Rename memos -> looma     | CLI entrypoint, docs, MCP tool labels               | S      | any   | Trivial; string/binary rename                  |

Critical path / sequencing: confidence (Phase 1) is a prerequisite for both the
uncertainty-aware resume and the correction force-promote/reject semantics, so it
lands first. The Correction Layer is the largest and riskiest unit (it is the only
subsystem that *mutates* an existing graph rather than appending), so it is built
behind the ledger from day one - every mutation is a replayable, invertible ledger
row, which also delivers reproducibility for free. Health Metrics are read-only and
can trail into Phase 3 without blocking anything. No item expands scope beyond the
six requirements; local-first and WorkItem-first retrieval are preserved throughout.
```
