# Post 7 — Loop and graph engineering in OpenCode

**Thesis:** OpenCode has no Stop hook — but its server/SDK architecture makes it the most hackable harness: the graph runtime primitives are all public API, and the plugin system lets you build whatever gate you want.

**Length:** ~1,300 words. **Sources:** [10, 11, 12, 13, 14, 19].

## What you get out of the box

- **Headless `opencode run`** with `--format json` NDJSON streams.
- **HTTP server + typed SDK**: `session.create({parentID})`, `promptAsync()`, `session.children()`, SSE `/event` stream, structured `outputFormat` responses [10, 11].
- **Plugins** (TypeScript): custom tools, event hooks, before/after tool-call interception [19].
- **Provider-agnostic**: any model, including local/self-hosted endpoints [19].

## Building the verifier loop (step-by-step)

1. No Stop hook exists — the loop is a shell wrapper: `opencode run "..."` inside `for i in 1 2 3`, verifier first, cap always. (Full script in post 3.)
2. Or write a plugin listening for session-idle events that re-prompts on verifier failure — more elegant, more moving parts.
3. Gotcha: subagent idle events look identical to main-session idle — filter on `parentID` or you'll mistake a finished subagent for a finished run [14].

## Building the two-node graph (step-by-step)

1. `opencode serve` (or the SDK client against a running instance).
2. Node one: `session.create()` → `session.prompt()` with `outputFormat` for a structured result.
3. Node two: fresh `session.create()` (clean context), prompt = artifact + bar only.
4. Router: your code branches on node two's structured verdict; `promptAsync()` + SSE when you want parallel branches.
5. Reference: `opencode-agent-teams` does DAG + topological sort + parallel levels in ~200 LOC [12]; your own `dynamic-workflow.ts` plugin does planner→router→executor.

## Pros

- Graph primitives are first-class API, not conventions: parent/child sessions, async prompts, event stream, structured output [10, 11].
- Plugin system = build your own Stop hook if you want one.
- Provider-agnostic: route graph nodes to different models per node (cheap verifier, strong author) [19].
- LSP diagnostics feed back after every edit — an in-harness micro-verifier loop [19].

## Cons

- No native blocking-stop contract: loop gating is shell or plugin code you maintain.
- `opencode run --format json` drops child-session events — headless multi-agent runs are fire-and-forget without `serve` + SSE [14].
- Client/server means a persistent process for the good stuff; more ops surface than a pure CLI [19].
- Younger ecosystem: fewer battle-tested patterns to copy than Claude Code.

## Pre-writing checklist

- [ ] Build both reference implementations; compare LOC against the Claude Code versions
- [ ] Reproduce the subagent-idle gotcha [14] and show the one-line filter that fixes it
- [ ] Run one graph node on a different (cheaper) model to demo per-node routing
