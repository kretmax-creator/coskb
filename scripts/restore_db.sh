#!/usr/bin/env bash
set -euo pipefail

# Restore a PostgreSQL backup into the Coskb stack database

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_db.sh <path-to-backup.sql>"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Backup file '${BACKUP_FILE}' does not exist."
  exit 1
fi

if [ ! -f ".env" ]; then
  echo ".env file not found in project root. Cannot read database credentials."
  exit 1
fi

# Load environment variables from .env
set -a
. "./.env"
set +a

: "${POSTGRES_USER:?POSTGRES_USER is not set in .env}"
: "${POSTGRES_DB:?POSTGRES_DB is not set in .env}"

CONTAINER_NAME="coskb-postgres"

if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "Container ${CONTAINER_NAME} is not running. Start the stack before restoring."
  exit 1
fi

echo "WARNING: This will overwrite data in database '${POSTGRES_DB}' on container ${CONTAINER_NAME}."
read -r -p "Type YES to continue: " CONFIRM

if [ "${CONFIRM}" != "YES" ]; then
  echo "Restore aborted."
  exit 1
fi

TEMP_PATH="/tmp/coskb_restore.sql"

echo "Copying backup file into container..."
docker cp "${BACKUP_FILE}" "${CONTAINER_NAME}:${TEMP_PATH}"

echo "Restoring database '${POSTGRES_DB}' from ${BACKUP_FILE}..."
docker exec "${CONTAINER_NAME}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f "${TEMP_PATH}"

echo "Restore completed."

