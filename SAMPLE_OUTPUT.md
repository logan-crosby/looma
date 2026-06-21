# Sample output

The CLI formatting below is exactly what Looma prints. The **project, paths, and
content are a synthetic, representative example** - not from any real private repo -
so this file is safe to publish. Looma has been exercised at real scale (hundreds
of sessions and tens of thousands of messages across a dozen projects); the
per-command examples here use a made-up `acme-web` project to protect transcript
privacy.

## `looma doctor`

```
looma doctor

  [ OK ]  Python version     3.12.1
  [ OK ]  SQLite FTS5        available
  [ OK ]  Looma data dir     writable: /home/you/.looma
  [ OK ]  Database           /home/you/.looma/looma.db (4096 KB)
  [ OK ]  Claude history     128 transcript files under /home/you/.claude/projects
  [ OK ]  Current git repo   /home/you/code/acme-web  remote=github.com/acme-co/acme-web

Local-first: your transcript contents never leave this machine. No cloud, no API key.
```

## `looma status`

```
looma status
  db:         /home/you/.looma/looma.db
  projects:   3
  sessions:   41
  messages:   6188
  work items: 12
  memories:   214 candidate (63 promoted -> 63 validated)
  commits:    18

  current dir -> acme-web (github.com/acme-co/acme-web)
```

## `looma work`

```
WorkItems for acme-web (github.com/acme-co/acme-web)   [3 items]

  #3    Implement OAuth Login
       feature · active · conf 0.76 (high) · last 2026-06-18 · 9 files
       files: auth/oauth.py, auth/routes.py, auth/session.py ...
  #7    Add Redis Session Cache
       feature · active · conf 0.58 (medium) · last 2026-06-17 · 4 files
       files: cache/redis.py, auth/session.py, config/settings.py ...
  #5    Fix Checkout Total Rounding
       bugfix · active · conf 0.41 (medium) · last 2026-06-15 · 3 files
       files: checkout/totals.py, checkout/tax.py ...
```

## `looma resume "auth"`  (confident match -> full bundle)

```
PROJECT: acme-web (github.com/acme-co/acme-web)
         branch feature/oauth, head 9f3a1c2bd, 3 dirty
GOAL: auth

[CONFIDENT MATCH]

  WORKITEM #3: Implement OAuth Login
    feature · active · conf 0.76 (high)

  CONSTRAINTS (decisions / architecture)
    - Use JWT over opaque tokens for stateless verification
    - Sessions cached in Redis, not in-process memory

  UNFINISHED / BLOCKING
    [ ] refresh-token rotation not implemented yet
    [ ] failing test: test_oauth_callback_state

  AFFECTING BUGS
    (!) callback state param dropped on redirect

  RECENT SESSIONS
    - 2026-06-18  claude/claude-opus-4-8
    - 2026-06-17  claude/claude-opus-4-8

  COMMITS
    - 9f3a1c2bd Wire Google provider into OAuth login flow
    - a1b2c3d4e Add Redis-backed session store

  FILES FOR THIS WORK
    auth/oauth.py, auth/routes.py, auth/session.py, tests/test_oauth.py

  NEXT LIKELY STEP: address todo: refresh-token rotation not implemented yet
```

## `looma resume "session cache"`  (ambiguous -> alternatives kept separate, not collapsed)

```
PROJECT: acme-web (github.com/acme-co/acme-web)
         branch feature/oauth, head 9f3a1c2bd
GOAL: session cache

[AMBIGUOUS - kept separate, not collapsed]

  WORKITEM #7: Add Redis Session Cache
    feature · active · conf 0.58 (medium)

  CONSTRAINTS (decisions / architecture)
    - Sessions cached in Redis, not in-process memory

  RECENT SESSIONS
    - 2026-06-17  claude/claude-opus-4-8

  COMMITS
    - a1b2c3d4e Add Redis-backed session store

  FILES FOR THIS WORK
    cache/redis.py, auth/session.py, config/settings.py

  NEXT LIKELY STEP: continue editing cache/redis.py

  OTHER CANDIDATE WORK ITEMS (not merged):
    #3 Implement OAuth Login  [conf 0.76 (high)]

  Narrow with:  looma resume --project <key> '<more specific goal>'
```
