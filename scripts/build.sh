#!/usr/bin/env bash
set -euo pipefail

# Build / export Docker images for Coskb stack

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

IMAGES=(
  "pgvector/pgvector:pg15"
  "requarks/wiki:2"
  "nginx:1.25"
)

OUTPUT_DIR="data/backups/images"
mkdir -p "${OUTPUT_DIR}"

echo "Building image bundle for Coskb stack..."

for image in "${IMAGES[@]}"; do
  echo "Pulling image: ${image}"
  docker pull "${image}"

  # Replace characters that are not suitable for filenames
  filename="${image//\//-}"
  filename="${filename//:/-}.tar"

  output_path="${OUTPUT_DIR}/${filename}"
  echo "Saving image ${image} to ${output_path}"
  docker save -o "${output_path}" "${image}"
done

echo "Image bundle saved to ${OUTPUT_DIR}"

