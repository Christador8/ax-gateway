#!/usr/bin/env bash
# Launch `ax listen` with CrewAI handler (see README).
set -euo pipefail

AGENT_NAME="${1:?Usage: $0 <agent_name>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/.env" ]; then
  set -o allexport
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.env"
  set +o allexport
else
  echo "note: no $SCRIPT_DIR/.env — relying on exported env vars." >&2
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
  elif [ -x "$SCRIPT_DIR/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/Scripts/python.exe"
  else
    PYTHON_BIN="$(command -v python3 || command -v python)"
  fi
fi

BRIDGE="$SCRIPT_DIR/agent.py"
if [ ! -f "$BRIDGE" ]; then
  echo "ERROR: agent.py missing at $BRIDGE" >&2
  exit 1
fi

echo "Starting crewai_agent example"
echo "  Agent:  $AGENT_NAME"
echo "  Python: $PYTHON_BIN"
echo "  Model:  ${CREWAI_MODEL:-gpt-4o-mini}"
echo

exec ax listen --agent "$AGENT_NAME" --exec "$PYTHON_BIN $BRIDGE"
