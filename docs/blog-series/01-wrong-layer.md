# Post 1 — Your agent isn't dumb, it's under-engineered

**Thesis:** Every "my agent is being dumb" complaint is a misdiagnosis. The model is fine; you engineered the wrong layer.

**Length:** ~900 words. **Feeds from:** blog-draft.md intro + five-layers sections. **Sources:** [1, 2, 3, 4, 15, 16].

## Outline

1. **Cold open** — a concrete misdiagnosis from your own experience. Candidate: polishing morning-brief's prompt for weeks while the real problem was zero verification. One paragraph, no throat-clearing.
2. **The five layers, one sentence each** — prompt (one call), context (one window), harness (one run), loop (one goal), graph (the whole workflow). Moka's zoom-out timeline: 2024 prompt → 2025 context → 2026 harness/loop/graph. Nothing died; the prompt is just the smallest part now [1].
3. **The Anthropic fork** — workflow vs agent: who owns the control flow [3]. Graph ≈ workflow, loop ≈ agent-with-a-stop. Both camps land on "simplest thing that works."
4. **The layer diagnostic** — Moka's failure table [1]: output format wrong → prompt; forgets facts → context; flaky tools → harness; never stops → loop; can't pause/parallelize → graph. This is the table readers will screenshot.
5. **Why this matters now** — harness moved the same model from top-30 to top-5 on Terminal Bench [1]. The leverage moved outside the prompt.
6. **Closer** — "Next: I turned this table on my own machine. The results were embarrassing."

## Pre-writing checklist

- [ ] Re-read [1] and [3] end to end; be able to state the workflow/agent fork without notes
- [ ] Pick your cold-open anecdote and verify it against logs
- [ ] Write the layer-diagnostic table from memory, then correct against [1]
- [ ] Decide series name + where it lives (Substack? personal site?)

## What you learn writing this

The taxonomy cold — you'll be able to place any workflow complaint on a layer in seconds, which is the skill every later post depends on.
