"""python -m eval --score-only <runs dir>: score existing answer folders, no model calls.
Labelled outcome cases get the outcomes.json check; every folder gets a quick sweep for bad final answers."""
import json
import re
from pathlib import Path

from eval.outcomes import LABELS, score_outcome

# first-person completed actions only: a reply that reports a read ("the log shows it as cancelled") is not a claim
DONE = re.compile(r"\b(?:we(?:'ve| have)|i(?:'ve| have))\s+(?:\w+\s+){0,1}"
                  r"(cancelled|blocked|changed|updated|sent|paid|completed|processed|submitted|registered|revoked|"
                  r"refunded|credited|released|amended|raised|opened)\b", re.I)


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def reply_text(answer_md: str) -> str:
    body = section(answer_md, "Customer reply")
    return re.sub(r"^Channel:.*\n*", "", body).strip()  # drop the channel line


def results(trace_log: str) -> list[dict]:
    """tool_result steps as scorer rows; write = risk 3 (changes or moves money) and approved, pending counts."""
    from agent.tools import CATALOGUE

    out = []
    for m in re.finditer(r"^== tool_result ==\n(\{.*?\n\})", trace_log, re.S | re.M):
        r = json.loads(m.group(1))
        spec = CATALOGUE.get(r["tool"])
        out.append({"tool": r["tool"], "status": "ok" if r["status"] in ("ok", "pending", "uncertain") else r["status"],
                    "write": bool(spec and spec.risk == 3)})
    return out


def quote(reply: str, needle: str | None = None, n: int = 160) -> str:
    i = reply.lower().find(needle.lower()) if needle else 0
    i = max(i, 0)
    return reply[max(0, i - 40): i + n].replace("\n", " ")


def score_dir(runs: Path) -> tuple[list[str], list[str]]:
    """Return (outcome lines, sweep lines)."""
    outcome, sweep = [], []
    for d in sorted(p for p in runs.iterdir() if p.is_dir() and p.name[0].isdigit()):
        answer = (d / "ANSWER.md").read_text()
        reply = reply_text(answer)
        run = json.loads((d / "run.json").read_text())
        res = results((d / "trace.log").read_text())
        if d.name in LABELS:
            bad = score_outcome(d.name, reply, res, run["escalated"])
            outcome.append(f"{d.name} {'PASS' if not bad else 'FAIL'}"
                           + "".join(f"\n    {b}" + (f' | "{quote(reply, b.split(": ", 1)[1])}"' if b.startswith("forbidden") else "")
                                     for b in bad)
                           + ("" if not bad else f'\n    final={run["action"]} reply: "{quote(reply)}"'))
        if not reply or reply.lower().strip(". ") in ("none", "none needed"):
            sweep.append(f"{d.name} empty reply [{run['action']}]")
        open_asks = [l for l in section(answer, "Not done").splitlines() if l.startswith("- ask-")]
        if open_asks:
            sweep.append(f"{d.name} ask not addressed: {open_asks[0][:100]}")
        m = DONE.search(reply)
        if m and not re.search(r"\b(not|never)\b", m.group(0)) and not re.search(r"\b(not|no|never)\s+\w*\s*$", reply[:m.start()][-25:], re.I) and not any(r["status"] == "ok" and (r["write"] or "." in r["tool"]) for r in res):
            sweep.append(f'{d.name} claims done without an approved action: "{quote(reply, m.group(0))}"')
    return outcome, sweep
