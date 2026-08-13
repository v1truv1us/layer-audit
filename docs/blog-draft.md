# Blog draft — working title: "Your agent isn't dumb, it's under-engineered: a field guide to prompt, loop, and graph engineering"

> Status: first draft. Voice target: practitioner explaining to practitioners, first person, concrete. ~1,100 words. Edit freely — flagged spots need your decision.

---

A few weeks ago I read Daniel Moka's *Agentic Engineering 101* [1] and had an uncomfortable realization: every "my agent is being dumb" complaint I've had this year was actually a misdiagnosis. The model was fine. I had engineered the wrong layer.

Moka's frame is five layers, and the industry has zoomed out one layer at a time: prompt engineering (2024), context engineering (2025), harness engineering (early 2026), loop engineering (mid 2026), graph engineering (now). Nothing died — the prompt is still in there, it's just the smallest part of the job. Here's the version of that framework I've actually been using, mapped onto the tools I run every day (Claude Code and OpenCode), with the receipts.

## The five layers in one paragraph each

**Prompt engineering** is getting one call right: one job, an example of what good looks like, a schema that locks the output. It has a ceiling. Moka's diagnostic: if your agent fails the same way no matter how you reword the prompt, the bottleneck is outside the call.

**Context engineering** is getting one window right — curating what enters the finite window so the good stuff isn't buried in the middle where accuracy drops.

**Harness engineering** is getting one run right: tools, permissions, and *verification*. Moka cites Terminal Bench, where moving the same model into a better harness took it from the top 30 to the top 5. Same model. The machinery was the difference.

**Loop engineering** is getting one goal right: the agent runs without you until a goal-check passes. The hard part isn't the retry, it's the stop. A loop with no honest exit condition is an agent that reports success while the tests are red.

**Graph engineering** is getting the workflow right: the transitions live in code. If tests fail, back to fix; if they pass, on to review; independent branches run in parallel; a human approval pauses and resumes days later. Moka's line is the one to steal: *the graph is the rails, the loop is the motor.*

Anthropic said the same thing earlier with different words [3]: workflows are LLMs orchestrated through predefined code paths; agents are LLMs choosing their own path. Graph ≈ workflow, loop ≈ agent-with-a-good-stop. Both camps land on the same rule: use the simplest thing that works, and only climb a layer when the current one demonstrably can't.

## What these layers actually look like in my harnesses

This is the part I couldn't find written down anywhere, so I dug through the docs and the issue trackers.

**Loop engineering in Claude Code is a Stop hook.** When the agent tries to end its turn, a script you registered runs; exit code 2 refuses the stop and the turn continues [5]. Three rules, each learned by someone the hard way [7, 8, 9]:

