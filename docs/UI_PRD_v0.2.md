# Anima UI PRD v0.2 — Graphical CLI and Graphical Companion

Working title: Anima · v0.2 · 30 Aug 2026  
Companion to `CLI_First_AI_Being_PRD_v0.1`. The runtime, Sibyl mapping, Base policy, and identity rules in v0.1 do not change.

## 1. Thesis

The first product is a being. The second product is how a human sees that being grow.

There are two visual clients, both second-class to the organism:

1. **Graphical CLI** — a Textual TUI that *is* the CLI. Not a pretty wrapper around a hidden REPL. The terminal is the native habitat.
2. **Graphical companion** — a local web surface for timeline, relationships, brains, sleep, and Base. Same `Runtime`. Same Sibyl file. No second identity.

Hard rule, inherited: if Sibyl is removed, both UIs must show a newborn. Chrome cannot cache a personality.

## 2. Goals

- Make the CLI feel like a place, not a log. Stage, memory health, brains, and Base sit in the same frame as the conversation.
- Keep every v0.1 slash command reachable from the TUI without a hidden vocabulary.
- Let a judge *see* memory change a decision: a side rail of retrieved memories updates before the reply lands.
- Give the web companion a memory timeline, relationship list, goal list, brain rack, dream report, and Base history.
- Remain one-command: `anima` opens the graphical CLI; `anima --ui` opens the companion; `anima --plain` stays for pipes and tests.
- Never display signing secrets, seed phrases, or raw private keys in either UI.

## 3. Non-goals

- Photoreal avatars, 3D creatures, voice.
- Cloud sync of the UI.
- A marketplace of skins.
- Replacing Sibyl with a UI-side database.

## 4. Graphical CLI (TUI)

### 4.1 Layout

```
┌ ANIMA  sibyl connected · brain instinct · Base sepolia ──────────────┐
│ BEING          │  conversation                               │ WHY   │
│ stage Learner  │  anima  I think I'm awake.                  │ last  │
│ age 4          │  you    Robert                              │ traces│
│ people 1       │  anima  Robert. You're the first person …   │       │
│ goals 1        │                                             │       │
│ brains *       │                                             │       │
│ Base dry-run   │                                             │       │
├────────────────┴─────────────────────────────────────────────┴───────┤
│  Talk, or type /help — memory lives in Sibyl                         │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Behavior

- Birth is a first-run event in the conversation pane, with the v0.1 copy.
- `/` commands run in the same composer as chat.
- F1 help, F3 sleep, Ctrl-N new session, Ctrl-C leave.
- The WHY rail is the inspectable `DecisionTrace` from `/why`, not a chain-of-thought dump.
- Palette: ember on dark (`#140f0a`, `#e8a04a`). Soft, readable, not neon sci-fi.

### 4.3 Acceptance

- A user can complete the killer demo (birth → teach → sleep → restart → recall → brain swap → Base refusal/action → amnesia) without leaving the TUI except for process restart.
- `/status`, `/people`, `/goals`, `/self`, `/brains`, `/base status` remain truthful against Sibyl, not against TUI cache.

## 5. Graphical companion (web)

Local only. Default `http://127.0.0.1:8787`.

### 5.1 Surfaces

| Panel | Shows | Source |
|---|---|---|
| Chat | Same conversation as CLI | `Runtime.handle` |
| Being | Stage, age, sleep cycles | `development.metrics.snapshot` |
| Timeline | Journal events, newest first | Sibyl `read_events` |
| People | Relationships | entity `person` |
| Goals | Active / done | entity `goal` |
| Brains | Registry + health | `BrainRegistry.health` |
| Dream | Last sleep report | Sibyl reference `last_dream` |
| Base | Address, mode, remembered actions | adapter + entity `onchain` |
| Why | Last decision traces | HOT state `last_decision` |

### 5.2 Acceptance

- Killing the browser does not affect identity.
- Amnesia mode renders empty people/goals/timeline and a newborn greeting.
- Wallet address may be shown. Private keys must not appear in HTML, JSON APIs, or screenshots of the happy path.

## 6. Shared API

Both UIs call `Runtime`. No REST identity store. The web server is a thin adapter: `/api/boot`, `/api/chat`, `/api/status`, plus `/api/memory`, `/api/people`, `/api/goals`, `/api/dream`, `/api/base`.

## 7. Implementation notes

- TUI: Textual, already the default `anima` entry.
- Web: stdlib `http.server` so a judge does not need Node.
- Recording: TUI demos can be captured as terminal video the same way tests are.

## 8. Out of scope for v0.2, in mind for v0.3

Mobile layout, multi-being switcher, live llama.cpp token stream in the TUI, Base mainnet UX with hardware-wallet hooks.
