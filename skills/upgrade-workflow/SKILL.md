---
name: upgrade-workflow
description: Build approved layer-audit proposals — upgrade a workflow from prompt to loop (or fix harness gaps) after the user moves a proposal into proposals/approved/. Use when the user says "build approved proposals", "upgrade workflow", or after the weekly layer audit surfaces approved items.
metadata:
  category: user-invoked
disable-model-invocation: true
---

# Upgrade Workflow

Consumes approved proposals from the layer-audit queue and implements the layer upgrade.
The filesystem is the queue: `~/Github/layer-audit/proposals/{pending,approved,rejected,done}/`.

## Procedure

1. List approved proposals: `ls ~/Github/layer-audit/proposals/approved/*.md`. If none, say so and stop.
2. For each proposal (oldest first), read the frontmatter: `workflow`, `issue`, `current_layer`, `proposed_layer`, `evidence`.
3. Dispatch on `issue` type. Only the two types below are supported — anything else (especially `graph` targets), say "manual design needed" and leave the file in `approved/`.

### stuck-at-prompt → loop

Wrap the one-shot workflow in a cooking-loop with a falsifiable goal-check:

1. Read the workflow's run script (`~/.pi/agent/scripts/run-<name>.sh`) and registry entry (`~/Github/layer-audit/registry.json`).
2. Define the done-condition from the registry `output_glob`/`min_bytes` (e.g. "output file for today exists and is ≥ min_bytes") plus any content check the evidence implies.
3. Add a retry wrapper in the run script: after the `pi -p` call, verify the done-condition; if unmet, retry up to 3 times with a short backoff, logging each attempt via `emit-telemetry.sh --workflow <name> --outcome failure --stop-reason error`. On final failure exit non-zero (run-locked records it).
4. Mark `verified` only when the done-condition check passes: change the run to emit `--verified 1` on success.

### harness-gap

1. Read the top `error_sig` values from the proposal evidence and reproduce: run the workflow's command manually, capture the first error line.
2. Fix the tool/permission/environment cause — not the prompt, not retries. If the cause isn't clear after one reproduction attempt, stop and write findings as a comment in the proposal file, leave it in `approved/`.
3. Re-run the workflow once to confirm the error signature is gone.

## Finish

1. Move the proposal from `approved/` to `done/`, appending a `## Resolution` section: what changed (file paths), verification command run, and result.
2. Update the registry entry if the layer changed (`declared_layer`, and bump any new fields the upgrade introduced).
3. Report one line per proposal: `workflow: issue → what changed → how it was verified`.
4. Remind the user the next weekly audit (Mon 07:00) confirms whether the signal dropped.

## Guardrails

- Never auto-build from `pending/` — only `approved/`.
- Never widen scope: one proposal, one change. Adjacent fixes are new proposals.
- If a proposal's workflow file doesn't match what the proposal describes (drift), stop and say so.
