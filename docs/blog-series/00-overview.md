# Blog series: Agentic Engineering, learned in public

Eight posts in two arcs. Each is standalone-valuable, builds on the previous, and has a **pre-writing checklist** — things you must build or verify before publishing that post. The checklists are the learning mechanism: you can't write post 3 until you've run a real loop, and you can't write post 4 until you've drawn one real edge.

Every post 2+ contains a **numbered step-by-step** the reader can follow on their own machine. No post is pure essay.

`docs/blog-draft.md` is the raw monolith — most of it feeds posts 1–2. Cannibalize freely.

## Arc 1: The framework, applied to my own machine

| # | Working title | Layer | Your proof |
|---|---------------|-------|-----------|
| 1 | Your agent isn't dumb, it's under-engineered | All 5 (survey) | The misdiagnosis story |
| 2 | I graded my own AI workflows. Most were at the wrong layer | The rubric | 23 workflows classified |
| 3 | Loop engineering: stop writing prompts, start writing verifiers | Loop | morning-brief, converted |
| 4 | Graph engineering: a loop is a single node in a graph | Graph | second-brain chain, rewired |
| 5 | I built a system that tells me what to automate next | Meta | layer-audit itself |

## Arc 2: The harness field guides (same task, three harnesses)

The comparative trick: **build the same verifier loop and the same two-node graph in all three harnesses**, then report. Not "which AI CLI is best" (slop) — "here is exactly what loop and graph engineering costs in each."

| # | Working title | Angle |
|---|---------------|-------|
| 6 | Loop and graph engineering in Claude Code | Hooks, /goal, Agent SDK — the most engineered surface |
| 7 | Loop and graph engineering in OpenCode | Plugins, SDK, child sessions — the most hackable surface |
| 8 | Loop and graph engineering in Pi | Extensions, headless `pi -p`, launchd — the smallest surface |

## Arc 3: The capstone workshop

| # | Working title | Angle |
|---|---------------|-------|
| 9 | Give your slowest codebase a performance budget | Hands-on tutorial: rainfocus, from "needs perf work" to defended budget |

## Series rules

1. **One claim per post, proven with your own machine.** Every post has a personal artifact: a log line, a before/after, a score table. This is what separates it from the 10,000-word slop the skeptics [17] predicted.
2. **Publish in order; the checklists gate you.** If a checklist item fails, that's the post — "I tried X and it broke" is better material than success.
3. **Every tutorial step-by-step is tested by you first.** If a reader follows your steps and hits a wall you didn't, the series dies. The checklists exist to prevent this.
4. **Each post links back to the series index and forward to the next.** Post 5 closes arc 1; posts 6–8 stand alone but assume arc 1 vocabulary.
5. **Voice: practitioner, first person, short paragraphs.** Show commands and log excerpts. No "in today's fast-paced world."

## Sources key

Bracketed numbers refer to `docs/grounded-reference.md`'s reference list. Per-post source assignments are in each outline.
