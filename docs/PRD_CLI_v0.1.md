# PRD v0.1 — CLI-First Persistent AI Being

The original brief lives at `CLI_First_AI_Being_PRD_v0.1.docx`. Anima implements it.

Follow-on visual product: [`UI_PRD_v0.2.md`](UI_PRD_v0.2.md).

## Identity rule

No `MEMORY.md`, `PERSONALITY.md`, `USER.md`, or `AGENTS.md` may be the source of persistent identity. Durable personal state is written to and retrieved from Sibyl Memory (`sibyl-memory-client`, SQLite + FTS5).

## Critical path

1. Parse intent.
2. Query Sibyl for self, relationships, goals, strategies, episodes.
3. Build a small context package.
4. Route to primary or specialist brain.
5. Reply or propose an action.
6. Persist the experience through Sibyl.

Sleep (`/sleep`) consolidates that history. A fresh process with empty LLM context must still be the same being.
