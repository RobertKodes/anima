# Publish the public GitHub repo

Hackathon rules require a **public** GitHub repository (MIT or Apache-2.0) with real commit history. A Cursor-hosted private copy does not count.

This machine’s `gh` token in the keyring is **invalid**. Re-auth, then create and push. Do not force-push.

## 1. Re-authenticate

```bash
gh auth refresh -h github.com
gh auth status
```

If refresh fails: `gh auth login -h github.com -p https -w`

## 2. Push (from the repo root)

```bash
git branch -m main
git remote remove origin 2>/dev/null || true
gh repo create anima --public --source=. --remote=origin --push \
  --description "Local-first AI being. The LLM is a brain. Sibyl Memory is the self. Base is the action rail."
```

If `anima` is taken on your account, use `anima-being` instead of `anima`.

## 3. Confirm a stranger can clone

```bash
gh repo view --web
git ls-remote origin HEAD
```

Paste the HTTPS URL into [`README.md`](../README.md) clone instructions, [`docs/SUBMISSION.md`](SUBMISSION.md), and [`docs/POSTS.md`](POSTS.md), then commit:

```bash
git add README.md docs/SUBMISSION.md docs/POSTS.md
git commit -m "$(cat <<'EOF'
Add the public clone URL for judges.

EOF
)"
git push
```

## What not to do

- Do not upload `wallet.json`, `.env`, or `*.db`.
- Do not use a private repo and “make it public later” after judges start.
- Do not substitute a Cursor-hosted remote for GitHub. The form wants github.com.
