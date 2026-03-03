#!/usr/bin/env bash
set -euo pipefail

# Weekly backup wrapper: run backup_db.sh and rotate old dumps (keep last N).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if [ ! -f ".env" ]; then
  echo ".env file not found in project root. Cannot run backup."
  exit 1
fi

set -a
. "./.env"
set +a

KEEP="${BACKUP_KEEP_COUNT:-4}"
BACKUP_DIR="data/backups"

bash "${SCRIPT_DIR}/backup_db.sh"

# Rotate: keep only the last KEEP coskb_*.sql files (by mtime, oldest removed first)
if [ ! -d "${BACKUP_DIR}" ]; then
  exit 0
fi

shopt -s nullglob
files=("${BACKUP_DIR}"/coskb_*.sql)
shopt -u nullglob

if [ "${#files[@]}" -le "${KEEP}" ]; then
  exit 0
fi

count_to_remove=$((${#files[@]} - KEEP))
# List by mtime (oldest first), take first count_to_remove, delete them
for f in "${files[@]}"; do
  stat -c "%Y %n" "$f"
done | sort -n | head -n "${count_to_remove}" | while IFS= read -r line; do
  path="${line#* }"
  rm -f "$path" && echo "Removed old backup: $path"
done
