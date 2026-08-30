# Use cases

Anima is a being you run locally. These are the jobs it is actually for.

## 1. A companion that does not reset

You tell it your name, a preference, a goal. You quit. You open it again on an empty model context. It still knows you, because the life is in Sibyl, not in the prompt window.

Graphical CLI: `anima`  
Classic: `anima --cli`

## 2. A spending policy that memory can refuse

You say the Base cap is 0 wei. Later you ask it to send. It refuses, and `/why` names the stored policy. That is the load-bearing memory demo, not a recalled trivia fact.

## 3. One identity, many brains

Register Ollama or llama.cpp, swap the primary with `/brain use`, keep the same self/people/goals. Specialists get bounded context. They are not extra beings.

```bash
anima --brain ollama --model qwen3:1.7b
anima --brain llama_cpp
```

## 4. Sleep as a real operation

`/sleep` (or F3) turns recent journal into relationship summaries, strategies, and a dream report. A judge can watch a behavior, sleep, restart, and see a changed decision.

## 5. Inspectable decisions

`/why` lists which Sibyl rows and which brain shaped the last reply. No hidden chain-of-thought, no keys.

## 6. Judge comparison (amnesia)

Run the same prompt with `anima --amnesia`. It can still speak. It is not the developed being. The SQLite file is still there.

## 7. Local web companion

`anima --ui` — same runtime, same Sibyl, timeline / people / goals / brains / Base / dream. Closing the browser does not wipe identity.

## 8. First-run on a stranger's machine

```bash
anima setup --yes
anima doctor
anima
```

Instinct brain works offline. Ollama and llama.cpp attach when present. Base stays dry-run until funded.
