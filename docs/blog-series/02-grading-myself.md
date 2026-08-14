# Post 2 — I graded my own AI workflows. Most were at the wrong layer.

**Thesis:** A decision rubric is only worth anything if you'll apply it to yourself. Here's mine applied to my 23 workflows, with the embarrassing results.

**Length:** ~1,100 words. **Feeds from:** docs/classification-2026-08-12.md, issues-*.md. **Sources:** [1, 3, 17].

## Outline

1. **The rubric on an index card** — prompt when one call does it and a human reads it; loop when repeated trigger + scriptable done-condition + varying path; graph only for parallel branches / mid-run approval / resume-after-crash; otherwise fix the harness [1, 3].
2. **The inventory** — "I run ~23 agent workflows: scheduled briefs, CI watchers, a knowledge pipeline, a trading job." A table readers can skim.
3. **The findings, worst first:**
   - morning-brief: daily prompt, 8% failure, zero verification, and one run that reported "OK" after hanging **five days** (457,438 seconds — the log line is the post's hero image)
   - second-brain: 7 cron jobs time-ordered by guesswork — 03:00, 03:05, 03:15 — a graph pretending to be a schedule
   - ralph-wiggum: a routing table written in prose — a graph wearing a loop's clothes
   - The correctly-layered ones, briefly: it wasn't all broken
4. **What the rubric caught that vibes wouldn't** — the jobs that *feel* fine because they usually work (silent failures are invisible without checking output files).
5. **The gut check box** — the 4 questions from [17] as a sidebar; admit which of your "graphs" fail it.
6. **Closer** — "The fix list wrote itself. Next: loops, starting with the five-day hang."

## Step-by-step: grade your own workflows in 30 minutes

1. **Inventory (10 min).** Run `crontab -l`, `ls ~/Library/LaunchAgents`, and list your skills/commands directories (`ls ~/.claude/skills ~/.config/opencode/skills`). Anything triggered more than twice is a workflow. Write the list.
2. **Check for silent failures (10 min).** For each scheduled job, find its output from the last run. Missing file, zero bytes, or suspiciously tiny = it "succeeded" at producing nothing. This is the step that finds the bodies.
3. **Check for hangs (5 min).** Grep your logs for absurd durations: any run 10× longer than the median is a hang your trigger swallowed.
4. **Apply the rubric (5 min).** For each workflow, one line: repeated trigger? scriptable done-condition? needs parallel/approval/resume? That maps it to prompt / loop / graph / harness-fix.
5. **Rank by frequency × pain.** A daily job failing 10% beats a weekly job failing 50%. That ranking is your work queue — you didn't decide anything; the numbers did.

## Pre-writing checklist

- [ ] Verify the 457438s log line: `grep 457438 ~/.pi/agent/logs/runtimes.log`
- [ ] Re-run `python3 audit.py` and screenshot the real issues table
- [ ] Count your actual workflows from registry.json — don't round
- [ ] Run the gut check on ralph-wiggum honestly and write down the score

## What you learn writing this

Ruthless self-application. Anyone can grade workflows in the abstract; you'll have graded yours, with numbers, in public. Also: silent-failure detection as a concept — most readers have never checked whether their "successful" automations produced anything.
