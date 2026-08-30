# Submission packet

Anima is ready to submit once the public GitHub URL exists. This page is the operator checklist.

## Repo

- License: MIT (`LICENSE`)
- Identity store: Sibyl Memory (`sibyl-memory-client`), SQLite + FTS5, no embeddings
- No `MEMORY.md` / `PERSONALITY.md` / `USER.md` as identity
- Graphical CLI is the default product surface (`anima`)
- README includes the two-minute path, partner stacks, “how memory made this possible”, and Prior Work

## Judge path (< 2 minutes)

1. [`src/anima/memory/sibyl_adapter.py`](../src/anima/memory/sibyl_adapter.py)
2. [`src/anima/memory/retrieval.py`](../src/anima/memory/retrieval.py)
3. [`src/anima/memory/writer.py`](../src/anima/memory/writer.py)
4. [`src/anima/core/runtime.py`](../src/anima/core/runtime.py)
5. Videos: [`recordings/hackathon_demo.mp4`](../recordings/hackathon_demo.mp4), [`recordings/tutorial_demo.mp4`](../recordings/tutorial_demo.mp4)

## Clone and run

```bash
git clone <PUBLIC_REPO_URL>
cd anima
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
anima setup --yes --brain fake    # or --brain ollama
anima doctor
anima
```

Killer demo (unattended): `python scripts/demo_flow.py`

## Scoring evidence

| Gate | Evidence |
|---|---|
| Fresh-session continuity | `tests/test_memory_continuity.py` + tutorial video |
| Memory changes a decision | Base refuse after stored 0-wei policy |
| Deletion test | `anima --amnesia` / `tests/test_deletion_test.py` |
| Brain swap | `tests/test_brain_swap.py` |
| Sleep | `tests/test_sleep.py` + `/sleep` in the TUI |
| Base | Adapter + policy + dry-run execute; live Sepolia needs a funded wallet (`dry_run = false`) |
| Secret hygiene | Wallet file 0600; keys never in Sibyl |
| CLI product | Graphical TUI with slash complete, palette, Why rail |

## What you still do as the operator

1. If `gh auth status` is invalid: `gh auth refresh -h github.com`, then the commands in [`PUBLISH.md`](PUBLISH.md).
2. Prefer an unedited 2–5 min screen capture of the recall beat ([`RECORD_DEMO.md`](RECORD_DEMO.md)).
3. Optional multiplier: fund a Base Sepolia wallet, set `dry_run = false`, run `/base action intent=sepolia-note value=0 --yes` in the live video.
4. Post the two drafts in [`POSTS.md`](POSTS.md) tagging **@sibylcap** and **@base**.
5. Open your private build-page link from registration and mark ready before **10 Sep 2026, 23:59 UTC**. Registration itself closes **31 Aug 2026**.

## Tests

```bash
pytest          # 23 passed as of this packet
python scripts/hackathon_smoke.py
```
