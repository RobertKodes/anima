#!/usr/bin/env bash
# Deploy site/ to gh-pages (GitHub Pages serves this branch for robertkodes.github.io/anima)
set -euo pipefail
cd "$(dirname "$0")/.."
git subtree split --prefix=site -b deploy-gh-pages
git push origin deploy-gh-pages:gh-pages --force
git branch -D deploy-gh-pages 2>/dev/null || true
echo "Deployed. Live in ~1 min: https://robertkodes.github.io/anima/"
