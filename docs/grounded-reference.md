# Prompt / Loop / Graph Engineering — Grounded Reference

Everything below is sourced. Confidence labels: [docs] = official documentation, [primary] = author/team's own writing, [secondary] = practitioner write-up.

## The five layers (Moka's taxonomy)

An agent is a while loop with layers of engineering wrapped around it [1]:

1. **Prompt engineering** — get one call right. One job per call, an example of expected quality, a schema that locks the output shape. Ceiling: if the agent fails the same way no matter how you reword, the bottleneck is outside the call [1].
2. **Context engineering** — get one window right. Curate what enters the finite window; summarize old turns, compress tool outputs, park big blobs in files [1].
3. **Harness engineering** — get one run right. Tools, permissions, verification, routing/recovery around the model. On Terminal Bench, a better harness moved the same model from top 30 to top 5 [1].
4. **Loop engineering** — get one goal right. The agent runs unattended until a goal-check passes. The hard part is the stop: run caps, token budgets, no-progress detection, a completion check the model can't fake [1, 2].
5. **Graph engineering** — get the whole workflow right. Transitions defined in code: if tests fail go back to fix, if they pass go to review, independent tasks in parallel, pause for human approval. "The graph is the rails, the loop is the motor" [1].

Anthropic's framing predates and complements this: **workflows** = LLMs orchestrated through predefined code paths; **agents** = LLMs dynamically directing their own process [3]. Moka's "graph" ≈ Anthropic's "workflow"; Moka's "loop" ≈ Anthropic's "agent" with engineered stop conditions. Anthropic's five workflow patterns — prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer — are all *workflows* (code owns control flow), not agents [3]. The convergent rule across Anthropic, OpenAI, and LangChain: find the simplest solution; add complexity only when it demonstrably improves outcomes [3, 4, 15].

## Loop engineering in Claude Code

Mechanism: the **Stop hook**. When the agent tries to end its turn, a registered script runs; exit code 2 blocks the stop and continues the conversation [5, docs].

The three rules practitioners keep rediscovering [7, 8, 9]:

1. **Exit 2 blocks; exit 1 does not.** Exit 1 is a non-blocking error — Claude Code waves the turn through. A gate ending in `exit 1` on its failure path is a placebo: it fails quietly, in the wrong direction, on the day tests are actually red [7].
2. **Check `stop_hook_active`.** The stdin payload includes this flag; it's true when the current stop exists because a previous block fired. If you block again on every stop, the session wedges shut. Standard guard: if the flag is set, exit 0 [7, 9]. (Belt-and-suspenders: Claude Code overrides a Stop hook after 8 consecutive blocks, tunable via `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` [8].)
3. **The check must be external and falsifiable.** Run the test suite, check the file, query `gh pr checks` — never ask the model if it's done. Canonical minimal gate: run `npm test`; green → exit 0; red → `{"decision":"block","reason":"..."}` [7, 9].

Practical notes: set an explicit short `timeout` on the hook (a slow check taxes every turn); scope conditions tightly or the gate becomes noise you learn to ignore [7]; hooks run synchronously, so put heavy checks on Stop, light ones on PostToolUse [9].

Headless alternative: `claude -p` in a bash until-loop with an external check — same pattern, no hook registration. The Agent SDK formalizes this: `query()` with `maxTurns`, resumable `session_id`, and `ResultMessage` subtypes (`success`, `error_max_turns`, `error_max_budget_usd`) your code branches on [6, docs]. That's a loop with a coded exit condition and resume.

## Loop engineering in OpenCode

No Stop-hook equivalent is documented; the idiomatic loop is a **shell wrapper around `opencode run`** (headless) with an external check, or a **plugin** reacting to `session.idle` events [10, 11]. Caution: subagent idle events are structurally identical to main-session idle events — filter by `parentID` or you'll treat a finished subagent as a finished run [14, primary issue].

## Graph engineering in OpenCode

The substrate is genuinely good — the SDK/server exposes everything a graph runtime needs [10, 11, docs]:

- `session.create({ parentID })` / `session.children()` — parent-child session trees (the nodes).
- `session.promptAsync()` — fire-and-forget, returns 204 (parallel branches).
- `GET /event` (SSE) — real-time completion subscription (the edge-trigger).
- `session.prompt` with `outputFormat` — structured output your router branches on (the transition conditions).
- Per-session `agent` routing and permissions — specialized nodes.

Working examples: the **opencode-agent-teams** npm plugin implements `team_create` (a DAG of tasks with `depends_on`), `team_run` (topological sort, parallel execution per dependency level via `Promise.all`), and `background` (fire-and-forget with result injection into the parent) in ~200 LOC on exactly those primitives [12, primary]. The plugin-based orchestration proposal in issue #20849 lays out the same architecture and explicitly recommends ~5 concurrent sessions [13]. Gap to know: `opencode run --format json` drops child-session events — headless multi-agent runs are fire-and-forget unless you use `opencode serve` + SSE (issue #33397, with a proposed patch) [14].

Your `dynamic-workflow.ts` is this pattern: planner builds a spec, router maps steps to model tiers, executor runs sequence/parallel/pipeline phases over child sessions.

