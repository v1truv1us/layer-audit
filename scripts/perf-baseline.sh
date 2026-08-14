#!/bin/bash
# perf-baseline.sh — baseline any registered workflow and print a ready-made
# performance-goal loop for it. Baselines come from telemetry (no re-runs);
# timed runs are only offered when telemetry has <3 samples.
#
# Usage: perf-baseline.sh <workflow> [--runs]

set -uo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WF="${1:-}"
[ -z "$WF" ] && { echo "usage: perf-baseline.sh <workflow> [--runs]"; exit 1; }

read -r MEDIAN RUNS MAX_S OUTPUT_CHECK < <(python3 - "$REPO_DIR" "$WF" <<'EOF'
import json, sys
repo, wf = sys.argv[1], sys.argv[2]
reg = json.load(open(f"{repo}/registry.json"))
spec = reg["workflows"].get(wf, {})
durs, runs = [], 0
try:
    for line in open(f"{repo}/telemetry/runs.jsonl"):
        r = json.loads(line)
        if r.get("workflow") == wf and r.get("duration_s") is not None and r.get("outcome") == "success":
            durs.append(r["duration_s"]); runs += 1
except FileNotFoundError:
    pass
durs.sort()
median = durs[len(durs)//2] if durs else "-"
check = "output exists and non-empty" if spec.get("output_glob") else "exit code 0"
print(median, runs, spec.get("max_duration_s", "-"), check)
EOF
)

echo "workflow:  $WF"
echo "telemetry: $RUNS successful timed runs"
echo "baseline:  median ${MEDIAN}s$([ "$MAX_S" != "-" ] && echo " (target: ${MAX_S}s)")"

if [ "$RUNS" -lt 3 ] && [ "${2:-}" = "--runs" ]; then
  SCRIPT="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}/scripts/run-${WF}.sh"
  [ ! -f "$SCRIPT" ] && { echo "no run script at $SCRIPT — cannot time"; exit 1; }
  case "$WF" in robinhood*|*trade*) echo "blocked: $WF has side effects; baseline it manually"; exit 1;; esac
  echo "timing 3 runs..."
  for i in 1 2 3; do S=$(date +%s); "$SCRIPT" >/dev/null 2>&1; echo "  run $i: $(( $(date +%s) - S ))s"; done
  exit 0
elif [ "$RUNS" -lt 3 ]; then
  echo "insufficient telemetry — re-run with --runs to time 3 live executions"
fi

if [ "$MEDIAN" != "-" ]; then
  TARGET=$(( MEDIAN * 70 / 100 ))
  cat <<EOF

--- performance-goal loop (paste into Claude Code) ---
/goal median of 3 timed runs of run-${WF}.sh under ${TARGET}s (30% cut from ${MEDIAN}s baseline) AND ${OUTPUT_CHECK}, stop after 6 tries
--- rules ---
harness times the runs, never the agent. keep/revert per iteration: beat the
benchmark or git restore. correctness gate (${OUTPUT_CHECK}) must stay green.
EOF
fi
