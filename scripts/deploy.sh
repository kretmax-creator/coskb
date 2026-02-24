#!/usr/bin/env bash
set -euo pipefail

# Deploy Coskb stack with Docker Compose

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "Starting Coskb stack with Docker Compose..."
docker compose up -d

echo
echo "Current service status:"
docker compose ps

