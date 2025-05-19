#!/usr/bin/env bash
set -e

echo "▶ Installing Python deps with uv"
pip install -q 'uv>=0.1.29'
REPO_ROOT="/workspaces/snippy"
SRC_DIR="$REPO_ROOT/src"
cd $SRC_DIR
uv venv .venv
uv pip install -r requirements.txt
