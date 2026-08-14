# Fast verification and AI bottleneck hunting

Two rules that multiply each other:

1. **Loops are only as good as their verifier is fast.** A loop whose check takes 10 minutes gets 6 iterations an hour; one whose check takes 10 seconds gets 360. Verification speed is the ceiling on loop quality (Augment: "the bottleneck moved to verification" [18]).
2. **Performance work is the highest-value loop target** — and it comes in exactly two flavors: make it **faster**, or make it **smaller**.

## Part 1: Make verification fast

Layer the gates:

| Gate | Runs | Cost | Catches |
|------|------|------|---------|
| Fast gate — affected tests only | every loop iteration | seconds | 90% of regressions |
| Slow gate — full suite + build | loop exit / before merge | minutes | integration breakage |

`scripts/verify-fast.sh` is the fast gate: maps changed files to affected tests by convention (`.test.ts`, `__tests__/`, `test_*.py`, `*_test.go`), runs just those, falls back to the full suite when mapping fails. Supports bun, vitest/jest, pytest, go, cargo, npm.

```bash
verify-fast.sh ~/Github/my-repo          # affected tests vs origin/main
verify-fast.sh ~/Github/my-repo HEAD~5   # affected tests vs a specific ref
```

Other fast-gate tricks: `pytest -x` (stop at first failure), `bun test --bail`, typecheck only (`tsc --noEmit` is seconds vs a full build), lint only changed files (`eslint $(git diff --name-only)`).

## Part 2: The bottleneck-hunting loop

The agent is the *analyst*; the harness owns the *measurement*. Same loop shape for both axes:

```
1. MEASURE   — harness runs the benchmark/profiler, captures a number
2. HYPOTHESIZE — agent reads the profile/output, names ONE bottleneck
3. FIX       — agent makes ONE change
4. RE-MEASURE — harness re-runs, median of 3
5. KEEP or REVERT — better → git commit; not better → git restore. No exceptions.
```

The keep/revert discipline is the whole game. A perf loop without revert-on-no-improvement accumulates changes that *felt* right and made nothing faster.

### Axis A: faster

| Target | Measure with | Loop goal example |
|--------|-------------|-------------------|
| Script/job runtime | `time`, `hyperfine` | `/goal hyperfine median of workflow.sh under 2s, tests green, stop after 8 tries` |
| API/endpoint latency | `oha`, `wrk`, autocannon | `/goal p95 of /api/search under 200ms (oha -n 500), tests green` |
| Node hot path | `node --cpu-prof`, clinic.js | `/goal flamegraph shows no frame >30% self-time outside vendor` |
| Python hot path | `py-spy record`, cProfile | same shape |
| Go hot path | `go test -bench -benchmem` | `/goal BenchmarkParse allocs/op under 50` |

### Axis B: smaller

| Target | Measure with | Loop goal example |
|--------|-------------|-------------------|
| JS bundle | `bundlesize`, source-map-explorer | `/goal main bundle under 250KB per bundlesize, tests green` |
| Dependency tree | `depcheck`, `npm ls --all` count | `/goal node_modules under 180MB, app boots` |
| Docker image | `docker images`, `dive` | `/goal image under 200MB, container healthcheck passes` |
| Binary | `bloaty`, `ls -la` | `/goal release binary under 15MB, smoke test passes` |
| Repo/workspace | `du -sh`, `git count-objects -vH` | `/goal repo under 500MB, clone+build passes` |

### Anti-Goodhart pairings (both axes, always)

- Faster **AND** tests green — or the agent deletes the slow tests.
- Smaller **AND** app boots/builds — or the agent tree-shakes the entrypoint.
- Median of 3 **AND** measured by the harness — or the loop exits on one lucky/cache-warm run.

## Where this feeds the blog series

Post 3 gains the "verification speed is the loop multiplier" section + the layered-gates table. Post 5's step-by-step references `verify-fast.sh` as the fast gate. The keep/revert discipline is a standalone section anywhere — it's the least-known, highest-value practice here.
