# Install one-liners

Scripts live in this folder and are served from GitHub:

`https://raw.githubusercontent.com/RobertKodes/anima/master/install/`

## Windows (PowerShell)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.ps1 | iex"
```

Alternative:

```powershell
iwr -useb https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.ps1 | iex
```

Install without onboard:

```powershell
& ([scriptblock]::Create((iwr -useb https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.ps1))) -NoOnboard
```

## macOS / Linux / WSL

```bash
curl -fsSL https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.sh | bash
```

Install without onboard:

```bash
curl -fsSL https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.sh | bash -s -- --no-onboard
```

## Flags

| Flag | Shell | Effect |
|------|-------|--------|
| `--no-onboard` | bash | Skip `anima onboard --yes` |
| `-NoOnboard` | PowerShell | Same |
| `--no-path` / `-NoPath` | both | Do not update PATH |
| `--dry-run` / `-DryRun` | both | Print plan only |

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `ANIMA_HOME` | `~/.anima` | Data directory + venv parent |
| `ANIMA_VENV` | `$ANIMA_HOME/.venv` | Virtual environment path |
| `ANIMA_REPO` | GitHub repo URL | Fork or mirror |
| `ANIMA_BRANCH` | `master` | Branch to install |

## Requirements

- Python 3.10+
- `git` (for pip install from GitHub)
- Network access to PyPI and GitHub
