# Post 4 — Graph engineering: a loop is a single node in a graph

**Thesis:** Graphs aren't the next hype layer to graduate to — they're what you draw when one loop strains, and the first edge to draw is always the reviewer.

**Length:** ~1,400 words. **Feeds from:** grounded-reference graph sections, harness-mechanics.md. **Sources:** [1, 3, 4, 10, 11, 12, 13, 14, 17, 19, 20].

## Outline

1. **The hype cycle beat** — July 2026: "loop engineering is dead, long live graph engineering," and the state-machine people calling it slop, same week [17]. Both overheated.
2. **The sentence that settles it** — a loop is a single node in a graph. You don't graduate; you wrap [17, 20].
3. **Context rot: the actual problem graphs solve** — one agent that researches, drafts, AND reviews in one window rubber-stamps its own work; the reviewer's context is contaminated by the author's [17]. OpenCode's Task tool shows the fix at the machine level: a subagent is a *new session* with a clean window [19].
4. **The three genuinely new capabilities** — parallel specialized nodes, explicit auditable control flow, fan-out/fan-in [17]. And the costs: more prompts, a state schema between nodes, new silent failure modes (the merge that drops a field).
5. **The migration path** — keep the loop as node one; split off the reviewer first; write down what crosses the edge; fan out only where N>1 already exists; stop when the next node stops paying [17].
6. **The honest rebrand section** — LangGraph, AutoGen GraphFlow, Google ADK all predate the term [17]. Huryn's "I call BS" + his real point: the discipline (name the objective and the bar) doesn't change with the drawing [17].
7. **Worked example: the second-brain cron chain becomes a graph** — 7 jobs at 03:00/03:05/03:15 (time-guessed dependencies) rewired as explicit edges with checkpointing; independent stages parallelized. Show the before crontab and the after diagram. Bonus: your `dynamic-workflow.ts` as the runtime.
8. **The gut check as closer** — the 4 questions [17], applied to the graph you just built, honestly scored.

## Step-by-step: promote one loop to a two-node graph

1. **Pick the failing step inside your loop.** Almost always the reviewer — the loop checking its own work in the same context that did the work.
2. **Write the state schema.** One sentence: "node one hands node two `<X>`." (e.g. "the draft file path + the acceptance criteria"). If you can't name what crosses the edge, stop here — you're not ready to split.
3. **Split it.** Node two runs in a *fresh* context: a new headless call, a subagent, a child session — never a continuation of node one's transcript. Node two sees only the artifact + the bar, not the reasoning that produced it.
4. **Route on the verdict in code.** `if reviewer_verdict == "fail": re-run node one with the critique`. The `if` lives in your shell/python, not in the model's instructions.
5. **Checkpoint between nodes.** Write state to a file after each node so a crash resumes mid-graph instead of restarting.
6. **Fan out only if N>1.** If node one iterates over N things one at a time (7 client sites, 10 sources), that's your first parallel branch. Otherwise skip it — a sequence drawn as boxes is not a graph.
7. **Score yourself with the gut check.** Four questions, count the yeses. Two or fewer and you built a loop with extra steps — say so in the post.

## Pre-writing checklist

- [ ] Build one real edge: pull verification of some workflow into a separate fresh-context step and measure whether it catches what the self-review missed
- [ ] Rewire at least two second-brain stages with an explicit dependency instead of a time guess
- [ ] Run `opencode-agent-teams` [12] or your own dynamic-workflow.ts on a real task so you can speak to fan-out from experience
- [ ] Read one skeptic in full (Huryn thread via [17]) and be able to steelman it
- [ ] Check whether Masterclass Part 2 (agent teams, due Aug 17 [20]) shipped; cite if yes

## What you learn writing this

Graphs by construction, not by diagram. You'll know where state should live, why the schema between nodes is the hard part, and when a graph is just a loop wearing a flowchart — because you'll have built both.