## Graph engineering in Claude Code

Two levels:

1. **Task-tool fan-out**: an orchestrator agent spawns subagents; `SubagentStop` hooks and the 8-block cap apply per subagent [5, 8].
2. **Agent SDK orchestration**: your code drives `query()` calls, branches on `ResultMessage`, resumes sessions by ID across restarts, and uses hooks (`PostToolBatch` can halt the loop before the next model call) as in-band circuit breakers [5, 6]. This is the rails-and-motor split in its cleanest form: the model is the motor inside each node; your code is the rails between them.

## The decision rubric (what to tell readers)

- **Stay prompt** when one call does the job and a human reads the output. Anthropic: maybe don't build agentic systems at all [3].
- **Loop** when: repeated trigger + a done-condition a script can check + the path varies per run. The engineering is the exit condition, not the retry.
- **Graph** only when at least one is true: **parallel branches, human approval mid-run, resume-after-crash** [1]. Otherwise the loop is enough.
- **Neither — fix the harness** when the same error signature repeats: a tool/permission/verification fix, not a layer jump [1].

### The 4-question gut check (AI Builder Club) [17]

Before claiming a loop became a graph, count the yeses:
1. Did you split one context into separate, specialized ones (not one agent switching hats)?
2. Is there a real fan-out/fan-in (parallel + merge, not a sequence drawn as boxes)?
3. Can you read the control flow as a diagram (routing defined up front, not emergent)?
4. Did the objective and success bar change? (If "done and correct" is identical, only the drawing changed.)

0–1 yes: a loop wearing a graph diagram. 2–3: genuinely composing. The one-line test: if you can name the specialized roles and draw an arrow between them, it's a graph; if one job needs to repeat until right, it's a loop.

### The migration path that actually works [17]

**A loop is a single node in a graph** — you don't graduate from loops, you wrap them:
1. Keep the loop; it becomes node one.
2. Split off the step failing inside it — almost always the *reviewer*, because a loop reviewing its own draft in the same context rubber-stamps it. Pulling review into a fresh-context node is the highest-value first edge.
3. Write down what node one hands node two (the state schema) — this is where graphs silently break.
4. Add fan-out only where you already iterate over N things one at a time.
5. Stop when the next node stops paying. Two or three well-separated nodes cover most real uses.

### Team-level loops (Augment Code) [18]

