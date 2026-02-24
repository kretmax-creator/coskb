#!/usr/bin/env bash
set -euo pipefail

# Stop Coskb stack

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "Stopping Coskb stack..."
docker compose down

echo "Coskb stack stopped."

