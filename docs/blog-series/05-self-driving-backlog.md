# Post 5 — I built a system that tells me what to automate next

**Thesis:** The meta-move: stop deciding which workflows to upgrade. Instrument everything, let a deterministic audit rank the pain, and approve upgrades from a queue.

**Length:** ~1,200 words. **Feeds from:** README.md, audit.py, registry.json, real issues/proposals data. **Sources:** [1, 3, 18] + your own repo.

## Outline

1. **The problem with posts 1–4** — they all required me to *decide what to look at*. That's the part I'm worst at. So the last step was removing myself from triage.
2. **The architecture in one diagram** — every scheduled job and loop emits one JSONL line per run → a deterministic Python audit scores 30 days of signals → ranked issues file → proposals in a folder → I move a file to `approved/` → a builder skill implements it. (Your README diagram, simplified.)
3. **Why the audit is deterministic code, not an LLM** — ranking is arithmetic (failure rates × frequencies × weights); an LLM drafting its own queue would recreate the silent-failure problem the system exists to catch. Rule: code for determinism, models for judgment.
4. **The signals** — fail rate, silent-failure rate (exit 0, empty output), cap rate (loops not converging), repeat-error signatures, unverified runs. Show the real formula and the real first-week table.
5. **What it found** — the actual results: morning-brief's stats, which workflows had no telemetry at all, what the first proposals were. Numbers from your own issues/ files.
6. **The filesystem-as-queue** — pending/approved/rejected/done. No dashboard, no database. Approval is `mv`. This is the design decision readers will steal.
7. **The honest limits** — silent-failure heuristics false-positive; cap_rate needs weeks of data; it can't tell you a workflow is *pointless*, only that it's *failing*. The audit finds broken layers, not bad ideas.
8. **Closer** — the loop closed on the series itself: the system that grades the workflows is itself registered in the registry, and its own audit row appears in the table. "Outcomes per dollar, not output per dollar" [18].

## Pre-writing checklist

- [ ] Let the system run for 2+ real weeks so the numbers in section 5 are earned, not seeded
- [ ] Approve and build at least one real proposal end-to-end (post 3's morning-brief counts)
- [ ] Run the Monday job once via launchd and capture the log line
- [ ] Write the honest-limits section from actual false positives you hit
- [ ] Decide what to open-source: the repo is private; the post will drive readers to ask for it

## What you learn writing this

Systems thinking applied to your own tooling: instrumentation before optimization, deterministic ranking before judgment, and queue design (approval as a file move). This is the post that turns the series from "I read some articles" into "I run an engineered system."
