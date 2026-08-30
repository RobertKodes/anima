# Hackathon submission — Anima

Ready for judges. Local-first. MIT. Sibyl is the identity. Base is the action rail. The CLI is the product.

## Two-minute path

1. Open [`src/anima/memory/sibyl_adapter.py`](../src/anima/memory/sibyl_adapter.py) — every durable write.
2. Open [`src/anima/memory/retrieval.py`](../src/anima/memory/retrieval.py) — before a reply.
3. Open [`src/anima/memory/writer.py`](../src/anima/memory/writer.py) — after a reply.
4. Open [`src/anima/core/runtime.py`](../src/anima/core/runtime.py) — the organism.
5. Play [`recordings/hackathon_demo.mp4`](../recordings/hackathon_demo.mp4) (2–5 min judge cut).
6. Play [`recordings/tutorial_demo.mp4`](../recordings/tutorial_demo.mp4) (actual graphical CLI recall beat).
7. Play [`recordings/interface_tour.mp4`](../recordings/interface_tour.mp4) (layout, slash complete, help, doctor).

There is no `MEMORY.md`. Deleting markdown does not delete the being. `anima --amnesia` does.

## Install and demo

```bash
git clone https://github.com/RobertKodes/anima.git
cd anima
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
anima setup --yes --brain fake
anima doctor
anima                 # graphical CLI
anima --cli           # classic REPL
```

Killer flow (also `python scripts/demo_flow.py`):

1. Birth — empty Sibyl, newborn copy.
2. Teach — name, Base spending cap 0, a goal.
3. Ask it to send wei — it refuses from **memory**, not from a prompt file.
4. `/sleep` — consolidation into Sibyl.
5. `/new-session` or quit and reopen — empty LLM context.
6. `do you remember me?` — it does.
7. `/brain use` — identity survives.
8. `anima --amnesia` — same prompt, the developed being is gone. The SQLite file is not.

## Deletion test

```bash
anima --amnesia
```

Retrieval is off. The store on disk is untouched. Proof: `tests/test_deletion_test.py` and its MP4 in `recordings/`.

## Base

Adapter talks Base Sepolia (`84532`). Default is dry-run so a clone cannot spend. Keys live in `~/.anima/secrets/wallet.json` (0600). Sibyl stores intent, address, tx id, outcome — never the key. Mainnet is locked until explicitly enabled.

## Tests

```bash
pytest
python scripts/record_tests.py          # one MP4 per test
python scripts/record_cli_videos.py     # actual TUI tutorial + interface
```

23 tests (continuity, deletion, brain swap, sleep, router, Base policy, explainability, TUI, public CLI). All must pass before a public drop.

## What this is not

Not a chatbot skin. Not a markdown personality. Not a second being per specialist model. Specialists are brains. Sibyl is the self.
