#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_NAME="$(basename "${PROJECT_DIR}")"
DATE_STAMP="$(date +%Y%m%d)"
OUTPUT_DIR="${1:-${PROJECT_DIR}/exports}"

SOURCE_ARCHIVE="${OUTPUT_DIR}/${PROJECT_NAME}-source-${DATE_STAMP}.tar.gz"
HISTORY_BUNDLE="${OUTPUT_DIR}/${PROJECT_NAME}-history-${DATE_STAMP}.bundle"

mkdir -p "${OUTPUT_DIR}"

echo "[1/2] Creating source archive: ${SOURCE_ARCHIVE}"
tar \
  --exclude="${PROJECT_NAME}/venv" \
  --exclude="${PROJECT_NAME}/.git" \
  --exclude="${PROJECT_NAME}/exports" \
  -czf "${SOURCE_ARCHIVE}" \
  -C "$(dirname "${PROJECT_DIR}")" \
  "${PROJECT_NAME}"

echo "[2/2] Creating git bundle: ${HISTORY_BUNDLE}"
git -C "${PROJECT_DIR}" bundle create "${HISTORY_BUNDLE}" --all

echo "Done. Exported files:"
ls -lh "${SOURCE_ARCHIVE}" "${HISTORY_BUNDLE}"