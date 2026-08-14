# Performance-goal loops: verifiers that measure, not vibes

"Make the tests pass" is a weak loop goal because it's already binary. "Improve performance" is a weak goal because it isn't. A performance-goal loop turns the second into the shape of the first: **a metric, a baseline, a target, and a measurement the agent doesn't control.**

## The anatomy

```
/goal <metric> <direction> <threshold> as measured by <external command>, stop after N tries
```

Examples that are actually loopable:

```
/goal median of 3 runs of bench.sh under 120s, stop after 8 tries
/goal lighthouse performance score ≥ 90 on /pricing, stop after 6 tries
/goal bundle size under 250KB per bundlesize CLI, stop after 5 tries
/goal morning-brief median duration back under 300s, stop after 5 tries
```

Weak versions that will never exit or will exit on noise:

```
/goal make it faster              ← no metric
/goal reduce runtime              ← no threshold
/goal get runtime under 120s      ← measured once; one lucky run exits the loop
```

## The five rules

1. **The harness measures, never the agent.** The benchmark command runs outside the model's hands (wrapper script, Stop hook, `/goal` evaluator). If the agent can run the benchmark, it can learn to run it selectively.
2. **Median of N, not a single run.** Machine load, model latency, and cache state make single timings noise. `for i in 1 2 3; do time cmd; done | median`. A loop that exits on one fast run exits on luck.
3. **Baseline first, target relative.** Record the current median before the loop starts ("from 312s, target 200s"). Absolute targets invented without a baseline produce loops that cap out immediately.
4. **Guard the guardrails.** Performance loops invite Goodharting: the agent can get faster by deleting tests, caching outputs, or weakening the very verifier. Pair every perf goal with a correctness gate that must stay green (`tests pass AND bench < X`). Both conditions in the same stop check.
5. **Cap by budget, not just iterations.** A perf loop that re-runs a benchmark 3× per iteration burns 3× the tokens. Iteration cap × benchmark cost = the real price of the goal; write it down before starting.

## The regression side (detection, not goals)

Goals improve; regression detection protects. The audit now does both halves of this:

- **`max_duration_s` per workflow** in `registry.json` → `performance-target-breach` issue when the 7-day median exceeds it.
- **Week-over-week median comparison** → `performance-regression` issue when recent runs are >50% slower than the baseline window.
- **Hung-run detection** → `hung-runs` issue when ≥10% of runs exceed 1h (the morning-brief case: a 5-day hang reporting OK).

Bisect order when a regression fires: model route first (did pick-model shift tiers?), then context size (did the prompt or retrieved data grow?), then tool latency (did an API get slow?).

## Where this feeds the blog series

Post 3 gets a section: "the strongest goal conditions are performance budgets" — with the anti-Goodhart pairing (correctness gate AND perf gate) as the non-obvious takeaway. The hung-runs proposal the audit generated on real data (5-day hang, 17% hang rate) is the worked example.
