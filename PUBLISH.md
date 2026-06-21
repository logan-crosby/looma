# Publish - exact commands

The repo for the alpha is `github.com/devYRPauli/looma`. Run these from the `looma/`
directory (the package root, which becomes the repo root).

## 1. Initialize and commit

```bash
git init
git branch -M main
git add .
git status            # sanity-check what is staged (see the gate below)
git commit -m "v0.1.0-alpha.1"
```

### Pre-push gate (do not skip)

```bash
# nothing private/build-junk should be tracked:
git ls-files | grep -Ei '\.db$|__pycache__|egg-info|/build/|/dist/' && echo "STOP: junk staged" || echo "clean"
git grep -niE '/Users/|/home/[a-z]' -- . && echo "STOP: absolute home paths" || echo "clean"
```

## 2. Create the GitHub repo and push

With the GitHub CLI (creates the repo and pushes `main` in one step):

```bash
gh repo create devYRPauli/looma --public --source . --remote origin --push \
  --description "Looma turns coding-agent history into resumable project context."
```

Or manually, if the repo already exists:

```bash
git remote add origin https://github.com/devYRPauli/looma.git
git push -u origin main
```

## 3. Tag the release

```bash
git tag v0.1.0-alpha.1
git push origin v0.1.0-alpha.1
```

## 4. Create the GitHub release (pre-release)

```bash
gh release create v0.1.0-alpha.1 \
  --title "Looma v0.1.0-alpha.1 - first public alpha" \
  --notes-file GITHUB_RELEASE.md \
  --prerelease
```

(Or paste the release body from `GITHUB_RELEASE.md` into the GitHub UI.)

## 5. Set topics (optional)

```bash
gh repo edit devYRPauli/looma \
  --add-topic claude-code --add-topic developer-tools --add-topic local-first \
  --add-topic sqlite --add-topic productivity --add-topic git \
  --add-topic agent-memory --add-topic python
```

## 6. Launch

Post one of the variants from `LAUNCH_TWEET.md` with the repo link (and the demo
GIF once recorded).
