# Public release checklist - Looma v0.1.0-alpha.1

## 1. Code & tests
- [x] Full test suite passes (`python3 -m unittest discover -s tests -t .`, 44 tests)
- [x] Package byte-compiles cleanly
- [x] `pip install -e .` verified in a clean virtualenv (see INSTALL_VERIFICATION.md)
- [x] `looma` binary exposed by the install
- [x] Zero third-party runtime dependencies

## 2. Install & first-run verified
- [x] `looma doctor` reports correctly on a fresh dir
- [x] `init` -> `ingest --limit 25` -> `work` flow runs clean in a fresh venv
- [x] Friendly empty states + clear errors

## 3. Docs verified
- [x] README follows the agreed structure; Works-Today vs Planned separated
- [x] RELEASE_ALPHA.md / IMPLEMENTATION_NOTES.md / CONTRIBUTING.md present
- [x] SAMPLE_OUTPUT.md is synthetic (no private content)
- [x] CHANGELOG.md written for v0.1.0-alpha.1
- [x] Positioning audit: no "AI memory" / "second brain" / "RAG" as positioning

## 4. Release audit
- [x] RELEASE_AUDIT.md generated; transcript-content leak found and fixed
- [x] No secrets / API keys / tokens
- [x] Machine-specific stats genericized; private repo names removed

## 5. Repo hygiene
- [x] `.gitignore` excludes store (`*.db`, `.looma/`), `__pycache__`, `*.egg-info`, build
- [x] LICENSE finalized: MIT; `license` set in pyproject.toml
- [x] ARCHITECTURE.md included in repo; relative links fixed
- [x] Pre-push gate run (`git ls-files` clean of db/pycache/egg-info)

## 6. GitHub release
- [x] Repo created/public at github.com/devYRPauli/looma
- [x] `main` pushed
- [x] Description + topics set
- [x] Tag `v0.1.0-alpha.1` pushed (pre-release)
- [x] GitHub release created from GITHUB_RELEASE.md

## 7. Optional polish (not blocking launch)
- [ ] Screenshots added to `docs/screenshots/`
- [ ] Demo GIF added to `docs/demo/` and embedded in README

## Remaining human action
- [ ] **Post the launch tweet** (pick a variant from LAUNCH_TWEET.md, add the repo link)

---

Everything above the "Remaining human action" line is done. The only step left to
launch is posting the tweet; screenshots/GIF are nice-to-have polish you can add any
time after.
