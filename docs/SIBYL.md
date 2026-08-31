# Sibyl Memory in Anima

Anima treats **Sibyl Memory as identity**. The LLM is a replaceable brain; if you delete the Sibyl store, the being is gone. There is no `MEMORY.md`, `USER.md`, or prompt-stuffed personality file.

## Architecture

```
User message
    │
    ▼
Runtime.handle()
    │
    ├─► retrieval.py      ──► SibylAdapter.search / get_entity / read_events
    │                         (context package before every reply)
    │
    ├─► brain.complete()  ──► Ollama / cloud / instinct
    │
    └─► writer.py         ──► SibylAdapter.set_entity / write_event
                              (every durable fact)
```

### Memory domains (entity categories)

| Category | Purpose |
|----------|---------|
| `self/being` | Name, description, values, sleep cycles |
| `person/*` | Relationships |
| `goal/*` | Active goals |
| `strategy/*` | What worked |
| `knowledge/*` | Consolidated facts |
| `experience/*` | Applied experience packs |

Journal episodes go through `write_event()` — searchable via FTS5 across tiers.

## Setup

**Free tier (default)** — works out of the box. Local SQLite at `~/.anima/sibyl/anima.db`, 256 KB cap.

**Pro tier** — server-verified caps and sync:

```bash
pip install sibyl-memory-cli[mcp]
sibyl init
anima sibyl setup
```

Credentials are loaded from (first match wins, merged with env):

1. `~/.anima/secrets/sibyl.json`
2. `~/.sibyl-memory/credentials.json`
3. `SIBYL_ACCOUNT_ID`, `SIBYL_SESSION_TOKEN`, `SIBYL_TIER`

Set tier in config: `sibyl_tier = "pro"` in `config.toml`.

## Commands

| Command | What it does |
|---------|----------------|
| `/memory recent` | Recent journal events |
| `/memory search <q>` | FTS5 search |
| `/sibyl status` | Tier, cap, auth, db path |
| `/sibyl lint` | Sibyl Memory lint report |
| `/sibyl learn` | Consolidate journal → entities |
| `/sibyl skills` | Pending skill proposals |
| `/self`, `/people`, `/goals` | Inspect entity tiers |
| `/sleep` | Anima consolidation pass |
| `--amnesia` | Run without retrieval (store untouched) |

CLI equivalents: `anima sibyl setup`, `anima sibyl status`, `anima doctor`.

## Built-in MCP bridge

Experience packs (e.g. Scholar) no longer spawn `sibyl mcp` as a subprocess. Anima exposes **in-process** tools on server id `anima-sibyl`:

- `search` — FTS5 query
- `recent` — journal tail
- `self` — self entity
- `people` — relationship list

```
/mcp list
/mcp tools anima-sibyl
/mcp call anima-sibyl search {"query": "Robert"}
```

Same `MemoryClient` instance as chat — no split brain.

## Deletion test (hackathon)

1. Talk to Anima — name, preferences stored in Sibyl.
2. `/memory search <name>` — hits appear.
3. Exit. Run `anima --amnesia` — no hits, newborn replies.
4. Restart normally — memory returns. **Nothing was deleted**; amnesia is a process flag.

## Code map

| File | Role |
|------|------|
| `memory/sibyl_adapter.py` | Thin `MemoryClient.local()` wrapper |
| `memory/factory.py` | `open_memory()` with credentials |
| `memory/sibyl_credentials.py` | Auth resolution + status formatting |
| `memory/retrieval.py` | Pre-reply context assembly |
| `memory/writer.py` | Post-reply durable writes |
| `mcp/sibyl_bridge.py` | In-process MCP tools |
| `app/sibyl_setup.py` | `anima sibyl setup` |

## Swap the brain, keep the being

`/brain use <id>` changes the primary model. Identity stays in Sibyl. That is the core thesis: **memory is the being; models are organs.**
