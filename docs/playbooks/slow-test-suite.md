# Playbook: the 20-minute test suite

Instantiates `docs/blog-series/09-perf-workshop.md` for one specific target: a full test suite that takes 20+ minutes. Fill in the blanks as you go — this file is the worksheet. Every step has a **Why** with references; bracketed numbers point at `docs/grounded-reference.md`.

**Target codebase:** ____________ (path)
**Suite:** ☐ frontend ☐ backend ☐ e2e ☐ combined
**Framework:** ____________ (jest / vitest / bun / pytest / go / playwright)

---

## Step 0 — The sentence

> "The ____________ suite takes ~____ minutes to run, and it runs ____ times per day per developer."

**Why:** "improve performance" is an unbounded intention; a loop needs one binary, measurable condition or it can never exit [1, 20]. Frequency × pain is the ranking function — a daily 20-minute suite beats a weekly 40-minute one even though it's "smaller," because the loop's payoff multiplies by how often the verifier runs [18].

Checkpoint: one sentence, one number, no "and".

## Step 1 — Benchmark

Suite timing is free — the suite *is* the benchmark. Make it explicit:

```bash
hyperfine --runs 3 'npm test'            # or: bun test / pytest / npx playwright test
```

Also capture the breakdown NOW (this decides your hypotheses later):

```bash
npx jest --verbose 2>&1 | tail -30       # per-suite times at the bottom
pytest --durations=20                     # slowest 20 tests
npx playwright test --reporter=line      # then check shard/test timings
```

Record:

| Run | Wall time |
|-----|-----------|
| 1 | |
| 2 | |
| 3 | |
| **median** | |

Where the time goes: setup/fixtures ____% · test execution ____% · I/O wait ____% · unknown ____%

**Why median, not best:** machine load and cache state make single timings noise; a loop that exits on one fast run exits on luck, and you've shipped a placebo improvement (rules 2–3 in `docs/performance-loops.md`). **Why the breakdown first:** the harness measures, the agent hypothesizes — but hypotheses are only as good as the profile. Without the breakdown, the loop burns its 6 iterations guessing [17: the state handed between nodes is where the work lives].

Checkpoint: median written down + a rough breakdown. If "unknown 80%", profile before continuing — don't guess.

## Step 2 — The gate (anti-Goodhart)

For a test-suite perf loop, the gate is not "tests pass" — that's the bench. The gate is:

> **Same number of tests, same or better coverage, all passing.**

```bash
npm test 2>&1 | grep -E "Tests:|Suites:"     # jest/vitest counts
# coverage if you have it: npm run coverage | grep "All files"
```

Baseline counts: tests ____ · suites ____ · coverage ____%

**Why:** Goodhart's law — "when a measure becomes a target, it ceases to be a good measure" (Goodhart 1975 on monetary policy; generalized by Hoskin 1996; Strathern's 1997 formulation [21]). An agent told "make the suite faster" is under exactly this pressure: the cheapest way to hit a duration target is to reduce the work — delete slow tests, skip setups, weaken assertions. That isn't speculation about malice; it's what any optimizer does to an unguarded metric. The paired gate (count + coverage + green) keeps the measure honest by pinning what the measure is *for*: the suite's job is catching bugs, so the gate measures bug-catching while the bench measures speed. This is the general pattern from `docs/performance-loops.md`: every performance goal ships with a correctness condition in the same stop check, or the loop will eventually trade the thing you care about for the number you asked for [18: loops must be accountable for outcomes, not output].

Checkpoint: counts written down. The loop goal will include them verbatim.

## Step 3 — Decide: bypass first, or optimize first

**Bypass (do this first, ~30 min):** the full suite stops running on every iteration; affected tests run instead.

```bash
~/Github/layer-audit/scripts/verify-fast.sh /path/to/repo     # test it now
```

