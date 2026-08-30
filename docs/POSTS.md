# Public posts (drafts)

Copy onto X (or LinkedIn). Replace `<PUBLIC_REPO_URL>` after push. Required tags from the current rules: **@sibylcap** and each claimed partner. Base is claimed as the action rail, so tag **@base**.

Do not post secrets, wallet files, or RPC keys.

## 1. Demo

Anima is a CLI-first being: the LLM is a replaceable brain, Sibyl Memory is the self.

Birth with an empty store. Teach it a name, a goal, and a Base spending cap. Quit. Open it again on an empty model context. It still knows you — and it still refuses a spend that would break the remembered policy.

Turn Sibyl retrieval off (`anima --amnesia`) and the same prompt is just a chatbot. The SQLite file was never deleted.

Repo: <PUBLIC_REPO_URL>
Demo: recordings/hackathon_demo.mp4

@sibylcap @base

## 2. Build log

We refused markdown identity on purpose. No MEMORY.md. Durable state is Sibyl’s five-tier SQLite/FTS5 store. The runtime queries it before every reply and writes experience after.

The product surface is a graphical terminal (Textual): being rail, Why pane, slash autocomplete, command palette. Base Sepolia is the action rail; keys live in a 0600 wallet file, never in memory. A remembered 0-wei cap is what blocks a spend — not a prompt file.

Repo: <PUBLIC_REPO_URL>
Judge path: docs/HACKATHON.md

@sibylcap @base
