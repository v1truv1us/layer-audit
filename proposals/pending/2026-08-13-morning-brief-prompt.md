---
id: 2026-08-13-morning-brief-prompt
workflow: morning-brief
issue: hung-runs
current_layer: prompt
proposed_layer: prompt
score: 3.30
evidence: {"runs_30d": 24, "fail_rate": 0.083, "silent_rate": 0.0, "cap_rate": 0.0, "repeat_error": 0.083, "unverified": 1.0, "median_duration_s": 25, "perf": {"recent_median_s": 18, "baseline_median_s": 25, "regressed": false}, "top_errors": [["exit1", 2]]}
status: pending
---
# morning-brief: hung-runs

## Problem
≥10% of runs exceeded 1 hour — the trigger fired, the agent never came back, and the wrapper reported OK. Add a hard timeout to the run wrapper (e.g. `timeout` command or launchd `TimeOut`) so hangs fail loudly instead of pretending to succeed.

## Evidence (30-day window)
- Runs: 24 | fail 8% | silent 0% | cap 0% | repeat-error 8% | unverified 100%
- Top error signatures: `exit1` x2

## Proposed change
Keep `morning-brief` at **prompt** — fix the performance, don't change the architecture.

## Verification plan
Run the upgraded workflow once manually and confirm the audit signal drops on the next weekly audit.

## Rollback
Revert the skill/script change; the previous layer behavior is preserved in git or the file's prior version.
