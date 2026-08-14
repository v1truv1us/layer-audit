# Playbook: the 20-minute test suite

Instantiates `docs/blog-series/09-perf-workshop.md` for one specific target: a full test suite that takes 20+ minutes. Fill in the blanks as you go — this file is the worksheet.

**Target codebase:** ____________ (path)
**Suite:** ☐ frontend ☐ backend ☐ e2e ☐ combined
**Framework:** ____________ (jest / vitest / bun / pytest / go / playwright)

---

## Step 0 — The sentence

> "The ____________ suite takes ~____ minutes to run, and it runs ____ times per day per developer."

Checkpoint: one sentence, one number, no "and".

## Step 1 — Benchmark

Suite timing is free — the suite *is* the benchmark. Make it explicit:

```bash
# pick yours
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

Where the time goes (from the breakdown): setup/fixtures ____% · test execution ____% · I/O wait ____% · unknown ____%

Checkpoint: median written down + a rough breakdown. If the breakdown says "unknown 80%", profile before continuing — don't guess.

## Step 2 — The gate (anti-Goodhart)

For a test-suite perf loop, the gate is not "tests pass" — that's the bench. The gate is:

> **Same number of tests, same or better coverage, all passing.**

```bash
# capture before the loop starts:
npm test 2>&1 | grep -E "Tests:|Suites:"     # jest/vitest counts
# coverage if you have it: npm run coverage | grep "All files"
```

Baseline counts: tests ____ · suites ____ · coverage ____%

Checkpoint: you have the counts written down. The loop goal will include them.

## Step 3 — Decide: bypass first, or optimize first

**Bypass (do this first, ~30 min):** the full suite stops running on every iteration; affected tests run instead.

```bash
~/Github/layer-audit/scripts/verify-fast.sh /path/to/repo     # test it now
```

If the fast gate covers your daily loop, the 20-minute suite only gates merges — and the pressure drops enough to choose the optimization calmly. **Do the bypass regardless.** Then answer: is the full-suite time still painful (merge queue waits, CI minutes cost)? ☐ yes → continue. ☐ no → done; register and stop (step 6).

## Step 4 — The structural wins menu (in rough order of payoff)

| Hypothesis | Typical payoff | Effort | Watch out for |
|------------|---------------|--------|---------------|
| Parallelize / shard (jest `--maxWorkers`, playwright `shard`, pytest-xdist) | 30-60% | low | flaky tests under parallel load; shared-state tests collide |
| e2e sharding across CI runners | 50-80% of e2e | low-med | needs CI matrix change |
| Shared/expensive fixtures → setup once per worker not per test | 20-50% | med | fixture pollution between tests |
| Delete or quarantine dead/snapshot-spam tests | varies | low | this is why the gate counts tests |
| Cache transforms/build artifacts between runs (jest cache, turbo) | 10-30% | low | stale-cache bugs |
| Replace heavy rendering (jsdom → happy-dom; real browser → component tests) | 20-40% | med | behavior differences |

Pick THREE as the loop's initial hypotheses, in order: 1. ____________ 2. ____________ 3. ____________

## Step 5 — The loop

```
/goal median of 3 runs of '<suite command>' under <target> (baseline <median>) AND test count = <N> and coverage >= <C>% and all passing, stop after 6 tries
```

My goal line: 

> ____________________________________________________________

Keep/revert per iteration: beat the median or `git restore .` No maybes.

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

Then `~/Github/layer-audit/scripts/perf-baseline.sh --project <repo-name>` confirms it end-to-end, and the Monday audit flags regressions from now on.

## Expected outcome

Honest range for a first pass on a 20-min suite: **20 → 8-12 min** from one structural win, plus the fast gate making the remaining time mostly invisible day-to-day. If the loop caps without landing, the iteration log + breakdown from step 1 is the post/follow-up material.
