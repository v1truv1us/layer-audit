#!/bin/bash
# emit-telemetry.sh — append one schema-2 JSONL record to the run ledger.
# Never fails the caller: all errors are swallowed (telemetry must not break workflows).
#
# Usage:
#   emit-telemetry.sh --workflow NAME [--harness H] [--trigger T] [--outcome O] \
#     [--stop-reason R] [--ts-start EPOCH] [--duration N] [--iterations N] \
#     [--verified 0|1] [--error-sig SIG] [--output-ref PATH]
{
set -uo pipefail

WORKFLOW="" HARNESS="" TRIGGER="" OUTCOME="unknown" STOP_REASON="" TS_START="" DURATION="" ITERATIONS="" VERIFIED="false" ERROR_SIG="" OUTPUT_REF=""
while [ $# -gt 0 ]; do
  case "$1" in
    --workflow) WORKFLOW="$2"; shift 2;;
    --harness) HARNESS="$2"; shift 2;;
    --trigger) TRIGGER="$2"; shift 2;;
    --outcome) OUTCOME="$2"; shift 2;;
    --stop-reason) STOP_REASON="$2"; shift 2;;
    --ts-start) TS_START="$2"; shift 2;;
    --duration) DURATION="$2"; shift 2;;
    --iterations) ITERATIONS="$2"; shift 2;;
    --verified) VERIFIED="$2"; shift 2;;
    --error-sig) ERROR_SIG="$2"; shift 2;;
    --output-ref) OUTPUT_REF="$2"; shift 2;;
    *) shift;;
  esac
done
[ -z "$WORKFLOW" ] && exit 0

LEDGER_DIR="$(cd "$(dirname "$0")/.." && pwd)/telemetry"
mkdir -p "$LEDGER_DIR"

jq -nc \
  --arg workflow "$WORKFLOW" --arg harness "$HARNESS" --arg trigger "$TRIGGER" \
  --arg outcome "$OUTCOME" --arg stop_reason "$STOP_REASON" \
  --arg ts_start "$TS_START" --arg duration "$DURATION" --arg iterations "$ITERATIONS" \
  --arg verified "$VERIFIED" --arg error_sig "$ERROR_SIG" --arg output_ref "$OUTPUT_REF" \
  '{
    schema: 2,
    workflow: $workflow,
    harness: (if $harness == "" then null else $harness end),
    trigger: (if $trigger == "" then null else $trigger end),
    declared_layer: null,
    ts_start: (if $ts_start == "" then null else ($ts_start | tonumber) end),
    ts_end: now | floor,
    duration_s: (if $duration == "" then null else ($duration | tonumber) end),
    iterations: (if $iterations == "" then null else ($iterations | tonumber) end),
    stop_reason: (if $stop_reason == "" then null else $stop_reason end),
    outcome: $outcome,
    verified: ($verified == "1" or $verified == "true"),
    error_sig: (if $error_sig == "" then null else $error_sig end),
    cost_usd: null,
    output_ref: (if $output_ref == "" then null else $output_ref end)
  }' >> "${LEDGER_DIR}/runs.jsonl" 2>/dev/null || true
} >/dev/null 2>&1 || true
exit 0
