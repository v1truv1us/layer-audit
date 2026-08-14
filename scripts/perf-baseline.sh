#!/bin/bash
# perf-baseline.sh — baseline any registered workflow and print a ready-made
# performance-goal loop for it. Baselines come from telemetry (no re-runs);
# timed runs are only offered when telemetry has <3 samples.
#
# Usage: perf-baseline.sh <workflow> [--runs]

set -uo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WF="${1:-}"
[ -z "$WF" ] && { echo "usage: perf-baseline.sh <workflow|--project name> [--runs]"; exit 1; }

# --- project mode: any repo with a bench command ---------------------------
if [ "$WF" = "--project" ]; then
  PROJ="${2:-}"
  [ -z "$PROJ" ] && { echo "usage: perf-baseline.sh --project <name>"; exit 1; }
  PROJ_LINE=$(python3 - "$REPO_DIR" "$PROJ" <<'EOF'
import json, sys
reg = json.load(open(f"{sys.argv[1]}/registry.json"))
p = reg.get("projects", {}).get(sys.argv[2], {})
print("|".join([p.get("path") or "-", p.get("bench") or "-", p.get("correctness") or "-", str(p.get("max_duration_s") or "-")]))
EOF
)
  IFS='|' read -r PPATH PBENCH PCORRECT PMAX <<< "$PROJ_LINE"
  if [ "$PPATH" = "-" ] || [ "$PBENCH" = "-" ]; then
    echo "project '$PROJ' has no path/bench in registry.json — fill them in first"
    exit 1
  fi
  PPATH="${PPATH/#\~/$HOME}"
  [ ! -d "$PPATH" ] && { echo "path not found: $PPATH"; exit 1; }

  echo "project:     $PROJ ($PPATH)"
  echo "bench:       $PBENCH"
  echo "correctness: $PCORRECT"

  echo "correctness gate: $PCORRECT"
  (cd "$PPATH" && eval "$PCORRECT" >/dev/null 2>&1) || { echo "GATE RED — fix correctness before perf work"; exit 1; }
  echo "gate green. timing 3 bench runs..."
  BEST_MED=""
  TIMES=""
  for i in 1 2 3; do
    S=$(date +%s)
    M0=$(python3 -c 'import time; print(time.monotonic())')
    (cd "$PPATH" && eval "$PBENCH" >/dev/null 2>&1)
    D=$(python3 -c "import time; print(round(time.monotonic() - $M0, 2))")
    TIMES="$TIMES $D"
    "$REPO_DIR/scripts/emit-telemetry.sh" --workflow "$PROJ" --harness bash --trigger manual --outcome success --stop-reason done --ts-start "$S" --duration "$D"
    echo "  run $i: ${D}s"
  done
  MED=$(echo $TIMES | tr ' ' '\n' | sort -n | sed -n 2p)
  TARGET=$(python3 -c "print(round($MED * 0.7, 2))")
  cat <<EOF
baseline:    median ${MED}s$([ "$PMAX" != "-" ] && echo " (registry target: ${PMAX}s)")

--- performance-goal loop (paste into Claude Code / opencode run) ---
/goal median of 3 runs of '$PBENCH' in $PPATH under ${TARGET}s (30% cut from ${MED}s baseline) AND '$PCORRECT' green, stop after 6 tries
--- rules ---
harness times, never the agent. one hypothesis per iteration. beat the median
or git restore. correctness gate ($PCORRECT) must stay green every iteration.
EOF
  exit 0
fi

# --- workflow mode ----------------------------------------------------------

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
