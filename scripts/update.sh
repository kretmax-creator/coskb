#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

BRANCH="${1:-}"
PREVIEW_FLAG="${2:-}"
PREVIEW_PORT=8891

usage() {
  echo "Usage:"
  echo "  bash scripts/update.sh                        # Update master and deploy"
  echo "  bash scripts/update.sh feature/x --preview    # Deploy feature branch on port ${PREVIEW_PORT}"
  echo "  bash scripts/update.sh --preview-stop         # Stop preview deployment"
}

stop_preview() {
  echo "Stopping preview deployment..."
  COMPOSE_PROJECT_NAME=coskb-preview docker compose down 2>/dev/null || true
  echo "Preview stopped."
}

deploy_preview() {
  local branch="$1"

  echo "Fetching latest changes..."
  git fetch origin

  if ! git rev-parse --verify "origin/${branch}" >/dev/null 2>&1; then
    echo "Error: branch '${branch}' not found on remote."
    exit 1
  fi

  echo "Checking out branch: ${branch}"
  git checkout "${branch}"
  git pull origin "${branch}"

  echo "Starting preview on port ${PREVIEW_PORT}..."
  COMPOSE_PROJECT_NAME=coskb-preview \
    NGINX_PORT="${PREVIEW_PORT}" \
    docker compose up -d --build

  echo
  echo "Preview running on port ${PREVIEW_PORT}"
  echo "Production remains on port 8890"
  COMPOSE_PROJECT_NAME=coskb-preview docker compose ps
}

deploy_master() {
  local current_branch
  current_branch="$(git branch --show-current)"

  if [ "${current_branch}" != "master" ]; then
    echo "Switching to master..."
    git checkout master
  fi

  echo "Pulling latest changes..."
  git pull origin master

  echo "Building and restarting services..."
  docker compose build
  docker compose up -d

  echo
  echo "Deployment complete."
  docker compose ps
}

if [ "${BRANCH}" = "--preview-stop" ]; then
  stop_preview
elif [ "${PREVIEW_FLAG}" = "--preview" ] && [ -n "${BRANCH}" ]; then
  deploy_preview "${BRANCH}"
elif [ -z "${BRANCH}" ]; then
  deploy_master
else
  echo "Error: unknown arguments."
  usage
  exit 1
fi
