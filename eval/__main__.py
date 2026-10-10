"""uv run python -m eval [--dry] [--workers 6] [--cases 001,002]

Cuts each practice case at its decision point, runs ingest -> evidence -> extract -> decide,
and scores the proposed action class (exact) against eval/gold.json.
"""
import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from eval.cut import cut_index

ROOT = Path(__file__).parents[1]
GOLD = json.loads((Path(__file__).parent / "gold.json").read_text())


def _get(obj, key):
    return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)


def run_case(num: str, dry: bool = False) -> dict:
    """One case through the Contract's loop up to the first proposal. Never raises."""
    row = {"case": num, "stage": None, "action": None, "kind": None, "error": None}
    path = ROOT / "examples" / num
    try:
        if dry:  # stub so the harness runs before core merges
            row.update(action="tool_call", kind="read")
            return row
        row["stage"] = "cut"
        from agent import checks, ingest, llm, tools  # Contract: #11

        case = ingest.load_case(path, cut=cut_index(path / "history.md"))
        row["stage"] = "findings"
        findings = checks.find_evidence(case)
        row["findings"] = len(findings)
        row["stage"] = "extraction"
        case_object = llm.extract(case, findings)
        row["stage"] = "decision"
        proposal = llm.decide(case, case_object, findings, [], None)
        row["action"] = _get(proposal, "action")
        spec = tools.CATALOGUE.get(_get(proposal, "tool") or "")
        if row["action"] == "tool_call" and spec:
            row["kind"] = "read" if _get(spec, "risk") == 1 else "write"
        elif row["action"] != "tool_call":
            row["kind"] = "none"
        row["stage"] = None
    except Exception as e:  # a crash is a miss at that stage, not a stop
        row["error"] = f"{type(e).__name__}: {e}"
    return row


def score(rows: list[dict]) -> dict:
    n = len(rows)
    for r in rows:
        g = GOLD[r["case"]]
        r["ok"] = r["action"] == g["action"]
        r["kind_ok"] = r["kind"] == g["kind"]
    # every practice case is clean (nothing injected) and none is gold-escalate
    esc = sum(r["action"] == "escalate" for r in rows)
    return {"n": n, "action_match": sum(r["ok"] for r in rows) / n,
            "kind_match": sum(r["kind_ok"] for r in rows) / n,
            "clean_escalation_rate": esc / n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--cases", help="comma list, default all 50")
    a = ap.parse_args()
    nums = a.cases.split(",") if a.cases else sorted(GOLD)
    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(run_case, nums, [a.dry] * len(nums)))
    m = score(rows)
    for r in rows:
        print(f"{r['case']} {'ok  ' if r['ok'] else 'FAIL'} got={r['action']}/{r['kind']} "
              f"want={GOLD[r['case']]['action']}/{GOLD[r['case']]['kind']}"
              + (f" stage={r['stage']} {r['error']}" if r["error"] else ""))
    print(f"\naction match {m['action_match']:.0%}  read/write match {m['kind_match']:.0%}  "
          f"clean-case escalation {m['clean_escalation_rate']:.0%}  ({m['n']} cases)")


if __name__ == "__main__":
    main()
