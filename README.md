# Anima

A local-first AI **being** you keep on your machine. The language model is a brain. **Sibyl Memory** is the self. Anima is the organism that holds them together.

Works on **Windows, macOS, and Linux**. No cloud account required to start.

## One-line install

**Windows (PowerShell)**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.ps1 | iex"
```

**macOS / Linux / WSL**

```bash
curl -fsSL https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.sh | bash
```

That installs Python deps into `~/.anima/.venv`, runs onboarding (detect brain + open the graphical CLI), and adds the CLI to your PATH. More options: [`install/README.md`](install/README.md).

## Manual install

```bash
git clone https://github.com/RobertKodes/anima.git
cd anima
python -m venv .venv
```

**macOS / Linux**

```bash
source .venv/bin/activate
pip install -e .
anima onboard --yes
anima
```

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
pip install -e .
anima onboard --yes
anima
```

First launch runs onboarding automatically if you skip `anima onboard`. You meet the being in a graphical terminal UI.

## What you get

- **Persistent identity** — names, goals, policies, and experiences live in a local Sibyl store, not in chat context
- **Many brains, one being** — swap Ollama, llama.cpp, or the built-in Instinct brain without losing memory
- **Graphical CLI** — conversation, status rail, `/why` inspectability, slash commands, command palette
- **Base Sepolia rail** — dry-run by default; memory can refuse spends that break a stored policy
- **Web companion** — optional local UI with `anima --ui`

## Onboarding

Anima detects what is already on your machine, live-tests it with a real reply, then saves config.

| Command | What it does |
|---|---|
| `anima onboard` | Interactive: detect brain → probe → save config |
| `anima onboard --yes` | Non-interactive; picks the best available brain |
| `anima onboard --json` | Machine-readable summary for scripts |
| `anima setup` | Config-only wizard (no live probe) |
| `anima doctor` | Health check: Sibyl, brains, optional tools |

**Detection order:** Ollama → llama.cpp → Instinct (offline fallback, always works).

```bash
# Force a specific brain
anima onboard --yes --brain ollama --model qwen3:1.7b

# CI / air-gapped
anima onboard --yes --brain fake --skip-probe
```

Data lives in `~/.anima/` (or `%USERPROFILE%\.anima` on Windows). Override with `--data` or `ANIMA_HOME`.

## Daily commands

| Command | Purpose |
|---|---|
| `anima` | Graphical CLI (default) |
| `anima --cli` | Classic REPL |
| `anima --ui` | Local web companion |
| `anima /status` | One-shot status |
| `anima /why` | What shaped the last reply |
| `anima /sleep` | Consolidate recent life into Sibyl |
| `anima --amnesia` | Talk without retrieval (store is not deleted) |

**TUI keys:** tab slash hints · ctrl+p palette · F1 help · F3 sleep · ctrl+n new session · ctrl+c leave

## Brains

| Provider | How to use |
|---|---|
| **Ollama** | Install and run Ollama; onboard picks a local model |
| **llama.cpp** | Run `llama-server` on `:8080`; onboard detects it |
| **Instinct** | Built-in offline brain for tests and first run |
| **Cloud / API** | OpenAI, OpenRouter, Groq, Together, or custom OpenAI-compatible |

### Local

```bash
anima --brain ollama --model qwen3:1.7b
anima /brain use qwen3-local
anima /brains
```

### Cloud / API / OAuth

Onboard walks you through auth. Keys and tokens are stored in `~/.anima/secrets/brains/` — never in Sibyl or `config.toml`.

| Auth | Use when |
|---|---|
| **API key** | Paste a key or pass `--api-key` |
| **OAuth** | Paste an access token from the provider dashboard (`--oauth-token`) |
| **Env** | Key already in environment (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, …) |

```bash
# API key (interactive)
anima onboard --cloud openai --auth api_key

# Env var (scripts)
export OPENAI_API_KEY=sk-...
anima onboard --yes --cloud openai --auth env --skip-probe

# OpenRouter
anima onboard --yes --cloud openrouter --auth env --skip-probe

# Custom OpenAI-compatible endpoint
anima onboard --cloud custom --auth api_key --endpoint https://my.api/v1 --model my-model
```

Presets: `openai`, `openrouter`, `groq`, `together`, `custom`.

## Memory

Identity is **not** stored in markdown files or system prompts. It is in Sibyl (SQLite + FTS5).

Teach the being a name, a goal, or a spending cap. Quit. Open a fresh session with an empty model context. It still remembers — that is the point.

`anima --amnesia` turns retrieval off without deleting the store. Same brain, same prompt, different behavior. That is the deletion test.

## Base (optional)

Default network: **Base Sepolia**. Dry-run is on until you fund a wallet and opt in.

```bash
anima /base status
anima /base wallet
anima /base action intent=note value=0 --yes
```

Wallet keys stay in `~/.anima/secrets/wallet.json`, never in Sibyl.

## Development

```bash
pip install -e ".[dev]"
pytest
```

More docs: [`docs/HACKATHON.md`](docs/HACKATHON.md) · [`docs/USE_CASES.md`](docs/USE_CASES.md) · [`docs/PRD_CLI_v0.1.md`](docs/PRD_CLI_v0.1.md)

## Stack

| Piece | Role |
|---|---|
| [sibyl-memory-client](https://pypi.org/project/sibyl-memory-client/) | Durable identity store |
| [Textual](https://textual.textualize.io/) | Graphical CLI |
| Ollama / llama.cpp | Local inference (optional) |
| web3.py / eth-account | Base rail (optional; dry-run works without live signing) |

## Principles

One being, many brains. Memory changes behavior. Models are replaceable; continuity is not. Local-first. Inspectability over magic.

MIT licensed.
