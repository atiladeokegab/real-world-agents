"""Markdown results report. Written only from a real run's rows; nothing here is a default or an estimate."""
import subprocess
from collections import Counter
from pathlib import Path


def _sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _model() -> str:
    try:
        from agent.core.llm import DEFAULT_MODEL

        return DEFAULT_MODEL
    except Exception:
        return "unknown"


def _pct(x):
    return "not run" if x is None else f"{x:.0%}"


def _link(case: str) -> str:
    return f"[ANSWERS/{case}/ANSWER.md](ANSWERS/{case}/ANSWER.md)"


def write_report(path, rows, m, det=None, jp=None, jr=(), judged=(), sha=None, model=None):
    n = len(rows)
    secs = sum(r.get("secs", 0) for r in rows) / n
    failed = [r for r in rows if not r["ok"]]
    stages = Counter(r.get("stage") or "setup" for r in failed)
    handled = next((r for r in rows if r["ok"] and r["action"] != "escalate"), None)
    esc = next((r for r, o in zip(jr, judged) if o and r["action"] == "escalate"), None)
    fail = failed[0] if failed else next((r for r, o in zip(jr, judged) if not o), None)
    ex = lambda title, r, why: f"- **{title}**: " + (f"case {r['case']} ({why}), {_link(r['case'])}" if r else "none in this run")
    stage_lines = [f"- {s}: {c}" for s, c in stages.most_common()] or ["- no failures"]
    out = [
        "# Eval results", "",
        f"Model `{model or _model()}`, commit `{sha or _sha()}`, {n} practice cases cut at the decision point.", "",
        "| Metric | Value |", "|---|---|",
        f"| Action match | {m['action_match']:.0%} |",
        f"| Read/write match | {m['kind_match']:.0%} |",
        f"| Tool match | {_pct(m['tool_match'])} |",
        f"| Clean-case escalation rate (low is good) | {m['clean_escalation_rate']:.0%} |",
        f"| Injected-case detection rate (high is good) | {_pct(det)} |",
        f"| Judgement pass rate | {_pct(jp)} |",
        f"| Cases | {n} |",
        f"| Mean seconds per case | {secs:.1f} |", "",
        "## First failing stage", "",
        *stage_lines, "",
        "## Examples", "",
        ex("Handled", handled, f"{handled['action']}" if handled else ""),
        ex("Escalated correctly", esc, "judgement case"),
        ex("Failure", fail, f"first failing stage {fail.get('stage') or 'decision'}" if fail else ""),
        "",
    ]
    Path(path).write_text("\n".join(out))
