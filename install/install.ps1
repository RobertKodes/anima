# Anima installer — Windows PowerShell
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.ps1 | iex"
# Usage: iwr -useb https://raw.githubusercontent.com/RobertKodes/anima/master/install/install.ps1 | iex

param(
    [switch]$NoOnboard,
    [switch]$NoPath,
    [switch]$DryRun,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$AnimaRepo = if ($env:ANIMA_REPO) { $env:ANIMA_REPO } else { "https://github.com/RobertKodes/anima.git" }
$AnimaBranch = if ($env:ANIMA_BRANCH) { $env:ANIMA_BRANCH } else { "master" }
$AnimaHome = if ($env:ANIMA_HOME) { $env:ANIMA_HOME } else { Join-Path $env:USERPROFILE ".anima" }
$AnimaVenv = if ($env:ANIMA_VENV) { $env:ANIMA_VENV } else { Join-Path $AnimaHome ".venv" }

function Write-AnimaLog([string]$Message) { Write-Host "[anima] $Message" -ForegroundColor Cyan }
function Write-AnimaWarn([string]$Message) { Write-Host "[anima] $Message" -ForegroundColor Yellow }
function Write-AnimaFail([string]$Message) { Write-Host "[anima] $Message" -ForegroundColor Red; exit 1 }

if ($Help) {
    @"
Anima installer

Usage:
  iwr -useb .../install/install.ps1 | iex
  ... | iex -NoOnboard

Options:
  -NoOnboard   Install only; skip anima onboard
  -NoPath      Do not update user PATH
  -DryRun      Show planned steps only
  -Help        Show this help

Environment:
  ANIMA_HOME, ANIMA_REPO, ANIMA_BRANCH, ANIMA_VENV
"@ | Write-Host
    exit 0
}

function Find-Python {
    $candidates = @(
        @("py", @("-3.12")),
        @("py", @("-3.11")),
        @("py", @("-3.10")),
        @("py", @("-3")),
        @("python", @()),
        @("python3", @())
    )
    foreach ($item in $candidates) {
        $cmd = $item[0]
        $args = $item[1]
        if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { continue }
        try {
            $version = & $cmd @args -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            $parts = $version.Trim().Split(".")
            $major = [int]$parts[0]
            $minor = [int]$parts[1]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 10)) {
                return @{ Command = $cmd; Args = $args }
            }
        } catch { continue }
    }
    return $null
}

function Add-AnimaPath([string]$ScriptsDir) {
    if ($NoPath) {
        Write-AnimaWarn "Add to PATH manually: $ScriptsDir"
        return
    }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$ScriptsDir*") {
        if ($DryRun) {
            Write-AnimaLog "[dry-run] would append to user PATH: $ScriptsDir"
        } else {
            [Environment]::SetEnvironmentVariable("Path", "$userPath;$ScriptsDir", "User")
            $env:Path = "$env:Path;$ScriptsDir"
            Write-AnimaLog "Updated user PATH"
        }
    }
}

function Install-AnimaLauncher([string]$ScriptsDir) {
    # pip's anima.exe is often blocked by Windows Application Control; run via python instead.
    $launcher = Join-Path $ScriptsDir "anima.cmd"
    $content = @"
@echo off
"%~dp0python.exe" -c "import sys; from anima.app.cli import main; raise SystemExit(main(sys.argv[1:]))" %*
"@
    Set-Content -Path $launcher -Value $content -Encoding ASCII
    $exe = Join-Path $ScriptsDir "anima.exe"
    if (Test-Path $exe) {
        Remove-Item -Force $exe
        Write-AnimaLog "Replaced blocked anima.exe with anima.cmd launcher"
    } else {
        Write-AnimaLog "Installed anima.cmd launcher"
    }
}

function Get-AnimaPipSource {
    if ($env:ANIMA_PIP_URL) { return $env:ANIMA_PIP_URL }
    $repo = $AnimaRepo.TrimEnd("/").Replace(".git", "")
    if ($repo -match "github\.com/([^/]+/[^/]+)$") {
        return "https://github.com/$($Matches[1])/archive/refs/heads/$AnimaBranch.zip"
    }
    return "git+${AnimaRepo}@${AnimaBranch}"
}

function Install-AnimaPackage {
    $source = Get-AnimaPipSource
    Write-AnimaLog "Installing Anima from $source ..."
    python -m pip install $source
    if ($LASTEXITCODE -ne 0 -and $source -notlike "git+*") {
        Write-AnimaWarn "Zip install failed; retrying via git (requires git)..."
        python -m pip install "git+${AnimaRepo}@${AnimaBranch}"
    }
    if ($LASTEXITCODE -ne 0) {
        Write-AnimaFail "pip install failed. If git errors persist, install git or set ANIMA_PIP_URL to a release zip."
    }
}

function Invoke-AnimaCli([string]$ScriptsDir, [string[]]$CliArgs) {
    $venvPython = Join-Path $ScriptsDir "python.exe"
    & $venvPython -c "import sys; from anima.app.cli import main; raise SystemExit(main(sys.argv[1:]))" @CliArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$python = Find-Python
if (-not $python) {
    Write-AnimaFail "Python 3.10+ is required. Install from https://www.python.org/downloads/"
}

$pythonCmd = $python.Command
$pythonArgs = $python.Args

Write-AnimaLog "Python: $(& $pythonCmd @pythonArgs --version)"
Write-AnimaLog "Install root: $AnimaHome"
Write-AnimaLog "Virtual env: $AnimaVenv"

if ($DryRun) {
    $drySource = Get-AnimaPipSource
    Write-AnimaLog "[dry-run] would create venv and pip install $drySource"
    if (-not $NoOnboard) { Write-AnimaLog "[dry-run] would run: python -m anima onboard --yes --launch" }
    exit 0
}

New-Item -ItemType Directory -Force -Path $AnimaHome | Out-Null

if (-not (Test-Path $AnimaVenv)) {
    Write-AnimaLog "Creating virtual environment..."
    & $pythonCmd @pythonArgs -m venv $AnimaVenv
}

$activate = Join-Path $AnimaVenv "Scripts\Activate.ps1"
. $activate

python -m pip install --upgrade pip wheel | Out-Null
Install-AnimaPackage

$scripts = Join-Path $AnimaVenv "Scripts"
Install-AnimaLauncher $scripts
Add-AnimaPath $scripts

if ($NoOnboard) {
    Write-AnimaLog "Skipping onboard (-NoOnboard)."
} else {
    Write-AnimaLog "Running onboard..."
    Invoke-AnimaCli $scripts @("onboard", "--yes", "--launch")
}

Write-Host @"

Anima is installed.

  anima              graphical CLI
  anima doctor       health check
  anima onboard      change brain / repair setup

Data: $AnimaHome
"@
