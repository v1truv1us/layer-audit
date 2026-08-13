# Loop and graph engineering mechanics, per harness

Companion to `grounded-reference.md` (which has the citations). This file is the practical "how do I actually do it" mapping for Claude Code and OpenCode.

## The layer-to-feature mapping

| Layer | Claude Code | OpenCode |
|-------|-------------|----------|
| Prompt | `CLAUDE.md`, skill `SKILL.md`, command `.md`, subagents in `.claude/agents/` | `AGENTS.md`, skills, commands, agents in `~/.config/opencode/agents/` |
| Context | `@file` refs, memory, hook-injected context, MCP resources | files loaded per skill/command, MCP resources |
| Harness | hooks (PreToolUse/PostToolUse/Stop), `permissions` in settings.json, MCP tools | plugins (TS event hooks), `permission` rules, MCP, custom tools |
| Loop | Stop hook exit 2 (cooking pattern), headless `claude -p` in a bash until-loop | shell loop around `opencode run`, plugin `session.idle` events |
| Graph | Task-tool subagent fan-out, Agent SDK `query()` orchestration | plugins/SDK spawning child sessions (e.g. `dynamic-workflow.ts`) |

## Loop engineering — three real implementations

1. **Stop hook** (Claude Code): agent tries to stop → hook checks a marker/condition → exit 2 forces continuation. Rules: exit 2 blocks (exit 1 does *not* — it's a silent placebo); check `stop_hook_active` and bow out if set; the harness force-overrides after 8 consecutive blocks. The check must be external and falsifiable — test suite green, file exists, `gh pr checks` passing.
2. **Shell wrapper** (either harness): `until check_done; do <headless call>; done` with an iteration cap. This is what scheduled launchd jobs need to become loops — the check is the engineering, not the retry.
3. **Scheduled re-invocation**: cron/launchd re-firing a headless call that reads its own prior state from files. Weakest form; no memory between runs except what's on disk.

If the done-condition can't be written as a shell test, there is no loop yet.

## Graph engineering — three levels, weakest to strongest

1. **Prose state machine**: a skill that says "if tests fail, return to step 3." Works, but the model re-interprets the routing every run. A graph in name only.
2. **Script-chained headless calls**: bash/python runs stage A, inspects the result, branches in code to B or C, checkpoints state to a file. Deterministic routing, resumable.
3. **Plugin/SDK orchestration**: code spawns child sessions per node, runs independent nodes in parallel, routes on structured outputs. OpenCode: `session.create({parentID})` + `promptAsync()` + SSE `/event` + `outputFormat` structured responses. Claude Code: Agent SDK `query()` with `maxTurns`, resumable `session_id`, `ResultMessage` subtypes.

## The decision rule

- Stop hook + exit check covers ~80% of "should this be a loop?" cases.
- Reach for a graph only when at least one holds: **parallel branches, human approval mid-run, resume-after-crash**. Otherwise a loop is enough — "the graph is the rails, the loop is the motor."
- A skill invoked by hand once in a while stays a prompt. Layer upgrades pay off only on repeated, triggered work.

## The decision flowchart

```
              ┌──────────────────────────────┐
              │   Incoming issue / workflow │
              └──────────────┬───────────────┘
               Single-turn transformation,
               no verification needed?
                  ┌──────────┴──────────┐
                YES                    NO
                  │   Needs iterative trial/error
                  │   against a scriptable verifier?
                  │        ┌──────────┴──────────┐
                  │      YES                    NO
                  │        │   Multiple specialized roles or
                  │        │   parallel branches to stop
                  │        │   context rot / self-review?
                  │        │        ┌──────────┴──────────┐
                  │        │      YES                   NO → harness fix
        ┌─────────▼───────┐┌───────▼────────┐  ┌─────────▼─────────┐
        │ PROMPT          ││ LOOP           │  │ GRAPH             │
        └─────────────────┘└────────────────┘  └───────────────────┘
```

## Criteria comparison

| Dimension | Prompt | Loop | Graph |
|-----------|--------|------|-------|
| Topology | 1 → 1 | one node, edge to itself | N nodes, explicit edges |
| Verification gate | human eyeball | machine exit code (tests, lint, file check) | multi-stage gates, specialist verifier nodes |
| Context | single turn, ephemeral | one session (context saturates over long runs) | isolated clean window per node |
| Primary failure mode | hallucination | infinite loop / fix-regression thrash | state leaks between nodes, merge drops data, routing bugs |
| Best for | formatting, commit messages, one-off refactors | bug fixes, failing tests, dep updates, scheduled briefs | multi-file features, cross-repo work, research→write→review pipelines |

## Canonical verifier loop (corrected)

The loop example circulating in research digests has a shell bug (`-lt$MAX_RETRIES` — missing space, never runs). Working version:

```bash
#!/usr/bin/env bash
MAX_RETRIES=5
COUNT=0
VERIFY="npm test"

while [ "$COUNT" -lt "$MAX_RETRIES" ]; do
  if $VERIFY; then
    echo "Verifier passed."; exit 0
  fi
  COUNT=$((COUNT + 1))
  claude -p "The command '$VERIFY' failed (attempt $COUNT/$MAX_RETRIES). Read the error output, inspect the relevant files, and fix it." --dangerously-skip-permissions
done

echo "Exceeded $MAX_RETRIES attempts."; exit 1
```

Notes: run the verifier *before* invoking the agent (don't burn a call when already green); pass the attempt count so the agent knows the loop is watching; exit non-zero on exhaustion so a wrapper (launchd, run-locked) records the failure.
