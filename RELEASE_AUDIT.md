# Release audit - Looma v0.1.0-alpha.1

Final pre-publish scan for anything that should not go into a public repo. Run
before the first commit so nothing sensitive enters git history.

## Summary

One real issue (private transcript content in the sample output) - **fixed**. No
secrets. Build artifacts exist on disk but are excluded by `.gitignore`.

## Findings

| Category                     | Found | Files affected                         | Fix applied                                                |
|------------------------------|-------|----------------------------------------|------------------------------------------------------------|
| Accidental transcript content| YES   | `SAMPLE_OUTPUT.md`                      | Rewritten with a synthetic `acme-web` example; zero real content. |
| Private repository names     | YES   | `SAMPLE_OUTPUT.md` (real private repo)  | Removed; replaced with `github.com/acme-co/acme-web`.      |
| Machine-specific stats       | YES   | `README.md`, `RELEASE_ALPHA.md`, `IMPLEMENTATION_NOTES.md`, `SAMPLE_OUTPUT.md` | Exact session/message counts genericized to "hundreds of sessions across a dozen projects". |
| Hardcoded local paths        | MINOR | `SAMPLE_OUTPUT.md`, `IMPLEMENTATION_NOTES.md` | Sample paths replaced with `/home/you/...`; a literal `/private/tmp` note generalized. `docs/demo/demo_script.sh` uses an intentional `/tmp` demo path (kept). |
| Usernames                    | OK    | `README`, `CONTRIBUTING`, `LICENSE`, `pyproject` | Only the repo owner's public GitHub handle (`devYRPauli`) - intentional, not a leak. |
| Secrets / API keys / tokens  | NONE  | -                                      | Grep for `ghp_/sk-/AKIA/api_key/password/secret/bearer` returned nothing. |
| Committed databases (`*.db`) | NONE  | -                                      | No `.db` in the repo tree; `.gitignore` excludes `*.db`/`-wal`/`-shm`/`.looma/`. |
| `__pycache__`                | on disk | several dirs                         | Present from local runs; excluded by `.gitignore` (`__pycache__/`). |
| `.egg-info`                  | on disk | `looma.egg-info/`                     | From `pip install -e .`; excluded by `.gitignore` (`*.egg-info/`). |
| Build artifacts (build/dist) | NONE  | -                                      | None present; `.gitignore` covers them anyway.             |

## How transcript leakage was caught

The Phase 1 `SAMPLE_OUTPUT.md` was generated from a real run and contained a private
project's name, real TODO text, commit messages, and file paths. Because Looma's
output by design surfaces real project content, **any committed sample must be
synthetic.** It now is, and is labeled as such at the top of the file.

## Remaining manual checks (do at publish time)

- [ ] Review `git ls-files` after `git add .` - confirm only intended files are
      staged (no `*.db`, `__pycache__`, `*.egg-info`, demo DBs).
- [ ] Skim the staged `SAMPLE_OUTPUT.md` once more to confirm it reads as obviously
      synthetic.
- [ ] If you later add real screenshots/GIF under `docs/`, redact paths and private
      project names in them before committing.
- [ ] Confirm the GitHub repo is created under your own account and is the intended
      visibility.

## Verification commands used

```bash
# artifacts
find . \( -name __pycache__ -o -name '*.egg-info' -o -name '*.db' -o -name build -o -name dist \)
# private refs / paths (substitute your own username / private repo names)
grep -rniE "<your-username>|<private-repo-names>|/Users/|/home/" --include='*.md' .
# secrets
grep -rnEi "ghp_[A-Za-z0-9]+|sk-[A-Za-z0-9]+|AKIA[0-9A-Z]{16}|api[_-]?key=|password=|secret=" .
```
