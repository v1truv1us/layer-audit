# Post 6 — Loop and graph engineering in Claude Code

**Thesis:** Claude Code has the most engineered surface for this work — hooks give you loop control no other harness matches — but the graph layer costs you SDK code.

**Length:** ~1,300 words. **Sources:** [5, 6, 7, 8, 9, 20]. **Companion task:** the same verifier loop + two-node graph as posts 7–8.

## What you get out of the box

- **Hooks** (30 events): `Stop`, `SubagentStop`, `PreToolUse`, `PostToolBatch` — interception points on every phase of the agent loop [5, 8].
- **`/goal`, `/loop`, `/schedule`** — native loop commands (confirmed present 2026-08-13) [20].
- **Agent SDK** — `query()` with `maxTurns`, budget caps, resumable `session_id`, typed result messages [6].
- **Subagents + Task tool** — fresh-context delegation [19 describes the OpenCode equivalent; Claude Code's is analogous].

## Building the verifier loop (step-by-step)

1. Register a `Stop` hook in `~/.claude/settings.json` pointing at a bash script.
2. Script contract: verifier green → `exit 0`; red → print reason to stderr, `exit 2`.
3. Guard: read stdin JSON, if `.stop_hook_active == true` → `exit 0` immediately.
4. Set `timeout` on the hook (default 600s is a hang risk every turn).
5. Test: red suite → confirm block; `exit 1` variant → confirm it *doesn't* block (the placebo); 8 consecutive blocks → confirm harness override.

## Building the two-node graph (step-by-step)

1. Node one = Agent SDK `query()` doing the work, `session_id` saved.
2. Node two = a **new** `query()` (fresh context) receiving only the artifact + acceptance bar, returning a structured verdict.
3. Router = your TypeScript/Python `if` on the verdict; resume node one by `session_id` with the critique.
4. Checkpoint state to disk between nodes.

## Pros

- Stop hooks are the strongest loop primitive anywhere: in-band, per-turn, with a blocking contract and a loop-guard flag.
- The 8-block override means a buggy gate can't wedge a session forever [8].
- `session_id` resume makes crash-surviving graphs nearly free [6].
- `/goal`'s separate evaluator call (if confirmed) is verification-outside-the-context as a built-in [20].

## Cons

- Hooks are config + bash; a mistyped path silently disables a gate (watch for the non-blocking notice) [5].
- The exit-code contract is a footgun: `exit 1` looks like "block" to every shell programmer and means "ignore me" [7].
- No native DAG/parallel primitive — parallel fan-out is your code over the SDK or Task tool calls.
- Cloud `/schedule` runs on Anthropic infra: convenient, but your loop's trigger now depends on a vendor.

## Pre-writing checklist

- [x] Confirm `/goal` `/loop` `/schedule` exist — **confirmed 2026-08-13**
- [ ] Build both reference implementations and time them
- [ ] Deliberately trigger the exit-1 placebo and the 8-block override; screenshot both
