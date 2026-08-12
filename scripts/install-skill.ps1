param(
    [string]$CodexHome = (Join-Path $HOME ".codex")
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot "skill\analyze-lottery-history"
$skillsRoot = Join-Path $CodexHome "skills"
$destination = Join-Path $skillsRoot "analyze-lottery-history"

if (-not (Test-Path -LiteralPath (Join-Path $source "SKILL.md"))) {
    throw "Skill source not found: $source"
}

if (Test-Path -LiteralPath $destination) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupRoot = Join-Path $repoRoot "backups"
    $backup = Join-Path $backupRoot "analyze-lottery-history-$stamp"
    New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
    Copy-Item -LiteralPath $destination -Destination $backup -Recurse -Force
    Write-Host "Existing skill backed up to: $backup"
}

New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -Path (Join-Path $source "*") -Destination $destination -Recurse -Force
Write-Host "Skill installed to: $destination"
