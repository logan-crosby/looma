# Demo (GIF + video)

Place the animated GIF and the short demo video here:

- `looma-demo.gif`   - the hero asset for the README and the launch tweet
- `looma-demo.mp4`   - 30-60s screen recording for the GitHub release / social

## The recording (recommended command sequence)

Record this exact flow - it tells the whole story in under a minute and stays
honest about the alpha (the `--limit` keeps it fast and the timing line is real):

```bash
looma doctor
looma ingest --once --limit 25 --verbose
looma work
looma resume "auth"
```

Beats to land:
1. `doctor` -> all green, "transcripts stay local" (trust).
2. `ingest --limit 25 --verbose` -> counts + a real timing line (it actually works).
3. `work` -> WorkItems with confidence tags (the model).
4. `resume "auth"` -> the reconstructed bundle: constraints, unfinished, bugs,
   commits, files, next step (the payoff). Pause on this frame.

Keep it to ~45s. Do not speed-edit away the empty/low-confidence honesty - showing
a `[LOW CONFIDENCE]` banner is a feature, not a blemish.

## Making the GIF

Record with [asciinema](https://asciinema.org/) and convert with
[agg](https://github.com/asciinema/agg), or screen-record and convert:

```bash
# asciinema route (crisp, small files)
asciinema rec looma.cast -c "bash docs/demo/demo_script.sh"
agg looma.cast looma-demo.gif

# screen-capture route
# record looma-demo.mp4, then:
ffmpeg -i looma-demo.mp4 -vf "fps=12,scale=900:-1:flags=lanczos" looma-demo.gif
```

A ready-to-run `demo_script.sh` is included in this folder.

## Embedding (after adding assets)

```markdown
![Looma demo](docs/demo/looma-demo.gif)
```

(Placeholder file - delete this note once the real GIF/video are added.)
