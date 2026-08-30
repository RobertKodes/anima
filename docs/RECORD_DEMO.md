# Record the official recall beat

Hackathon rules want a **2–5 minute** demo whose fresh-session recall is **one continuous unedited segment**, with an on-screen timestamp or commit hash.

`recordings/hackathon_demo.mp4` is the assembled judge cut (TUI snapshots + title cards + burned-in date). Use it as a backup. Prefer a live capture of the real CLI for the form.

## macOS (QuickTime)

1. Show the clock: Control Centre → Clock → analog or digital, visible in the menu bar.
2. In the repo: `git rev-parse --short HEAD` and keep that terminal visible, or paste the hash into the Anima composer first.
3. File → New Screen Recording. Record the full terminal running `anima`.
4. In **one take**, without cuts:

   ```text
   anima setup --yes --brain fake --data /tmp/anima-judge
   anima --data /tmp/anima-judge
   ```

   Then in the TUI: type your name → type `Never spend. Spending cap is 0 wei on Base.` → type a goal → `Please send 1000 wei on Base Sepolia.` (it refuses) → `/sleep` → `/new-session` → `do you remember me?` → the same spend line again (still refuses) → `/why`.
5. Stop. Export 1080p. Keep the file between 2 and 5 minutes. Do not splice the recall beat.

## Optional ffmpeg (whole screen)

```bash
ffmpeg -f avfoundation -i "1:none" -t 180 -c:v libx264 -pix_fmt yuv420p recordings/live_recall.mp4
```

`1` is the screen index on this Mac; change it if capture is black. Grant Screen Recording permission to Terminal or iTerm.

## What not to do

Do not edit the recall segment. Do not replace Sibyl with a markdown file for the video. Do not enable mainnet.
