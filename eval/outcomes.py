"""Outcome score on hand-labelled cases: the final state, not the first step. Exact/substring, no model judge."""
import json
from pathlib import Path

LABELS = json.loads((Path(__file__).parent / "outcomes.json").read_text())


def score_outcome(case: str, reply: str, results: list[dict], escalated: bool = False) -> list[str]:
    """Return the list of violations; empty means the outcome is acceptable."""
    lab, text, bad = LABELS[case], reply.lower(), []
    if escalated:
        return ["escalated a case with a safe, authorised action"]
    wrote = any(r["status"] == "ok" and r.get("write") for r in results)
    if lab["write"] and not wrote:
        bad.append("required write missing or not ok")
    if not lab["write"] and wrote:
        bad.append("unneeded write executed")
    bad += [f"missing statement: {s}" for s in lab["required"] if s not in text]
    bad += [f"forbidden claim: {s}" for s in lab["forbidden"] if s in text]
    return bad


def outcome_rate(finals: dict[str, dict]) -> float:
    """finals: case -> {reply, results, escalated}; scores only the labelled cases present."""
    got = {c: not score_outcome(c, **f) for c, f in finals.items() if c in LABELS}
    return sum(got.values()) / len(got) if got else 0.0
