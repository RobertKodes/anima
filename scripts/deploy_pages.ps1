# Deploy site/ to gh-pages (GitHub Pages serves this branch)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
git subtree split --prefix=site -b deploy-gh-pages
git push origin deploy-gh-pages:gh-pages --force
git branch -D deploy-gh-pages 2>$null
Write-Host "Deployed. Live in ~1 min: https://robertkodes.github.io/anima/"
