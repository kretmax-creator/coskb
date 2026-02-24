#!/usr/bin/env bash
set -euo pipefail

# Load Docker images for Coskb stack from saved tar files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

INPUT_DIR="data/backups/images"

if [ ! -d "${INPUT_DIR}" ]; then
  echo "Directory ${INPUT_DIR} does not exist. Nothing to load."
  exit 1
fi

shopt -s nullglob
tar_files=("${INPUT_DIR}"/*.tar)
shopt -u nullglob

if [ ${#tar_files[@]} -eq 0 ]; then
  echo "No .tar files found in ${INPUT_DIR}. Nothing to load."
  exit 1
fi

echo "Loading Docker images from ${INPUT_DIR}..."

for tar_file in "${tar_files[@]}"; do
  echo "Loading ${tar_file}..."
  docker load -i "${tar_file}"
done

echo "All images loaded."

