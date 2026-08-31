# Anima Experiences Marketplace

**Experiences** are open-source bundles — unlike Hermes skins or OpenClaw skill folders alone, each Anima experience combines:

| Layer | What it configures |
|-------|-------------------|
| **Skills** | Granted capabilities (`web_fetch`, `explore`, …) |
| **MCP** | Model Context Protocol servers (tools + resources) |
| **Personality** | Sibyl self-model + strategy hints (not markdown files) |
| **Channels** | Telegram / Discord readiness |
| **Unique angle** | One line describing what makes this combo distinct |

Memory stays in **Sibyl**. Experiences shape *how* the being acts — they do not replace identity.

## Bundled experiences

| ID | Title | Best for |
|----|-------|----------|
| `scholar` | Scholar | Research, web fetch + explore + memory MCP |
| `guardian` | Guardian | Policy-first, Base spending discipline |
| `messenger` | Messenger | Telegram/Discord companion |

## Commands

```bash
anima experiences list
anima experiences apply scholar
anima channel telegram    # needs TELEGRAM_BOT_TOKEN
anima channel discord     # needs DISCORD_BOT_TOKEN + pip install 'anima[discord]'
```

In chat:

```
/experiences list
/experiences apply scholar
/mcp list
/mcp tools sibyl
```

## Author your own

Create `experiences/my-pack/experience.toml`:

```toml
id = "my-pack"
title = "My Pack"
version = "1.0.0"
author = "you"
summary = "One line pitch"
tags = ["custom", "demo"]
unique = "What makes this combo unlike a generic agent"

[[skills]]
capability = "web_fetch"

[[mcp]]
id = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
optional = true

[personality]
tone = "warm, concise"
self_description = "I was shaped by the my-pack experience."
values = ["honesty", "ground claims in Sibyl"]

[capabilities]
web_fetch = true
explore = true
```

Install locally:

```bash
cp -r experiences/my-pack ~/.anima/experiences/installed/
anima experiences apply my-pack
```

## Optional dependencies

```bash
pip install 'anima[mcp]'      # MCP tool discovery + calls
pip install 'anima[discord]'   # Discord channel bot
```

Telegram uses httpx only (already included).

## Open source

All bundled experiences are MIT. Publish yours by PR to `experiences/` or host a git repo and copy into `~/.anima/experiences/installed/`.