The outer shape of an agentic SDLC loop: **trigger → execution → verification (with human checkpoints placed by risk) → outcome → improve** (each run's trace feeds back into prompts/tests/criteria). Two rules worth stealing: "a loop that generates output nobody ships is not a successful loop" — loops must be accountable for finishing something — and measure loops on **outcomes per dollar, not output per dollar**. Boris Cherny (Claude Code creator): "I don't prompt Claude anymore, I write loops" [18].

### Prior art note (for the skeptics section)

Graph orchestration predates the July 2026 term: LangGraph `StateGraph` (add_node/add_edge), Microsoft AutoGen GraphFlow, Google ADK graph workflows + A2A delegation all shipped before "graph engineering" trended [17]. David K. Piano (XState creator) and Paweł Huryn are the named skeptics — Huryn's point: whether drawn as loop or graph, the discipline underneath (name the objective and the bar) doesn't change [17].

### Harness internals worth knowing (Cefboud deep dive) [19]

How OpenCode actually works under the hood: Bun/Hono HTTP server + Go TUI; the agent loop is AI SDK `streamText` with `stopWhen` controlling iterations; tools are description+schema+execute, and the *description is prompt engineering for the tool*; LSP diagnostics feed back into context after every edit (an in-harness verifier loop); the Task tool spawns a subagent as a **new session with its own context window, tools, and model**; git-write-tree snapshots before each step enable revert. Context compaction auto-summarizes at ~90% of the window.

### Claude Code native loop commands (Claude Code Masterclass) [20]

`/goal`, `/loop`, `/schedule` confirmed present in Claude Code (verified in a live session, 2026-08-13). The evaluator-model detail below is as-described by [20]; behavior-level details (separate evaluator call) not independently confirmed against official docs.

- `/goal <binary condition>, stop after N tries` — outcome-based loop. Key detail: **a separate evaluator model call checks the goal condition after each iteration** — verification is architecturally outside the working context, which is exactly the fresh-reviewer principle from [17]. Good conditions are measurable and binary ("all 47 tests passing"); weak ones ("make the code better") never exit.
- `/loop <interval> <task>` — time-based loop, no stop condition, dies when the terminal closes. For ongoing event-reactive work (poll PR comments, watch CI).
- `/schedule <cron-ish> <task>` — `/loop` moved to Anthropic's cloud; survives laptop close. For digests and fixed-schedule work.
- The combined **proactive pattern**: `/schedule` as the trigger + `/goal` as the batch completer ("every hour: check for bug reports" + "don't stop until every report found this run is triaged").

The article's three qualities of a good loop, which map cleanly onto the cooking-hook machinery:
1. **Clear stop condition** = success condition (binary, measurable) + safety cap (max iterations). The cap protects the budget from a stuck agent.
2. **Context management** — after ~a dozen iterations the window is polluted with old test logs and file states. Fixes: keep only latest error + file in question, `/compact` old steps, restate the goal every cycle (CLAUDE.md is reloaded each iteration).
3. **Error recovery** — design the loop assuming commands will fail; the stop condition keys on the *goal being met*, not on commands running clean.

Four phases every loop runs: **discover → plan → execute → verify**. And the three limitations that push a loop toward a graph (same conclusion as [17], independently): it can't credibly review its own fixes, it can't parallelize, and you can't read the flow as a diagram from a 47-tool-call transcript.

Origin detail: Boris Cherny's quote is dated June 30, 2026 here — "I no longer prompt Claude anymore. I have loops running that prompt Claude and figure out what to do next. My job is to write loops." [20]

## References

1. Moka, *Agentic Engineering 101* — https://craftbettersoftware.com/p/agentic-engineering-101 [primary]
2. Moka, *Loop Engineering 101* — https://craftbettersoftware.com/p/loop-engineering-101 [primary]
3. Anthropic, *Building Effective Agents* — https://www.anthropic.com/engineering/building-effective-agents [primary]
4. Claude, *Common workflow patterns for AI agents* — https://claude.com/blog/common-workflow-patterns-for-ai-agents-and-when-to-use-them [primary]
5. Claude Code docs, *Hooks reference* — https://code.claude.com/docs/en/hooks [docs]
6. Claude Code docs, *How the agent loop works (Agent SDK)* — https://code.claude.com/docs/en/agent-sdk/agent-loop [docs]
7. Kothari, *How Claude Code stop hooks work* — https://amitkoth.com/claude-code-stop-hooks/ [secondary]
8. backgrind, *Claude Code Hooks Explained: Events, Payloads, Exit Codes* — https://backgrind.com/blog/claude-code-hooks-explained/ [secondary]
9. Claude Lab, *Running Claude Code Hooks as a Quality Gate* — https://claudelab.net/en/articles/claude-code/claude-code-hooks-quality-gate-reliability [secondary]
10. OpenCode docs, *SDK* — https://opencode.ai/docs/sdk/ [docs]
11. OpenCode docs, *Server* — https://opencode.ai/docs/server/ [docs]
12. *opencode-agent-teams* — https://www.npmjs.com/package/opencode-agent-teams [primary]
13. opencode issue #20849, *Plugin-based agent orchestration layer* — https://github.com/anomalyco/opencode/issues/20849 [primary]
14. opencode issue #33397, *Expose child session events in NDJSON stream* — https://github.com/anomalyco/opencode/issues/33397 [primary]; related: #30043, *session.status should include parentID* — https://github.com/anomalyco/opencode/issues/30043
15. LangChain, *How to think about agent frameworks* — https://www.langchain.com/blog/how-to-think-about-agent-frameworks [primary]
16. Zhang (Anthropic), *How We Build Effective Agents* talk summary — https://shellypalmer.com/2026/04/how-anthropic-thinks-about-agents-workflows-and-tasks/ [secondary]
17. AI Builder Club, *Graph Engineering vs Loop Engineering* — https://www.aibuilderclub.com/blog/graph-engineering-vs-loop-engineering [secondary, verified 2026-08-13]. Sibling decision guide: https://www.aibuilderclub.com/blog/agent-graph-vs-loop-when-to-use
18. Perneti (Augment Code), *What is loop engineering?* — https://www.augmentcode.com/guides/what-is-loop-engineering [primary/vendor, verified 2026-08-13]
19. Abboud, *How Coding Agents Actually Work: Inside OpenCode* — https://cefboud.com/posts/coding-agents-internals-opencode-deepdive/ [secondary, source-code read, verified 2026-08-13]
20. Njenga, *Claude Code Loop & Graph Engineering Masterclass (Part 1)* — https://open.substack.com/pub/claudecodemasterclass/p/claude-code-loop-and-graph-engineering [secondary, verified 2026-08-13]. Part 2 (graph engineering with agent teams) announced for 2026-08-17, not yet published at time of writing.
21. Goodhart's law — Goodhart (1975, monetary policy: "any observed statistical regularity will tend to collapse once pressure is placed upon it for control purposes"); generalized by Hoskin (1996); canonical formulation by Strathern, *'Improving ratings': audit in the British University system*, European Review 5(3):305–321 (1997): "when a measure becomes a target, it ceases to be a good measure." [primary, verified 2026-08-13] Applied here: an agent optimizing an unguarded metric will reduce the work instead of the time — hence every perf goal pairs with a correctness gate.

Unverified (surfaced in third-party research digests, not yet checked — treat as leads, not citations):
- Raj, *Prompt vs Loop vs Graph Engineering* (Medium/The Gravity)
- *AFlow: Automating Agentic Workflow Generation* (arXiv 2410.10762)
- Greyling, *Agent Teams & Subagents in Claude Code* (Medium)
- *Prompts vs Skills vs Loops* (YouTube, https://www.youtube.com/watch?v=32jdWMbvgbw)
