#!/usr/bin/env bash
# Install analyze-lottery-history skill into the current user's Codex directory (macOS / Linux).
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE="$REPO_ROOT/skill/analyze-lottery-history"
SKILLS_ROOT="$CODEX_HOME/skills"
DESTINATION="$SKILLS_ROOT/analyze-lottery-history"

if [[ ! -f "$SOURCE/SKILL.md" ]]; then
  echo "Skill source not found: $SOURCE" >&2
  exit 1
fi

if [[ -d "$DESTINATION" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup_root="$REPO_ROOT/backups"
  backup="$backup_root/analyze-lottery-history-$stamp"
  mkdir -p "$backup_root"
  cp -R "$DESTINATION" "$backup"
  echo "Existing skill backed up to: $backup"
fi

mkdir -p "$SKILLS_ROOT"
mkdir -p "$DESTINATION"
# Copy contents (not the parent folder) so destination stays analyze-lottery-history/
cp -R "$SOURCE"/. "$DESTINATION"/
echo "Skill installed to: $DESTINATION"