**Why bypass first:** verification speed is the ceiling on loop quality — a loop whose check takes 20 minutes gets a handful of iterations a day; one whose check takes 20 seconds gets hundreds [18]. Most of the suite's cost is paid in *repeated* runs, and selection removes the repetition without touching the suite. Optimizing first means spending the loop's expensive iterations on a cost you could have mostly deleted for free. (Anthropic's evaluator-optimizer pattern makes the same point structurally: the evaluator must be cheap enough to run every cycle [3].)

If the fast gate covers your daily loop, the 20-minute suite only gates merges. Is the full-suite time still painful (merge queue waits, CI minutes cost)? ☐ yes → continue. ☐ no → done; register and stop (step 6).

## Step 4 — The structural wins menu (in rough order of payoff)

| Hypothesis | Typical payoff | Effort | Watch out for |
|------------|---------------|--------|---------------|
| Parallelize / shard (jest `--maxWorkers`, playwright `shard`, pytest-xdist) | 30-60% | low | flaky tests under parallel load; shared-state tests collide |
| e2e sharding across CI runners | 50-80% of e2e | low-med | needs CI matrix change |
| Shared/expensive fixtures → setup once per worker not per test | 20-50% | med | fixture pollution between tests |
| Delete or quarantine dead/snapshot-spam tests | varies | low | this is why the gate counts tests |
| Cache transforms/build artifacts between runs (jest cache, turbo) | 10-30% | low | stale-cache bugs |
| Replace heavy rendering (jsdom → happy-dom; real browser → component tests) | 20-40% | med | behavior differences |

**Why structural first:** the suite is a system, and system-level wins (parallelism, caching, dedup of setup) dwarf code-level wins (optimizing individual tests) by an order of magnitude. This is the same reason the harness layer beats the prompt layer [1]: you get more from changing the machinery than from polishing what runs inside it. The step-1 breakdown tells you which row of this table to start from — I/O-heavy suites want fixtures and caching; CPU-heavy suites want parallelism.

Pick THREE as the loop's initial hypotheses, in order: 1. ____________ 2. ____________ 3. ____________

## Step 5 — The loop

```
/goal median of 3 runs of '<suite command>' under <target> (baseline <median>) AND test count = <N> and coverage >= <C>% and all passing, stop after 6 tries
```

My goal line:

> ____________________________________________________________

Keep/revert per iteration: beat the median or `git restore .` No maybes.

**Why 30%-style targets and a 6-try cap:** heroic targets push the agent into rewrites that never land; a capped loop with a modest target finds the one or two structural wins that actually exist (targets rule, `docs/performance-loops.md`). The cap is budget protection — an agent that can't find the win will happily burn tokens looking [20]. **Why keep/revert is absolute:** without revert-on-no-improvement, the loop accumulates changes that *felt* right, the suite gets weird and not faster, and you've lost the baseline you needed to measure against. One hypothesis per iteration is what makes the keep/revert decision legible [17].

Iteration log:

| # | Hypothesis | Median after | Keep? |
|---|-----------|--------------|-------|
| 1 | | | ☐ |
| 2 | | | ☐ |
| 3 | | | ☐ |
| 4 | | | ☐ |
| 5 | | | ☐ |
| 6 | | | ☐ |

## Step 6 — Register and defend

In `~/Github/layer-audit/registry.json` → `projects`:

```json
"<repo-name>": {
  "path": "~/path/to/repo",
  "bench": "<suite command>",
  "correctness": "<suite command> (count=N, coverage>=C%)",
  "metric": "duration_s",
  "max_duration_s": <target in seconds>
}
```

Then `~/Github/layer-audit/scripts/perf-baseline.sh --project <repo-name>` confirms it end-to-end.

**Why register:** an undefended improvement is a loan. Suites re-slow the week after the push — new tests, new fixtures, someone bumps a dependency — and without a tripwire you discover it the same way you did this time: by noticing you're waiting. The audit's `performance-regression` and `performance-target-breach` signals turn "the suite got slow again" from a vibes-discovery into a found issue with a number attached. This is the improve-stage of the loop from [18]: each run's trace feeds back into the system.

## Expected outcome

Honest range for a first pass on a 20-min suite: **20 → 8-12 min** from one structural win, plus the fast gate making the remaining time mostly invisible day-to-day. If the loop caps without landing, the iteration log + breakdown from step 1 is the post/follow-up material.
