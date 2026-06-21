# Screenshots

Drop terminal screenshots here and reference them from the top-level README.

## What to capture

Use a clean terminal (large readable font, dark theme, ~100 cols), in a real repo
with Claude Code history. Capture these four, named exactly so the README can embed
them later:

| File                  | Command                        | Why it sells the project                       |
|-----------------------|--------------------------------|------------------------------------------------|
| `01-doctor.png`       | `looma doctor`                 | Credibility: all-green env checks, "stays local"|
| `02-work.png`         | `looma work`                   | WorkItems with confidence + recent files        |
| `03-resume-auth.png`  | `looma resume "auth"`          | The payoff: reconstructed, git-anchored context |
| `04-status.png`       | `looma status`                 | Scale: sessions/messages/projects indexed       |

## Tips

- Run `looma ingest --once --limit 25` first so output is fast and bounded.
- Prefer a repo where `resume` returns a real WorkItem (a feature/bugfix you
  actually worked on with the agent).
- Redact anything sensitive before publishing (paths, private repo names).
- Keep images under ~1 MB; PNG, not screenshots-of-screenshots.

## Embedding (after adding images)

```markdown
![looma resume](docs/screenshots/03-resume-auth.png)
```

(Placeholder file - delete this note once real screenshots are added.)
