#!/usr/bin/env bash
# Copy standalone.js from the sibling streamlit-drawable-konva build into this package.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${STANDALONE_SRC:-$ROOT/../streamlit-drawable-konva/streamlit_drawable_konva/frontend/build/standalone.js}"
DEST="$ROOT/violit_drawable_konva/static/standalone.js"

if [[ ! -f "$SRC" ]]; then
  echo "Missing $SRC" >&2
  echo "Build the Streamlit package frontend first (npm run build in frontend/)." >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
cp -f "$SRC" "$DEST"
echo "Synced $(wc -c < "$DEST") bytes -> $DEST"