1. Exit 2 blocks; **exit 1 does not**. Exit 1 is a "non-blocking error" and the turn ends anyway. A gate whose failure path says `exit 1` is a placebo — it fails silently on exactly the day you needed it.
2. Check `stop_hook_active` in the stdin payload. If a previous block caused this stop, bow out, or your gate jams shut forever. (Claude Code also force-overrides a Stop hook after 8 consecutive blocks [8] — the harness has your back, but don't rely on it.)
3. The check must be something the model can't fake: run the test suite, check the output file exists, ask `gh pr checks`. Never ask the model if it's done.

The minimal version is fifteen lines of bash: run tests, green → exit 0, red → block with a reason. That *is* loop engineering. The engineering was never the loop; it's the exit condition.

**Graph engineering in OpenCode is the SDK.** The primitives are all there [10, 11]: `session.create({ parentID })` for child-session trees, `session.promptAsync()` for fire-and-forget parallel branches, an SSE event stream for completion triggers, structured `outputFormat` responses your router can branch on. Someone already proved it fits in ~200 lines: the `opencode-agent-teams` plugin implements a DAG of tasks with `depends_on` edges, topological sort, and parallel execution per dependency level [12]. Claude Code's Agent SDK gives you the same shape from the outside: your code drives `query()` calls, branches on the result type, and resumes sessions by ID after a crash [6].

## The decision rule, and my own workflows graded by it

After all the reading, the rubric I trust fits on an index card:

- **Stay a prompt** when one call does the job and a human reads the output anyway.
- **Make it a loop** when it has a repeated trigger, a done-condition a script can check, and a path that varies run to run.
- **Make it a graph** only when you need at least one of: parallel branches, a human approval mid-run, or resume-after-crash. Otherwise the loop is enough.
- **And sometimes the answer is neither** — if the same error repeats every run, that's a harness bug. Fix the tool, not the architecture.

Then I did the uncomfortable part: I graded my own automation. I run about a dozen scheduled agent jobs on my machine. My morning briefing — a single headless prompt fired by launchd every day at 8am — had silently produced garbage 8% of the time and once "succeeded" after hanging for five days. One prompt, no verification, no exit condition. Textbook stuck-at-prompt; it's getting a shell-wrapper loop with an output check. My knowledge-base pipeline is seven cron jobs scheduled five minutes apart by pure guesswork about how long each stage takes — that's a graph waiting to be drawn, with explicit dependencies and parallel stages. And my trading job? It stays a prompt with a human in the loop. The rubric says loops are for goals a script can verify, and "don't lose money" is not that script.

## The one-line version

Average developers engineer the prompt. The rest of the job is the environment around it — and now I have a way to tell which layer is actually broken before I start polishing wording that was never the problem.

---

## References

1. Moka, *Agentic Engineering 101* — https://craftbettersoftware.com/p/agentic-engineering-101
2. Moka, *Loop Engineering 101* — https://craftbettersoftware.com/p/loop-engineering-101
3. Anthropic, *Building Effective Agents* — https://www.anthropic.com/engineering/building-effective-agents
4. Claude, *Common workflow patterns for AI agents* — https://claude.com/blog/common-workflow-patterns-for-ai-agents-and-when-to-use-them
5. Claude Code docs, *Hooks reference* — https://code.claude.com/docs/en/hooks
6. Claude Code docs, *How the agent loop works* — https://code.claude.com/docs/en/agent-sdk/agent-loop
7. Kothari, *How Claude Code stop hooks work* — https://amitkoth.com/claude-code-stop-hooks/
8. backgrind, *Claude Code Hooks Explained* — https://backgrind.com/blog/claude-code-hooks-explained/
9. Claude Lab, *Hooks as a Quality Gate* — https://claudelab.net/en/articles/claude-code/claude-code-hooks-quality-gate-reliability
10. OpenCode docs, *SDK* — https://opencode.ai/docs/sdk/
11. OpenCode docs, *Server* — https://opencode.ai/docs/server/
12. *opencode-agent-teams* — https://www.npmjs.com/package/opencode-agent-teams
13. opencode issue #20849 — https://github.com/anomalyco/opencode/issues/20849
14. opencode issue #33397 — https://github.com/anomalyco/opencode/issues/33397
15. LangChain, *How to think about agent frameworks* — https://www.langchain.com/blog/how-to-think-about-agent-frameworks

## Before you publish — decisions to make

1. **Title**: current one is punchy; alternates: "Stop polishing prompts: a field guide to loop and graph engineering" / "I graded my own AI workflows. Most were engineered at the wrong layer."
2. **The 5-day hang claim**: verify your own log line before publishing (`grep "457438" ~/.pi/agent/logs/runtimes.log`) — it's your best anecdote, make sure you can defend it.
3. **How much of your setup to reveal**: the morning-brief/second-brain/trading examples are specific and credible; the trading one especially. Keep or genericize to taste.
4. **Moka attribution**: the piece leans on his taxonomy heavily — consider a one-line heads-up to him on Substack after publishing; good first-post etiquette and distribution.

## New material to consider weaving in (added 2026-08-13, from second research pass)

Strongest additions, in order of value to the article:

1. **"A loop is a single node in a graph"** (AI Builder Club [17]) — the sentence that ends the loops-vs-graphs flame war. You don't graduate from loops; you wrap them. Pairs perfectly with Moka's "rails and motor" line.
2. **The reviewer-node insight** [17]: the first edge to draw when promoting a loop to a graph is pulling *review* into a fresh context — a loop that reviews its own draft rubber-stamps it. This is a concrete, non-obvious claim your readers can act on, and it applies directly to your morning-brief example (it "verifies" its own output today, in the same context that wrote it).
3. **The 4-question gut check** [17]: split contexts? real fan-out/fan-in? control flow readable as a diagram? did the success bar change? Zero-to-one yes = a loop wearing a flowchart. Good as a sidebar box.
4. **The skeptic beat** [17]: the term is new, the practice isn't — LangGraph, AutoGen GraphFlow, Google ADK all shipped graph orchestration before July 2026. Paweł Huryn's "I call BS on graph engineering" + his deeper point (the discipline is naming the objective and the bar, whatever you draw). One paragraph of this makes the article honest instead of hypey, and it's a good look for a first post.
5. **Augment's team-level frame** [18]: trigger → execute → verify (human checkpoint placed by risk) → outcome → improve. Two quotable lines: "a loop that generates output nobody ships is not a successful loop" and "measure loops in outcomes per dollar, not output per dollar." Also Boris Cherny's "I don't prompt Claude anymore, I write loops."
6. **Context rot** as the motivation for graphs: a single loop carrying research + drafting + review in one context degrades as the window fills — the researcher's raw search dumps contaminate the reviewer. This is *why* graph nodes get fresh windows (and it's literally what OpenCode's Task tool does — new session per subagent [19]).

Suggested insertion points: 1+2 into the graph section; 3 as a boxed sidebar after the decision rule; 4 as a short "is this just a rebrand?" section before the conclusion; 5 into the conclusion; 6 into the intro/problem framing.
