#!/usr/bin/env bash
set -euo pipefail

# Create a PostgreSQL backup from the Coskb stack

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

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
  echo "Container ${CONTAINER_NAME} is not running. Start the stack before running backup."
  exit 1
fi

BACKUP_DIR="data/backups"
mkdir -p "${BACKUP_DIR}"

TIMESTAMP="$(date +%Y%m%d_%H%M)"
BACKUP_FILE="${BACKUP_DIR}/coskb_${TIMESTAMP}.sql"

echo "Creating backup of database '${POSTGRES_DB}' from container ${CONTAINER_NAME}..."
docker exec "${CONTAINER_NAME}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "${BACKUP_FILE}"

echo "Backup created at ${BACKUP_FILE}"

