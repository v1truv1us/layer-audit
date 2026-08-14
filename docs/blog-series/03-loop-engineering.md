# Post 3 — Loop engineering: stop writing prompts, start writing verifiers

**Thesis:** A loop is not a retry. The entire discipline is the exit condition — and it must be something the model can't fake.

**Length:** ~1,300 words. **Feeds from:** harness-mechanics.md, grounded-reference loop sections. **Sources:** [1, 2, 5, 6, 7, 8, 9, 17, 18, 20].

## Outline

1. **The Boris Cherny hook** — "I no longer prompt Claude. My job is to write loops." (June 30, 2026 [20], also cited in [18].) What he means: the human stops operating the cycle.
2. **The anatomy** — discover → plan → execute → verify [20]. Everyone writes the first three. The discipline lives in the fourth.
3. **The two-part stop condition** — binary success check + safety cap [1, 20]. Weak conditions ("make the code better") never exit; strong ones ("all 47 tests pass") are shell-testable.
4. **The three ways to build one in a CLI harness:**
   - **Stop hook** (Claude Code): exit 2 blocks, exit 1 is a placebo [5, 7, 8]. The `stop_hook_active` guard [7, 9]. The 8-block harness override [8].
   - **Shell wrapper** (any harness): the corrected verifier-loop script from harness-mechanics.md — verifier first, agent second, cap always.
   - **Native commands**: `/goal`, `/loop`, `/schedule`, and the combined proactive pattern [20] — with the caveat that you verified them yourself (checklist).
5. **The evaluator insight** — `/goal` reportedly checks the condition with a *separate model call* [20]: even Anthropic's own loop command refuses to let the author grade its own work.
6. **Worked example: morning-brief becomes a loop** — before (one `pi -p` call, 8% silent failure, 5-day hang) and after (verify output exists ≥ N bytes and has all five sections, retry ×3, emit telemetry). Show the actual diff.
7. **Closer** — "My loop now checks its own homework. But it still grades its own essay. That's post 4."

## Step-by-step: convert a scheduled prompt into a loop

1. **Write the verifier first.** One shell command that exits 0 only when done: `[ -s "$OUT_FILE" ] && grep -q "SECTION_FIVE" "$OUT_FILE"`. If you can't write this line, you don't have a loop candidate — you have a prompt.
2. **Wrap the call.** Verifier runs *before* the agent (don't burn tokens when already done), agent runs on failure, cap at 3 attempts:
   ```bash
   for i in 1 2 3; do
     check_done && exit 0
     claude -p "Output check failed: $(check_done 2>&1 | tail -5). Fix it." 
   done
   exit 1
   ```
3. **Test the failure path on purpose.** Delete the output file, run the wrapper, watch the agent get invoked. Then make the task impossible and confirm the cap fires. A loop you've never seen fail is a loop you haven't tested.
4. **(Claude Code) Alternative: Stop hook.** Register a `Stop` hook in settings.json: run verifier, exit 0 if green, exit 2 with reason on stderr if red. Add the `stop_hook_active` guard at the top — exit 0 if set.
5. **Add telemetry.** One log line per run: timestamp, attempts, verifier result. You'll want it for post 5.

## Pre-writing checklist

- [x] Confirm `/goal`, `/loop`, `/schedule` exist — **confirmed 2026-08-13**
- [ ] Watch one `/goal` run and confirm the evaluator call is a separate model invocation (transcript or debug log)
- [ ] Actually convert morning-brief to a verify-retry loop (the upgrade-workflow skill's first real job)
- [ ] Deliberately break a Stop hook with `exit 1` and watch it wave the turn through — the placebo is the post's best demo
- [ ] Test a deliberately-wedged loop against `stop_hook_active` and the 8-block cap
- [ ] Capture before/after telemetry lines from runs.jsonl

## What you learn writing this

Loops at the muscle-memory level: exit codes, guards, caps, and why the verifier is the whole game. After this post you will never ship another unverified scheduled prompt.
