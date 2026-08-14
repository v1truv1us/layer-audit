#!/usr/bin/env python3
"""Layer audit: rank workflow issues across the prompt/loop/graph taxonomy.

Deterministic. Reads:
  - ~/.pi/agent/logs/runtimes.log          (legacy backfill, START/OK/FAIL/SKIP)
  - ~/.pi/agent/telemetry/runs.jsonl       (schema-2 emitter records)
Writes:
  - <repo>/issues/issues-YYYY-MM-DD.md
  - <repo>/proposals/pending/<id>.md

Repo root defaults to the script's parent dir; override with LAYER_AUDIT_HOME.
"""

import fnmatch
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
PI_DIR = Path(os.environ.get("PI_CODING_AGENT_DIR", HOME / ".pi" / "agent"))
AUDIT_DIR = Path(os.environ.get("LAYER_AUDIT_HOME", Path(__file__).resolve().parent))
REGISTRY_PATH = AUDIT_DIR / "registry.json"
RUNTIMES_LOG = PI_DIR / "logs" / "runtimes.log"
RUNS_JSONL = AUDIT_DIR / "telemetry" / "runs.jsonl"
WINDOW_DAYS = 30

RE_START = re.compile(r"^\[([^\]]+)\] START (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
RE_OK = re.compile(r"^\[([^\]]+)\] OK after (\d+)s at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
RE_FAIL = re.compile(r"^\[([^\]]+)\] FAIL exit=(\d+) after (\d+)s at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
RE_SKIP = re.compile(r"^\[([^\]]+)\] SKIP at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
TS_FMT = "%Y-%m-%d %H:%M:%S"


def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def parse_ts(s):
    return int(datetime.strptime(s, TS_FMT).timestamp())


def backfill_runtimes_log():
    """Pair START with the next OK/FAIL per workflow. Leftover STARTs = crash."""
    if not RUNTIMES_LOG.exists():
        return []
    lines = RUNTIMES_LOG.read_text(errors="replace").splitlines()
    events = []
    for line in lines:
        for kind, rx in (("start", RE_START), ("ok", RE_OK), ("fail", RE_FAIL), ("skip", RE_SKIP)):
            m = rx.match(line)
            if m:
                events.append((kind, m))
                break
    runs = []
    pending = {}
    for kind, m in events:
        name = m.group(1)
        if kind == "start":
            pending[name] = parse_ts(m.group(2))
        elif kind == "ok":
            runs.append({
                "workflow": name, "ts_start": pending.pop(name, parse_ts(m.group(3)) - int(m.group(2))),
                "duration_s": int(m.group(2)), "outcome": "success", "stop_reason": "done",
                "iterations": 1, "verified": False, "error_sig": None, "source": "runtimes.log",
            })
        elif kind == "fail":
            runs.append({
                "workflow": name, "ts_start": pending.pop(name, parse_ts(m.group(4)) - int(m.group(3))),
                "duration_s": int(m.group(3)), "outcome": "failure", "stop_reason": "error",
                "iterations": 1, "verified": False, "error_sig": f"exit{m.group(2)}", "source": "runtimes.log",
            })
        elif kind == "skip":
            runs.append({
                "workflow": name, "ts_start": parse_ts(m.group(2)), "duration_s": 0,
                "outcome": "unknown", "stop_reason": "skip", "iterations": 0,
                "verified": False, "error_sig": None, "source": "runtimes.log",
            })
    for name, ts in pending.items():
        runs.append({
            "workflow": name, "ts_start": ts, "duration_s": None, "outcome": "unknown",
            "stop_reason": "crash", "iterations": None, "verified": False, "error_sig": None,
            "source": "runtimes.log",
        })
    return runs


def load_emitter_runs():
    if not RUNS_JSONL.exists():
        return []
    runs = []
    for line in RUNS_JSONL.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        rec["source"] = "runs.jsonl"
        runs.append(rec)
    return runs


def dedupe(runs):
    """Prefer emitter records over backfill when they overlap (same workflow, ts within 120s)."""
    emitter = [r for r in runs if r["source"] == "runs.jsonl"]
    legacy = [r for r in runs if r["source"] != "runs.jsonl"]
    emitter_keys = {(r["workflow"], r["ts_start"] // 120) for r in emitter if r.get("ts_start")}
    kept = [r for r in legacy if (r["workflow"], r["ts_start"] // 120) not in emitter_keys]
    return emitter + kept


def resolve_alias(name, workflows):
    if name in workflows:
        return name
    for key, spec in workflows.items():
        if name in spec.get("aliases", []):
            return key
    return name


def check_output(workflow_key, spec, ts_start):
    """Return 'missing', 'tiny', or 'ok' for workflows with an output check."""
    if not spec.get("output_glob"):
        return None
    out_dir = Path(os.path.expanduser(spec.get("output_dir", "")))
    date = datetime.fromtimestamp(ts_start).strftime("%Y-%m-%d")
    pattern = spec["output_glob"].replace("{date}", date)
    matches = [p for p in out_dir.iterdir() if fnmatch.fnmatch(p.name, pattern)] if out_dir.is_dir() else []
    if not matches:
        return "missing"
    min_bytes = spec.get("min_bytes", 0)
    if all(p.stat().st_size < min_bytes for p in matches):
        return "tiny"
    return "ok"


def error_sig(text):
    norm = re.sub(r"\d+", "N", text.strip())[:200]
    return hashlib.sha1(norm.encode()).hexdigest()[:8]


def compute_signals(runs):
    outcomes = Counter(r["outcome"] for r in runs)
    stops = Counter(r.get("stop_reason") for r in runs)
    total = len(runs)
    sigs = Counter(r["error_sig"] for r in runs if r.get("error_sig"))
    verified = sum(1 for r in runs if r.get("verified"))
    hung = sum(1 for r in runs if r.get("duration_s") and r["duration_s"] > 3600)
    durations = sorted(r["duration_s"] for r in runs if r.get("duration_s") is not None)
    median_s = durations[len(durations) // 2] if durations else None
    return {
        "runs": total,
        "fail": outcomes["failure"] / total,
        "silent": outcomes["silent-failure"] / total,
        "unknown": outcomes["unknown"] / total,
        "cap": stops["cap"] / total,
        "skip": stops["skip"] / total,
        "repeat_error": (sigs.most_common(1)[0][1] / total) if sigs else 0.0,
        "unverified": 1 - (verified / total),
        "hung": hung,
        "median_s": median_s,
        "top_errors": sigs.most_common(3),
    }


def perf_window(runs, now):
    """Split runs into recent (7d) and baseline (8-30d), compare median durations."""
    recent_cut = now - 7 * 86400

    def med(rs):
        ds = sorted(r["duration_s"] for r in rs if r.get("duration_s") is not None)
        return ds[len(ds) // 2] if ds else None

    recent = [r for r in runs if r["ts_start"] >= recent_cut]
    baseline = [r for r in runs if r["ts_start"] < recent_cut]
    rm, bm = med(recent), med(baseline)
    regressed = rm is not None and bm is not None and len(recent) >= 3 and rm > bm * 1.5
    return {"recent_median_s": rm, "baseline_median_s": bm, "regressed": regressed}


def classify(workflow, spec, sig, thresholds):
    layer = spec.get("declared_layer", "prompt")
    if layer == "prompt" and (sig["fail"] > thresholds["fail_rate"] or sig["silent"] > thresholds["silent_rate"]):
        return "stuck-at-prompt", "loop"
    if sig["repeat_error"] >= thresholds["repeat_error"]:
        return "harness-gap", layer
    if layer == "loop" and sig["cap"] >= thresholds["cap_rate"]:
        return "non-terminating-loop", "graph"
    perf = sig.get("perf", {})
    if sig["hung"] / sig["runs"] >= 0.10:
        return "hung-runs", layer
    max_s = spec.get("max_duration_s")
    if max_s and perf.get("recent_median_s") and perf["recent_median_s"] > max_s:
        return "performance-target-breach", layer
    if perf.get("regressed"):
        return "performance-regression", layer
    return None, None


ISSUE_COPY = {
    "stuck-at-prompt": "One-shot prompt that fails or silently produces no output too often. Rewording the prompt has hit its ceiling — wrap it in a loop with a verification step that checks the output actually landed.",
    "harness-gap": "The same error signature repeats across runs. Retrying won't help; a tool, permission, or environment fix is needed before more runs.",
    "non-terminating-loop": "The loop hits its iteration cap instead of converging. The goal-check is too strict or the path is underspecified — promote to explicit graph transitions or loosen the check.",
    "performance-regression": "Median run duration grew >50% week-over-week. Something in the model route, prompt size, or environment got slower. Bisect: model choice first, then context size, then tool latency.",
    "performance-target-breach": "Runs exceed the registry's max_duration_s target. Either the workflow got slower (see regression) or the target is wrong. Fix the slowdown or set a performance-goal loop to bring it back under target.",
    "hung-runs": "≥10% of runs exceeded 1 hour — the trigger fired, the agent never came back, and the wrapper reported OK. Add a hard timeout to the run wrapper (e.g. `timeout` command or launchd `TimeOut`) so hangs fail loudly instead of pretending to succeed.",
}


def proposal_markdown(pid, workflow, spec, issue, target, score, sig):
    current = spec.get("declared_layer", "unknown")
    change_line = (
        f"Keep `{workflow}` at **{current}** — fix the performance, don't change the architecture."
        if target == current else
        f"Move `{workflow}` from **{current}** to **{target}**."
    )
    ev = {
        "runs_30d": sig["runs"], "fail_rate": round(sig["fail"], 3),
        "silent_rate": round(sig["silent"], 3), "cap_rate": round(sig["cap"], 3),
        "repeat_error": round(sig["repeat_error"], 3), "unverified": round(sig["unverified"], 3),
        "median_duration_s": sig.get("median_s"),
        "perf": sig.get("perf"),
        "top_errors": sig["top_errors"],
    }
    return f"""---
id: {pid}
workflow: {workflow}
issue: {issue}
current_layer: {spec.get("declared_layer", "unknown")}
proposed_layer: {target}
score: {score:.2f}
evidence: {json.dumps(ev)}
status: pending
---
# {workflow}: {issue}

## Problem
{ISSUE_COPY[issue]}

## Evidence (30-day window)
- Runs: {sig['runs']} | fail {sig['fail']:.0%} | silent {sig['silent']:.0%} | cap {sig['cap']:.0%} | repeat-error {sig['repeat_error']:.0%} | unverified {sig['unverified']:.0%}
- Top error signatures: {', '.join(f'`{s}` x{c}' for s, c in sig['top_errors']) or 'none'}

## Proposed change
{change_line}

## Verification plan
Run the upgraded workflow once manually and confirm the audit signal drops on the next weekly audit.

## Rollback
Revert the skill/script change; the previous layer behavior is preserved in git or the file's prior version.
"""


def existing_proposal_ids():
    ids = set()
    for sub in ("pending", "approved", "rejected", "done"):
        d = AUDIT_DIR / "proposals" / sub
        if d.is_dir():
            for p in d.iterdir():
                if p.suffix == ".md":
                    ids.add(p.stem)
    return ids


def main():
    reg = load_registry()
    workflows = reg["workflows"]
    for name, p in reg.get("projects", {}).items():
        if name not in workflows:
            workflows[name] = {
                "declared_layer": "harness", "trigger": "manual", "kind": "project",
                "max_duration_s": p.get("max_duration_s"), "aliases": [],
            }
    weights = reg["weights"]
    thresholds = reg["thresholds"]

    runs = dedupe(backfill_runtimes_log() + load_emitter_runs())
    for r in runs:
        r["workflow"] = resolve_alias(r["workflow"], workflows)

    cutoff = int((datetime.now() - timedelta(days=WINDOW_DAYS)).timestamp())
    by_wf = defaultdict(list)
    for r in runs:
        if r.get("ts_start") and r["ts_start"] >= cutoff:
            by_wf[r["workflow"]].append(r)

    # Apply silent-failure output checks to successful runs.
    for wf, wfruns in by_wf.items():
        spec = workflows.get(wf, {})
        for r in wfruns:
            if r["outcome"] == "success":
                check = check_output(wf, spec, r["ts_start"])
                if check in ("missing", "tiny"):
                    r["outcome"] = "silent-failure"

    rows = []
    for wf, wfruns in by_wf.items():
        spec = workflows.get(wf)
        if spec and spec.get("enabled") is False:
            continue
        sig = compute_signals(wfruns)
        sig["perf"] = perf_window(wfruns, int(datetime.now().timestamp()))
        if sig["runs"] < thresholds["min_runs"]:
            rows.append((wf, spec, sig, 0.0, None, None, "insufficient-data"))
            continue
        score = sig["runs"] * (
            weights["fail"] * sig["fail"] + weights["silent"] * sig["silent"]
            + weights["cap"] * sig["cap"] + weights["repeat_error"] * sig["repeat_error"]
            + weights["unverified"] * sig["unverified"]
        )
        issue, target = classify(wf, spec or {"declared_layer": None}, sig, thresholds)
        if not spec:
            issue, target = "unregistered-workflow", None
        rows.append((wf, spec, sig, score, issue, target, None))

    no_telemetry = [k for k, v in workflows.items() if k not in by_wf and v.get("enabled") is not False]

    today = datetime.now().strftime("%Y-%m-%d")
    ranked = sorted([r for r in rows if r[6] is None], key=lambda r: -r[3])
    insufficient = [r for r in rows if r[6] == "insufficient-data"]

    lines = [f"# Layer audit — {today}", "",
             "| # | Workflow | Layer | Runs | Fail | Silent | Cap | RepeatErr | Unverified | Med(s) | Hung(>1h) | Score | Issue |",
             "|---|----------|-------|------|------|--------|-----|-----------|------------|--------|-----------|-------|-------|"]
    for i, (wf, spec, sig, score, issue, target, _) in enumerate(ranked, 1):
        layer = (spec or {}).get("declared_layer", "UNREGISTERED")
        med = f"{sig['median_s']:.0f}" if sig.get("median_s") is not None else "-"
        lines.append(
            f"| {i} | {wf} | {layer} | {sig['runs']} | {sig['fail']:.0%} | {sig['silent']:.0%} "
            f"| {sig['cap']:.0%} | {sig['repeat_error']:.0%} | {sig['unverified']:.0%} | {med} | {sig['hung']} | {score:.2f} | {issue or '-'} |"
        )
    if insufficient:
        lines += ["", "## Insufficient data (<5 runs)",
                  ", ".join(f"{wf} ({sig['runs']})" for wf, _, sig, *_ in insufficient)]
    if no_telemetry:
        lines += ["", "## Registered but no telemetry in window",
                  ", ".join(no_telemetry)]
    lines += ["", f"Proposals: `{AUDIT_DIR}/proposals/pending/`. Move to `approved/` to build, `rejected/` to dismiss."]

    issues_path = AUDIT_DIR / "issues" / f"issues-{today}.md"
    issues_path.write_text("\n".join(lines) + "\n")

    existing = existing_proposal_ids()
    written = []
    for wf, spec, sig, score, issue, target, _ in ranked:
        if not issue or issue == "unregistered-workflow" or score == 0:
            continue
        pid = f"{today}-{wf}-{target or 'fix'}"
        if pid in existing:
            continue
        (AUDIT_DIR / "proposals" / "pending" / f"{pid}.md").write_text(
            proposal_markdown(pid, wf, spec or {}, issue, target, score, sig))
        written.append(pid)

    print(f"issues: {issues_path}")
    print(f"ranked: {len(ranked)} workflows, {sum(1 for r in ranked if r[4])} issues, {len(written)} new proposals")
    for pid in written:
        print(f"  + {pid}")


if __name__ == "__main__":
    sys.exit(main())
