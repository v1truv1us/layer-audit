# layer-audit

Finds which of my agent workflows are engineered at the wrong layer — prompt vs loop vs graph, per [Daniel Moka's Agentic Engineering 101](https://craftbettersoftware.com/p/agentic-engineering-101) — without me having to decide what to look at. Issues surface themselves; upgrades are proposed, approved, then built.

## How it works

```
run-locked.sh (all launchd pi jobs) ──┐
cooking-stop-hook.sh (all loops)    ──┼─> telemetry/runs.jsonl (gitignored)
                                      │
scripts/run-layer-audit.sh (Mon 07:00, launchd)
  └─> audit.py
        ├─> issues/issues-YYYY-MM-DD.md      ranked issue table
        └─> proposals/pending/<id>.md        upgrade proposals
                                               │ mv to approved/
                                               ▼
                                     upgrade-workflow skill builds it
```

1. **Telemetry** — `scripts/emit-telemetry.sh` appends one schema-2 JSONL record per run. Wired into `~/.pi/agent/scripts/run-locked.sh` (covers every scheduled pi job) and `~/.claude/hooks/cooking-stop-hook.sh` (covers every cooking loop; emits on cap-hit and stale-marker crash).
2. **Audit** — `audit.py` is deterministic (no LLM in the ranking path). Backfills from `~/.pi/agent/logs/runtimes.log`, merges emitter records, checks output files for silent failures, scores each workflow over a 30-day window, classifies issues, writes proposals.
3. **Approval** — the filesystem is the queue. Review `issues/`, move a proposal from `pending/` to `approved/` or `rejected/`.
4. **Build** — the `upgrade-workflow` skill (opencode + claude copies in `skills/`) consumes `approved/`, implements prompt→loop wraps and harness-gap fixes, moves the file to `done/`.

## Signals and issue types

`score = runs_30d × (0.35·fail + 0.30·silent + 0.15·cap + 0.10·repeat_error + 0.10·unverified)`

| Signal | Issue | Proposal |
|--------|-------|----------|
| prompt-layer + fail>15% or silent>10% | `stuck-at-prompt` | wrap in loop with verification |
| same `error_sig` ≥30% of runs | `harness-gap` | fix tool/permission, not retries |
| loop-layer + cap≥30% | `non-terminating-loop` | fix goal-check or promote to graph |
| runs but not in registry | `unregistered-workflow` | classify + register |

Hung runs (>1h duration) are reported informationally, not scored. `registry.json` holds per-workflow layer, trigger, output check (`output_glob`, `min_bytes`), and aliases (cross-harness names share one key).

## Docs

- `docs/grounded-reference.md` — the five layers, mechanics per harness, decision rubric, all web-sourced
- `docs/classification-2026-08-12.md` — every workflow classified with rationale
- `docs/blog-draft.md` — first-person article draft based on the above

## External wiring (absolute paths — update if this repo moves)

| File | What it references here |
|------|------------------------|
| `~/.pi/agent/scripts/run-locked.sh` | `scripts/emit-telemetry.sh` |
| `~/.claude/hooks/cooking-stop-hook.sh` | `scripts/emit-telemetry.sh` (2 sites) |
| `~/Library/LaunchAgents/com.pi.layer-audit.plist` | `scripts/run-layer-audit.sh` (copy in `deploy/`) |
| `~/.config/opencode/skills/upgrade-workflow/SKILL.md` | proposals queue (canonical copy in `skills/`) |
| `~/.claude/skills/upgrade-workflow/SKILL.md` | same |

`audit.py` self-locates via its own path (`LAYER_AUDIT_HOME` overrides for tests). It still *reads* `~/.pi/agent/logs/runtimes.log` — that's pi's data, not this repo's.

## Operate

```bash
python3 audit.py                                    # run audit now
launchctl kickstart gui/$(id -u)/com.pi.layer-audit # run the scheduled job now
ls proposals/pending/                               # what wants approval
```
