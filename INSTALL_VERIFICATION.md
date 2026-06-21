# Clean install verification

Verified Looma installs and runs from a **fresh virtual environment** with no
pre-existing state. Real paths and project names below are redacted for privacy;
the commands, exit codes, and counts are from the actual run.

## Procedure

```bash
python3 -m venv /tmp/looma-verify-venv
source /tmp/looma-verify-venv/bin/activate
export LOOMA_DB=/tmp/looma-verify/looma.db   # isolated; never touches your real store

cd looma
pip install -e .
looma doctor
looma init
looma ingest --once --limit 25
looma work
```

## Results

| Step                     | Exit | Observation                                                        |
|--------------------------|------|--------------------------------------------------------------------|
| `python -m venv` + `pip install -e .` | 0 | Installed; `looma` binary exposed at `<venv>/bin/looma`. Zero third-party deps pulled. |
| `looma doctor`           | 0    | Python OK, SQLite FTS5 OK, data dir writable, Claude history found; DB and git-repo show WARN (expected: DB not yet created, run from a non-repo dir). |
| `looma init`             | 0    | Database created at the configured path; "stays local" notice shown. |
| `looma ingest --once --limit 25` | 0 | Ingested 25 sessions / ~31k messages; indexed 6 projects; built 24 work items, 417 candidate memories, 106 promoted to validated memory. |
| `looma work --project <key>` | 0 | Listed WorkItems for the resolved project with confidence tags.   |

## Sample (redacted) output

```
$ looma doctor
  [ OK ]  Python version     3.12.12
  [ OK ]  SQLite FTS5        available
  [ OK ]  Looma data dir     writable: /tmp/looma-verify
  [WARN]  Database           not created yet (run `looma init`)
  [ OK ]  Claude history     <N> transcript files under /home/you/.claude/projects
  [WARN]  Current git repo   <cwd> is not a git repo (path-key fallback used)

$ looma init
Initialized looma at /tmp/looma-verify/looma.db

$ looma ingest --once --limit 25
Ingested 25 sessions, 31462 new messages
Indexed:  6 projects, 24 sessions, 31462 messages
Built:    24 work items, 417 candidate memories, 106 promoted to validated memory

$ looma work --project <key>
WorkItems for <project> (<key>)   [2 items]
  ...
```

## Environment

- Python 3.12 (project requires >= 3.10).
- macOS; standard-library SQLite with FTS5 available.
- No network access required; no API keys; no third-party runtime dependencies.

## Conclusion

A fresh `pip install -e .` yields a working `looma` binary, and the
doctor -> init -> ingest -> work flow completes cleanly. The unit suite
(`python3 -m unittest discover -s tests -t .`, 44 tests) also passes.
