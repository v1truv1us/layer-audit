# Layer-fit classification — 2026-08-12

Rubric (Moka + Anthropic):
- **prompt**: one call gets it done; human reads the output; no falsifiable done-condition worth enforcing.
- **loop**: repeated trigger + a done-condition a script can check + the path to done varies per run.
- **graph**: known, repeated multi-stage workflow that needs explicit transitions — parallel stages, pause/approve/resume, or restart-survival.

Ranked by expected value (frequency × current pain).

## Upgrade to LOOP

| Workflow | Now | Why loop | Effort |
|----------|-----|----------|--------|
| morning-brief | prompt | Runs daily, fails 8%, hangs (one 5-day "OK"), zero verification — a done-condition exists (output file ≥ min_bytes with 5 sections). Wrap in verify-retry loop. | ~1h |
| weekly-status | prompt | Same shape as morning-brief, weekly. | ~30m |
| triage | prompt | Same shape; consumes a queue, so done-condition is "output written + queue cleared". | ~30m |
| meeting-prep | prompt | Same shape as triage. | ~30m |

## Upgrade to GRAPH

| Workflow | Now | Why graph | Effort |
|----------|-----|-----------|--------|
| second-brain chain (7 cron jobs) | 7 independent cron entries | Stages are time-ordered by guesswork (03:00, 03:05, 03:15…), not by dependency. Independent stages could parallelize; a crashed stage silently breaks the chain. One graph with explicit edges + checkpointing replaces 7 cron lines. | ~3h |
| ralph-wiggum | loop (prose) | Its gap-analysis routing table is graph logic written in prose — the model re-interprets transitions every run. Coding the transitions (via dynamic-workflow.ts) makes it checkpointable and resumable for real. | ~4h |
| orchestrate | designed, unbuilt | Already specified as a graph (plan.json → workers → verifiers). Build it on dynamic-workflow.ts instead of a new runtime. | ~4h |

## Upgrade to HARNESS (not a layer jump — fix the run, not the architecture)

| Workflow | Why |
|----------|-----|
| robinhood-cycle | Scheduled single run handling money. Needs verification + alerting on the run, NOT autonomy. Keep human-in-loop. |

## Stay PROMPT (correctly layered)

| Workflow | Why |
|----------|-----|
| weekly-review, workflow-from-chats | Manual, low-frequency, human is the loop. |
| disabled launchd jobs (competitor-scan, doc-review, poly-audit, research-deep) | Disabled; revisit if re-enabled. |
| test-fix-loop, investigation-loop, loop-on-ci, verification-loop, dreaming-consolidator, ud-audit-loop | Already loops with caps and exit conditions. Watch `cap_rate` telemetry for non-termination. |

## What happens next

These recommendations are now in `registry.json` as `recommended_layer`. The weekly audit (Mon 07:00) raises a `layer-mismatch` proposal for any active workflow whose declared and recommended layers differ, and a failure-signal proposal for anything actually breaking. Approve by moving a file from `proposals/pending/` to `proposals/approved/`, then run the `upgrade-workflow` skill.
