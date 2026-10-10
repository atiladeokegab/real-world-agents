"""Outcome score on hand-labelled cases: the final state, not the first step. Exact/substring, no model judge."""
import json
import re
from pathlib import Path

LABELS = json.loads((Path(__file__).parent / "outcomes.json").read_text())


NEGATED = re.compile(r"\b(not|no|never|cannot|whether|unless|until|if)\b|n't", re.I)


def claimed(text: str, phrase: str) -> bool:
    """True when phrase appears outside a negation or hedge ("hasn't arrived", "whether … received" are not claims)."""
    i = text.find(phrase)
    while i != -1:
        clause = re.split(r"[.,;!?\n]", text[max(0, i - 45): i])[-1]  # the hedge must be in the same clause
        if not NEGATED.search(clause):
            return True
        i = text.find(phrase, i + 1)
    return False


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
    bad += [f"forbidden claim: {s}" for s in lab["forbidden"] if claimed(text, s)]
    return bad


def outcome_rate(finals: dict[str, dict]) -> float:
    """finals: case -> {reply, results, escalated}; scores only the labelled cases present."""
    got = {c: not score_outcome(c, **f) for c, f in finals.items() if c in LABELS}
    return sum(got.values()) / len(got) if got else 0.0
