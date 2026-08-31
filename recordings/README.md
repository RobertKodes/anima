# Recordings

Professional 1080p demo videos — real Textual TUI (vector SVG capture) and plain `--cli` REPL.

| File | What it is |
|---|---|
| `hackathon_demo.mp4` | Full judge cut: title cards + TUI recall + plain CLI + interface tour + amnesia |
| `tutorial_demo.mp4` | TUI killer flow with intro/outro (memory recall beat) |
| `recall_beat.mp4` | TUI only — birth → teach → refuse → sleep → remember (best for form URL) |
| `plain_cli_demo.mp4` | Plain `--cli` with live token streaming frames |
| `demo_killer_flow.mp4` | Plain CLI killer flow (no intro card) |
| `interface_tour.mp4` | TUI: help, doctor, brains, base, skills, palette |
| `amnesia_demo.mp4` | TUI deletion test (`--amnesia`) |

## Regenerate (all platforms)

```bash
pip install -e ".[dev]"
python scripts/record_all_demos.py
```

Or step by step:

```bash
python scripts/record_cli_videos.py   # TUI demos
python scripts/record_plain_cli.py    # plain CLI demo
python scripts/assemble_hackathon_demo.py
```

Requires **ffmpeg** on PATH, or `imageio-ffmpeg` (bundled binary via pip).

Uses **svg2png-py** to rasterize real Textual SVG screenshots at 1080p — not terminal screen scrapes or fake text frames for the TUI.
