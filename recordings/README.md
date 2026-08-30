# Recordings

Actual graphical CLI (Textual) plus one file per automated test.

| File | What it is |
|---|---|
| `hackathon_demo.mp4` | 2–5 min judge cut (title cards + TUI clips + timestamp) |
| `tutorial_demo.mp4` | Live TUI: birth → Robert → spend policy → goal → Base refusal → sleep → remember |
| `interface_tour.mp4` | Live TUI: F1 help, slash hints, `/doctor`, `/brains`, `/base`, command palette |
| `demo_killer_flow.mp4` | Unattended plain-CLI killer demo |
| `tests_*.mp4` | One video per pytest |

Regenerate:

```bash
pytest
python scripts/record_tests.py
python scripts/record_cli_videos.py
python scripts/assemble_hackathon_demo.py
```
