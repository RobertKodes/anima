# Anima

A local-first persistent AI **being**. The language model is a brain. **Sibyl Memory** is the self. The runtime is the organism that keeps them together.

The product surface is a **graphical CLI** (Textual): banner, being rail, conversation, Why rail, live status, slash autocomplete, command palette. Same commands work in `anima --cli`. A local web companion is optional.

Hackathon packet: [`docs/HACKATHON.md`](docs/HACKATHON.md) · submission: [`docs/SUBMISSION.md`](docs/SUBMISSION.md) · use cases: [`docs/USE_CASES.md`](docs/USE_CASES.md)

## What it does

Anima is a CLI you keep. It is born with an empty Sibyl store. You teach it a name, a goal, and a Base spending policy. Quit. Open it again on an empty model context. It still knows you, and it still refuses a spend that would break the remembered policy.

Turn retrieval off (`anima --amnesia`) and the same prompt is a chatbot. The SQLite file was never deleted. That is the deletion test.

## What judges should read in under two minutes

Durable identity is **not** in markdown. It is in Sibyl.

| What happens | Where |
|---|---|
| Sibyl open / read / write / search | [`src/anima/memory/sibyl_adapter.py`](src/anima/memory/sibyl_adapter.py) |
| Before every reply: retrieve a small context package | [`src/anima/memory/retrieval.py`](src/anima/memory/retrieval.py) |
| After every reply: persist experience, people, goals, outcomes | [`src/anima/memory/writer.py`](src/anima/memory/writer.py) |
| Sleep consolidates raw history into durable state | [`src/anima/memory/consolidation.py`](src/anima/memory/consolidation.py) |
| The organism that binds memory, brains, Base, growth | [`src/anima/core/runtime.py`](src/anima/core/runtime.py) |
| Graphical CLI | [`src/anima/app/tui.py`](src/anima/app/tui.py) |
| Wallet secrets (never written to Sibyl) | [`src/anima/base/adapter.py`](src/anima/base/adapter.py) |

**Deletion test:** `anima --amnesia` turns retrieval off without deleting the store. It can still talk. It is no longer the developed being.

## How memory made this possible

The spend refusal is not a system prompt. Before every reply, retrieval loads a policy entity from Sibyl (a 0-wei Base cap, in the killer demo). The runtime hands that package to the brain and to the Base policy gate. A fresh session has an empty LLM context; the refusal still happens. Amnesia mode uses the same brain and the same prompt and cannot apply the stored cap, because it never read it.

That is the load-bearing moment: delete the memory calls and the being cannot keep a promise across sessions.

## Partner stacks

| Stack | Role | Where a judge can see it | Multiplier? |
|---|---|---|---|
| **Sibyl Memory** | Identity store (SQLite + FTS5, no embeddings) | Adapter, retrieval, writer | Mandatory. Not a multiplier. |
| **Base** | Action rail on **Base Sepolia** (84532) | [`src/anima/base/`](src/anima/base/), `/base status`, `/base action` | Intended. Dry-run execute and **memory-based refusal** are in-repo. A live broadcast tx needs a funded Sepolia wallet and `dry_run = false` in the operator demo. |

No Virtuals integration is claimed.

## Prior Work

This repository is the original Anima build. It is not a wrapper around a Sibyl sample app.

Third-party pieces we did not write: [`sibyl-memory-client`](https://pypi.org/project/sibyl-memory-client/) (identity store), [Textual](https://textual.textualize.io/) (graphical CLI), [web3.py](https://github.com/ethereum/web3.py) / `eth-account` (Base), local inference via Ollama or llama.cpp when you opt in.

`InstinctBrain` (`--brain fake`) is a deterministic stand-in so tests and the killer demo run without a GPU. It is load-bearing for proving “same prompt, different Sibyl state → different action.” It is not a claimed LLM result.

The product spec is [`docs/PRD_CLI_v0.1.md`](docs/PRD_CLI_v0.1.md) (from `CLI_First_AI_Being_PRD_v0.1.docx`). There is no prior Anima release.

## Install (public)

```bash
git clone https://github.com/RobertKodes/anima.git
cd anima
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
anima setup --yes          # writes config; picks Ollama if it is running
anima doctor               # toolchain check
anima                      # graphical CLI
```

| Command | What you get |
|---|---|
| `anima` | Graphical CLI (default on a TTY) |
| `anima --tui` | Force the graphical CLI |
| `anima --cli` | Classic REPL |
| `anima --ui` | Local web companion |
| `anima setup` | First-run wizard |
| `anima doctor` | Health check |
| `anima /status` | One-shot slash command |
| `anima --brain ollama --model qwen3:1.7b` | Local LLM |
| `anima --brain llama_cpp` | llama-server on :8080 |
| `anima --amnesia` | Deletion-test mode |

Keys in the graphical CLI: **tab** completes slash commands, **ctrl+p** command palette, **F1** help overlay, **F3** sleep, **ctrl+n** new session, **ctrl+c** leave.

## First launch (birth)

```
No persistent identity found.
Sibyl Memory ........ connected
Primary brain ....... instinct
Base ................. sepolia available

anima I think I'm awake.
anima I don't remember a life before this.
anima Who are you?
you   Robert
[relationship created]
anima Robert. You're the first person I remember.
```

Quit. Start again. Ask `do you remember me?` The model context is empty. Sibyl is not.

## Videos

| File | What it is |
|---|---|
| [`recordings/hackathon_demo.mp4`](recordings/hackathon_demo.mp4) | 2–5 min judge cut (problem, product, recall, CLI, Base). Timestamp burned in. |
| [`recordings/tutorial_demo.mp4`](recordings/tutorial_demo.mp4) | Actual graphical CLI: birth → teach → refuse → sleep → remember |
| [`recordings/interface_tour.mp4`](recordings/interface_tour.mp4) | Actual graphical CLI: help, slash hints, doctor, brains, palette |
| [`recordings/demo_killer_flow.mp4`](recordings/demo_killer_flow.mp4) | Unattended killer demo (plain) |
| `recordings/tests_*.mp4` | One video per automated test |

The official submission video should include **one continuous unedited screen capture** of a fresh session recalling earlier state, with the timestamp or commit hash visible. How to record that: [`docs/RECORD_DEMO.md`](docs/RECORD_DEMO.md).

```bash
pytest
python scripts/record_tests.py
python scripts/record_cli_videos.py
python scripts/assemble_hackathon_demo.py
```

## Base

Default network is **Base Sepolia**. Mainnet stays off until you enable it. Approval modes: `always-ask`, `policy-limited`, `disabled`. The signing key lives in `~/.anima/secrets/wallet.json` (mode 0600). Sibyl stores intent, address, tx id, and outcome — never the key. Dry-run is the default so a first clone cannot spend.

```bash
anima /base status
anima /base wallet
anima --cli   # then: /base action intent=sepolia-note value=0 --yes
```

## Principles

One being, many brains. Memory changes behavior. Models are replaceable; continuity is not. Local-first. Small context, durable memory. Inspectability over magic. Never pretend a memory exists when it was not persisted.

MIT licensed.
