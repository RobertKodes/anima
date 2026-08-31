# Hackathon submission — Anima

Ready for judges. Local-first. MIT. **Sibyl Memory is identity.** Base is the action rail. The CLI is the product.

**Live site:** https://robertkodes.github.io/anima/  
**Repo:** https://github.com/RobertKodes/anima

## Two-minute path

1. Open [`docs/SIBYL.md`](SIBYL.md) — architecture diagram for judges.
2. Open [`src/anima/memory/sibyl_adapter.py`](../src/anima/memory/sibyl_adapter.py) — every durable write.
3. Open [`src/anima/memory/retrieval.py`](../src/anima/memory/retrieval.py) — before a reply.
4. Open [`src/anima/memory/writer.py`](../src/anima/memory/writer.py) — after a reply.
5. Open [`src/anima/mcp/sibyl_bridge.py`](../src/anima/mcp/sibyl_bridge.py) — in-process Sibyl MCP (same store as chat).
6. Open [`src/anima/core/runtime.py`](../src/anima/core/runtime.py) — the organism.
7. Play [`recordings/hackathon_demo.mp4`](../recordings/hackathon_demo.mp4) (2–5 min judge cut).
8. Play [`recordings/amnesia_demo.mp4`](../recordings/amnesia_demo.mp4) (deletion test — store untouched).

There is no `MEMORY.md`. Deleting markdown does not delete the being. `anima --amnesia` does.

## Sibyl Memory integration

| Layer | File | What judges should see |
|-------|------|------------------------|
| Auth + tier | `memory/sibyl_credentials.py`, `memory/factory.py` | Pro via `sibyl init`, free tier local SQLite |
| Read/write | `memory/sibyl_adapter.py` | `MemoryClient.local()` — entities, journal, FTS5 |
| Every turn | `memory/retrieval.py` → brain → `memory/writer.py` | Context before reply; facts after |
| MCP | `mcp/sibyl_bridge.py` | `anima-sibyl`: search, recent, self, people |
| Commands | `/sibyl status`, `/memory search`, `/self` | Inspectable, not black-box |
| Deletion test | `anima --amnesia` | Retrieval off; SQLite file unchanged |

```bash
anima sibyl setup          # link credentials after sibyl init
anima doctor               # store health, tier, built-in MCP
/sibyl status
/mcp call anima-sibyl search {"query": "Robert"}
```

## Install and demo

```bash
git clone https://github.com/RobertKodes/anima.git
cd anima
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
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

## Experiences Marketplace

Unique angle: packs bundle **skills + MCP + personality seeded into Sibyl** — not markdown skins.

```bash
anima experiences list
anima experiences apply scholar
/mcp list    # built-in anima-sibyl + any external servers
```

Scholar: web fetch/explore + in-process Sibyl tools. Messenger: Telegram/Discord channel config.

## Deletion test

```bash
anima --amnesia
```

Retrieval is off. The store on disk is untouched. Proof: `tests/test_deletion_test.py` and [`recordings/amnesia_demo.mp4`](../recordings/amnesia_demo.mp4).

## Base

Adapter talks Base Sepolia (`84532`). Default is dry-run so a clone cannot spend. Keys live in `~/.anima/secrets/wallet.json` (0600). Sibyl stores intent, address, tx id, outcome — never the key. Mainnet is locked until explicitly enabled.

## Tests

```bash
pytest
python scripts/hackathon_smoke.py
```

61 tests — continuity, deletion, brain swap, sleep, router, Base policy, explainability, TUI, experiences, Sibyl integration. All must pass before a public drop.

## Form fill-ins (Sibyl Labs hackathon)

**Copy/paste pack:** [`docs/HACKATHON_FORM_FILL.txt`](HACKATHON_FORM_FILL.txt) · phone pack: [`docs/POST_PACK_FOR_PHONE.txt`](POST_PACK_FOR_PHONE.txt)

**Repo URL:** https://github.com/RobertKodes/anima

**Demo URL:** https://robertkodes.github.io/anima/ · videos in `recordings/hackathon_demo.mp4`

**Memory walkthrough:** Every turn: `retrieval.py` builds context from Sibyl FTS5 + entities → brain → `writer.py` persists facts. Inspect with `/memory search`, `/self`, `/sibyl status`. Experience packs seed `self/being` in Sibyl. Built-in MCP `anima-sibyl` exposes the same store to tools without a subprocess.

**Deletion test:** Run `anima --amnesia`. Teach a name in normal mode; search finds it. In amnesia mode, search returns nothing and replies are newborn — but `~/.anima/sibyl/anima.db` is unchanged. Restart without `--amnesia` and memory returns.

**Sibyl primitives used:** `set_entity` (self, person, goal, policy), `write_event` (journal), `search` (FTS5), `read_events`, `set_state`, `lint`, `learn`, `list_skill_proposals`. Free tier local SQLite; Pro via `sibyl init` + credentials.

## What this is not

Not a chatbot skin. Not a markdown personality. Not a second being per specialist model. Specialists are brains. Sibyl is the self.
