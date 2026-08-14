# Post 9 — Give your slowest codebase a performance budget (a hands-on workshop)

**Thesis:** Performance work fails as a vague intention ("rainfocus needs perf work") and succeeds as a loop with a number. This post is the workshop: you bring a slow codebase, you leave with a benchmark, a budget, and a loop that defends it.

**Length:** ~1,600 words — the longest post, because it's a tutorial. **Sources:** [1, 3, 17, 18, 20] + `docs/performance-loops.md` + `docs/fast-verification.md`. **Format:** every step ends with a **checkpoint** — if you can't check it off, stop and fix before moving on.

## Step 0 — Pick ONE slow thing (not "performance")

"The codebase needs perf work" is not a task. A task sounds like: "the events dashboard takes 11 seconds to load" or "`npm run build` takes 6 minutes."

Do this:
1. List the 3 complaints you hear most (from users, from yourself, from your own waiting).
2. Pick the one with the highest **frequency × pain**. Not the most interesting one.
3. Write it as one sentence with a number you guessed: "X takes about N."

**Checkpoint:** you have exactly one sentence. If it says "and", split it and pick one half.

## Step 1 — Write the benchmark (the hardest step)

One command that reproduces the slow thing and prints a number. Rules:

- **Fast enough to run 3× in a loop** — a 6-minute build is measurable as-is; an 11-second page load is not measured by hand, it's measured by `curl -w '%{time_total}' -o /dev/null -s <url>` or a lighthouse CI run.
- **End-to-end, not micro.** Time the thing the user feels, not a function you suspect.
- **Same input every time.** Seed data, fixed route, fixed flag set. A benchmark that measures different work each run measures nothing.

Recipes by target (from `fast-verification.md`): endpoint → `oha -n 200 <url>`; page → `lighthouse <url> --output json | jq '.categories.performance.score'`; build → `hyperfine 'npm run build'`; bundle → `bundlesize`; script → `time`.

**Checkpoint:** `for i in 1 2 3; do <your command>; done` prints three numbers in the same ballpark. Ballpark = within 2×. If they're wildly apart, fix the benchmark, not the code.

## Step 2 — Freeze the correctness gate

The anti-Goodhart rule: any perf loop without a correctness gate will eventually make the number better by making the product worse. The gate must exist *before* the loop starts.

Do this:
1. Identify the command that proves the thing still works: `npm test`, `verify-fast.sh .`, a healthcheck, "the dashboard renders the events table."
2. Run it. If it's red, **fix that first** — a perf loop on a red baseline will hide breakage behind the noise.

**Checkpoint:** gate is green and runs in under a minute (use `verify-fast.sh` if the full suite is slow).

## Step 3 — Baseline, honestly

Do this:
1. Run the benchmark 3–5 times. Take the **median**, not the best.
2. Record the context: machine, branch, rough load. "11.2s median, M-series MBP, main @ abc123."
3. Put it somewhere durable — a file in the repo, the registry, a PR description. Baselines you don't write down get quietly moved.

**Checkpoint:** one median number, written down, with the commit hash next to it.

## Step 4 — Set the target (this is where most perf work dies)

Targets fail two ways: too vague ("make it faster") or too heroic ("10× or bust"). The workshop rule:

- **First loop: 30%.** Not 10×. A 30% cut is achievable by finding one or two real bottlenecks, which is exactly what the loop is for. Heroic targets push agents (and humans) into architecture rewrites that never land.
- **State it as a pair:** perf target AND correctness gate, in one sentence: *"median of 3 runs of `oha /api/events` under 3.5s, with `npm test` green."*
- **Per-iteration budget:** each loop iteration is one hypothesis. If the loop caps at 6 tries, you get 6 hypotheses — pick a target that 6 hypotheses can plausibly reach.

**Checkpoint:** you can say the goal out loud and it contains: metric, threshold, gate, cap. Four parts.

## Step 5 — Run the loop

The paste-ready form (post 3 has the full derivation):

```
/goal median of 3 runs of '<bench>' under <target> (baseline <median>) AND '<gate>' green, stop after 6 tries
```

Or the shell version from `perf-baseline.sh --project <name>` once the project is registered.

While it runs, the keep/revert discipline (from `fast-verification.md`): every iteration either beats the median or gets `git restore`d. No "it felt faster." No accumulating maybes.

**Checkpoint:** after the loop exits — pass or cap — you can list each hypothesis it tried and which ones survived. If you can't, you weren't watching the measurement, you were watching the agent.

## Step 6 — When one loop isn't enough: the graph

One endpoint, one loop. But rainfocus-shaped problems are usually N slow things: five endpoints, three pages, a build. That's the graph trigger (post 4's rule: fan out only where N>1 already exists).

The shape:
```
        ┌────────────┐  profile   ┌──────────┐  one fix   ┌──────────┐
        │ profiler   │───────────►│ fixer    │───────────►│ verifier │──► keep/revert
        │ (per target│            │ (fresh   │            │ (harness:│
        │  node,     │◄───────────│  context)│   reject   │  bench + │
        │  fan-out)  │            └──────────┘            │  gate)   │
        └────────────┘                                   └──────────┘
```

The profiler node runs per-target in parallel (5 endpoints = 5 branches), hands each fixer a profile + one hypothesis, and the verifier is harness code, not a model. The fixer never sees the profiler's raw dumps — context rot is why.

**Checkpoint:** you can name what crosses each edge (profile JSON → hypothesis → diff → verdict). If you can't, you're drawing boxes around a loop.

## Step 7 — Defend it

An improvement without a regression tripwire is a loan. Register the project (`registry.json` → `projects`) with its bench + gate + `max_duration_s`; the weekly audit then flags regressions forever. Perf becomes a defended property, not a one-time campaign.

**Checkpoint:** next Monday's audit shows rainfocus's row. From then on, getting slower is a found issue, not a discovered one.

## What to write about

The post writes itself from your artifacts: the sentence from step 0, the benchmark command, the baseline table, the target, the list of hypotheses the loop tried, the before/after medians, and (honestly) whether the 30% landed or the cap fired. Either outcome is a good post. "We capped out at 6 hypotheses and only found 12%" with the profile of why is more credible than a victory lap.

## Pre-writing checklist

- [ ] Complete steps 0–7 on rainfocus (or the closest repo you can touch)
- [ ] Save every artifact: baseline numbers, goal line, iteration log, final medians
- [ ] Record what the profiler said vs what the fix was — the gap between them is the most interesting paragraph
- [ ] Note the time cost honestly: setup hours vs saved seconds-per-day — readers will do this math
