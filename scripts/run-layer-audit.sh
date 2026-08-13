#!/bin/bash
set -euo pipefail

# Layer Audit — Weekly, Monday 07:00 (before morning-brief).

export PI_CODING_AGENT_DIR="${HOME}/.pi/agent"
export PATH="/opt/homebrew/bin:$PATH"

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

"${PI_CODING_AGENT_DIR}/scripts/run-locked.sh" "layer-audit" \
  python3 "${REPO_DIR}/audit.py"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Layer audit complete"
