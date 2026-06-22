#!/usr/bin/env bash
# ForgeOS V1 — one-command installer (macOS / Linux).
#
# Usage:  bash install.sh
#
# Installs `uv` if needed, then installs ForgeOS so the `forgeos` command works
# from any terminal. Safe to re-run (idempotent).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "ForgeOS installer"
echo "================="

# 1. Ensure uv is available.
if ! command -v uv >/dev/null 2>&1; then
  echo "-> Installing uv ..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"   # make uv usable in this session
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is installed but not on your PATH." >&2
  echo "       Open a NEW terminal window and run 'bash install.sh' again." >&2
  exit 1
fi
echo "-> uv: $(uv --version)"

# 2. Install ForgeOS (and dependencies) as a global command.
cd "$SCRIPT_DIR"
echo "-> Installing ForgeOS (first run can take a minute) ..."
uv tool install --force .

# Make the global 'forgeos' command available in new terminals (adds uv's tool
# bin directory to your shell PATH). Harmless if already configured.
uv tool update-shell || true

echo
echo "Done. ForgeOS is installed — 'forgeos' is now a global command."
echo
echo "Next steps:"
echo "  1. forgeos init"
echo "  2. export ANTHROPIC_API_KEY=\"sk-ant-...\"      # or: forgeos provider use ollama"
echo "  3. forgeos doctor"
echo "  4. forgeos wizard                               # full getting-started walkthrough"
echo
echo "If 'forgeos' is not found, open a NEW terminal (uv adds it to your PATH)."
