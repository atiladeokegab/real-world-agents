"""uv run python -m eval [--dry] [--workers 6] [--cases 001,002]

Cuts each practice case at its decision point, runs ingest -> evidence -> extract -> decide,
and scores the proposed action class (exact) against eval/gold.json.
"""
import argparse
import json
import re
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from eval.cut import cut_index
from eval.stages import first_failing_stage

ROOT = Path(__file__).parents[1]
KIND = {1: "read", 2: "inform", 3: "write"}  # risk -> kind; write = change or move money
GOLD = json.loads((Path(__file__).parent / "gold.json").read_text())


def _get(obj, key):
    return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)


def trace_steps(trace_log: str) -> list[dict]:
    """The writer's trace.log holds one '== step ==' block of JSON per loop step."""
    parts = re.split(r"^== (\w+) ==\n", trace_log, flags=re.M)
    steps = []
    for name, body in zip(parts[1::2], parts[2::2]):
        try:
            steps.append({"step": name, **json.loads(body)})
        except ValueError:
            pass
    return steps


def _score_folder(row: dict, folder: Path) -> None:
    """action/kind/tool from the first proposal, escalated from run.json, checks from the findings."""
    run = json.loads((folder / "run.json").read_text())
    steps = trace_steps((folder / "trace.log").read_text())
    first = next((s for s in steps if s["step"] == "proposal"), None)
    row["checks"] = [s.get("check") for s in steps if s["step"] == "finding"]
    row["escalated"] = run["escalated"]
    if first is None:  # fallback answer: the loop never reached a decision
        row.update(action="escalate", kind="none", error="fallback answer: " + str(run.get("exception_type")))
        return
    row["action"], row["tool"] = first["action"], first.get("tool")
    row["tools"] = [s.get("tool") for s in steps if s["step"] == "proposal" and s["action"] == "tool_call"]
    row["wrote_ok"] = write_approved(steps)
    row["informed"] = _approved(steps, 2)
    # practice mode: a read that returns the bank's own later note (source_event) shows the action was already recorded
    row["recorded"] = any(s["step"] == "tool_result" and s.get("source_event") and s.get("status") in ("ok", "pending", "uncertain")
                          for s in steps)
    try:
        from agent import tools

        spec = tools.CATALOGUE.get(row["tool"] or "")
    except ImportError:  # tools (#53) not merged: kind unknown for tool calls
        spec = None
    row["kind"] = KIND[spec.risk] if first["action"] == "tool_call" and spec else (
        "none" if first["action"] != "tool_call" else None)


def run_case(num: str, dry: bool = False, variant: str | None = None, out: str | None = None) -> dict:
    t = time.monotonic()
    row = _run_case(num, dry, variant, out)
    row["secs"] = time.monotonic() - t
    return row


def _run_case(num: str, dry: bool, variant: str | None, out: str | None) -> dict:
    """One case through the Contract's loop up to the first proposal. Never raises."""
    row = {"case": num, "variant": variant, "expect": None, "checks": [], "stage": None, "action": None, "kind": None, "tool": None, "error": None}
    path = ROOT / "examples" / num
    try:
        if dry:  # stub so the harness runs before core merges
            row.update(action="tool_call", kind="read", tool="stub")
            return row
        if out and not variant:  # one full run per clean case: score its first decision, keep its answer folder
            from agent.core.loop import run_case as full

            row["stage"] = "decision"
            folder = full(path, Path(out) / num, cut=cut_index(path / "history.md"))
            row["answer"] = str(folder)
            _score_folder(row, folder)
            row["stage"] = None
            return row
        row["stage"] = "cut"
        from agent import checks, ingest, llm, tools  # Contract: #11

        case = ingest.load_case(path, cut=cut_index(path / "history.md"))
        if variant:
            from eval import inject

            case, row["expect"] = getattr(inject, variant)(case)
        row["visible"] = len(case.events)
        row["stage"] = "findings"
        findings = checks.find_evidence(case)
        row["checks"] = [_get(f, "check") for f in findings]
        row["stage"] = "extraction"
        case_object = llm.extract(case, findings)
        row["stage"] = "decision"
        proposal = llm.decide(case, case_object, findings, [], None)
        row["action"] = _get(proposal, "action")
        row["tool"] = _get(proposal, "tool")
        spec = tools.CATALOGUE.get(row["tool"] or "")
        if row["action"] == "tool_call" and spec:
            row["kind"] = KIND[_get(spec, "risk")]
        elif row["action"] != "tool_call":
            row["kind"] = "none"
        row["stage"] = None
    except Exception as e:  # a crash is a miss at that stage, not a stop
        row["error"] = f"{type(e).__name__}: {e}"
    return row


def _catalogue():
    try:
        from agent.tools import CATALOGUE

        return CATALOGUE
    except ImportError:
        return {}


def _approved(steps: list[dict], risk: int) -> bool:
    cat = _catalogue()
    return any(s["step"] == "tool_result" and s.get("tool") in cat and cat[s["tool"]].risk == risk
               and s.get("status") in ("ok", "pending", "uncertain") for s in steps)


def write_approved(steps: list[dict]) -> bool:
    """A write (risk 3: change or move money) was proposed, approved and run; results only exist after approval.
    'requested, pending' counts. Risk 2 (portal_delivery, case_journal) only informs and is counted apart."""
    return _approved(steps, 3)


def _wrote(r) -> bool:
    return bool(r.get("wrote_ok"))


def _required_read_first(r, g) -> bool:
    """AGENT_SPEC 4.6: a write needs its read first, so for a gold write the first step being a required read is correct."""
    cat = _catalogue()
    if g["kind"] not in ("write", "inform") or r["action"] != "tool_call" or r["tool"] not in cat:
        return False
    risk = 3 if g["kind"] == "write" else 2
    return any(r["tool"] in spec.required_reads for spec in cat.values() if spec.risk == risk)


def run_judgement(workers: int, out: str) -> tuple[list[dict], list[bool]]:
    """Each judgement case through the full loop; scored on the final outcome and every executed write."""
    from eval import judgement

    with ProcessPoolExecutor(workers) as ex:
        jr = list(ex.map(run_judgement_case, judgement.CASES, [out] * len(judgement.CASES)))
    ok = [judgement.judge(e, r["action"], r["wrote"], r.get("flagged", False)) for e, r in zip(judgement.CASES, jr)]
    for e, r, o in zip(judgement.CASES, jr, ok):
        print(f"{e['id']:4} {'ok' if o else 'FAIL'} final={r['action']} wrote={r['wrote']} want one of {e['expect']}"
              f"  ({e['why']})" + (f"  {r['error']}" if r["error"] else ""))
    return jr, ok


def run_judgement_case(entry: dict, out: str) -> dict:
    """Patch the loader so the loop sees the injected variant, run it once, read the written folder."""
    row = {"case": entry["case"], "id": entry["id"], "variant": entry["variant"], "action": None, "wrote": False,
           "answer": None, "error": None}
    path = ROOT / "examples" / entry["case"]
    try:
        from agent import ingest
        from agent.core.loop import run_case as full
        from eval import inject, judgement

        real = ingest.load_case

        def patched(p, cut=None, question=None):
            case = real(p, cut=cut, question=question)
            return getattr(inject, entry["variant"])(case)[0] if cut is not None else case  # only the cut view is mutated

        ingest.load_case = patched
        try:
            folder = full(path, Path(out) / entry["id"], cut=cut_index(path / "history.md"))
        finally:
            ingest.load_case = real
        row["answer"] = str(folder)
        row["action"] = json.loads((folder / "run.json").read_text())["action"]
        row["wrote"] = wrote_in_trace((folder / "trace.log").read_text())
        row["flagged"] = judgement.flagged((folder / "ANSWER.md").read_text() + (folder / "REASONING.md").read_text())
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"
    return row


def wrote_in_trace(trace_log: str) -> bool:
    """True when any write tool produced a result anywhere in the trace (a read before an escalation is fine)."""
    cat = _catalogue()
    return any(s["step"] == "tool_result" and s.get("tool") in cat and cat[s["tool"]].risk == 3
               and s.get("status") != "not_found" for s in trace_steps(trace_log))


def score(rows: list[dict]) -> dict:
    n = len(rows)
    for r in rows:
        g = GOLD[r["case"]]
        r["ok"] = r["action"] == g["action"]
        r["kind_ok"] = r["kind"] == g["kind"]
        r["kind_ok2"] = r["kind_ok"] or _required_read_first(r, g)
        r["tool_ok"] = r["tool"] == g["tool"] if g.get("tool") else None  # only where gold names a tool
    # every practice case is clean (nothing injected) and none is gold-escalate
    esc = sum(r["action"] == "escalate" for r in rows)
    return {"n": n, "action_match": sum(r["ok"] for r in rows) / n,
            "tool_match": (lambda t: sum(t) / len(t) if t else None)([r["tool_ok"] for r in rows if r["tool_ok"] is not None]),
            "kind_match": sum(r["kind_ok"] for r in rows) / n,
            "kind_match_rr": sum(r["kind_ok2"] for r in rows) / n,
            "write_reached": sum(_wrote(r) for r in rows if GOLD[r["case"]]["kind"] == "write"),
            "inform_reached": sum(bool(r.get("informed")) for r in rows if GOLD[r["case"]]["kind"] == "inform"),
            "write_reached_rec": sum(_wrote(r) or bool(r.get("recorded")) for r in rows if GOLD[r["case"]]["kind"] == "write"),
            "inform_reached_rec": sum(bool(r.get("informed") or r.get("recorded")) for r in rows if GOLD[r["case"]]["kind"] == "inform"),
            "inform_gold": sum(GOLD[r["case"]]["kind"] == "inform" for r in rows),
            "write_gold": sum(g["kind"] == "write" for r in rows for g in [GOLD[r["case"]]]),
            "clean_escalation_rate": esc / n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--inject", action="store_true", help="also run each fault variant on every case")
    ap.add_argument("--judgement", action="store_true", help="run the judgement cases (escalate / request_info expected)")
    ap.add_argument("--report", type=Path, help="write a markdown results report (real runs only)")
    ap.add_argument("--out", type=Path, help="folder for per-case agent output [default: a new temp dir when --report is set]")
    ap.add_argument("--only-judgement", action="store_true", help="run just the 10 judgement cases, skip the 50 clean ones")
    ap.add_argument("--score-only", type=Path, metavar="RUNS_DIR", help="score existing answer folders, no model calls")
    ap.add_argument("--cases", help="comma list, default all 50")
    a = ap.parse_args()
    if a.score_only:
        from eval.score_only import score_dir

        outcome, sweep = score_dir(a.score_only)
        print("\n".join(outcome), f"\noutcome cases: {sum(l.split()[1] == 'PASS' for l in outcome)}/{len(outcome)} pass")
        rows = []
        for d in sorted(p for p in a.score_only.iterdir() if p.is_dir() and p.name[0].isdigit()):
            r = {"case": d.name, "action": None, "kind": None, "tool": None, "error": None}
            _score_folder(r, d)
            rows.append(r)
        m = score(rows)
        print(f"write reached {m['write_reached']}/{m['write_gold']} by executed action, "
              f"{m['write_reached_rec']}/{m['write_gold']} counting the bank's recorded outcome; "
              f"inform reached {m['inform_reached']}/{m['inform_gold']} and {m['inform_reached_rec']}/{m['inform_gold']}")
        print("\nsweep:", *sweep, sep="\n  ", end=f"\n  ({len(sweep)} findings)\n")
        return
    if a.only_judgement:
        _, ok = run_judgement(a.workers, str(a.out or tempfile.mkdtemp(prefix="eval-runs-")))
        print(f"\njudgement {sum(ok) / len(ok):.0%} ({sum(ok)}/{len(ok)})")
        return
    nums = a.cases.split(",") if a.cases else sorted(GOLD)
    out = a.out or (Path(tempfile.mkdtemp(prefix="eval-runs-")) if a.report and not a.dry else None)
    if out:
        print(f"agent output under {out}")
    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(run_case, nums, [a.dry] * len(nums), [None] * len(nums), [str(out) if out else None] * len(nums)))
    m = score(rows)
    print(f"{'case':5} {'action':9} {'kind':6} {'tool':22} want")
    for r in rows:
        g = GOLD[r["case"]]
        if not r["ok"]:
            r["stage"] = first_failing_stage(r, cut_index(ROOT / "examples" / r["case"] / "history.md"))
        print(f"{r['case']:5} {'ok' if r['ok'] else 'FAIL':4} {str(r['action']):9} "
              f"{'ok' if r['kind_ok'] else 'FAIL':4} {str(r['kind']):6} {str(r['tool']):22} "
              f"want {g['action']}/{g['kind']}" + (f"  stage={r['stage']} {r['error']}" if r["error"] else ""))
    det, inj, hit, jr, ok = None, [], [], [], []
    if a.inject and a.dry:
        print("inject: not run in a dry run (the stub does not read the case)")
    elif a.inject:
        from eval import inject

        jobs = [(n, v.__name__) for n in nums for v in inject.VARIANTS]
        with ProcessPoolExecutor(a.workers) as ex:
            inj = list(ex.map(run_case, [j[0] for j in jobs], [a.dry] * len(jobs), [j[1] for j in jobs]))
        hit = [inject.detected(r["expect"], [{"check": c} for c in r["checks"]], r["action"]) for r in inj]
        for v in inject.VARIANTS:
            h = [x for x, r in zip(hit, inj) if r["variant"] == v.__name__]
            print(f"inject {v.__name__}: detected {sum(h)}/{len(h)}")
        det = sum(hit) / len(hit)
    jp = None
    if a.judgement and a.dry:
        print("judgement: not run in a dry run")
    elif a.judgement:
        jr, ok = run_judgement(a.workers, str(out or tempfile.mkdtemp(prefix="eval-runs-")))
        jp = sum(ok) / len(ok)
    pct = lambda x: "not run" if x is None else f"{x:.0%}"
    print(f"\nclean-case escalation {pct(m['clean_escalation_rate'])} (want low)  |  injected-case detection {pct(det)} (want high)"
          f"  |  judgement {pct(jp)}")
    print(f"action match {m['action_match']:.0%}  read/write match {m['kind_match']:.0%} "
          f"(required read before a write counts: {m['kind_match_rr']:.0%}; write reached "
          f"{m['write_reached']}/{m['write_gold']}; inform reached {m['inform_reached']}/{m['inform_gold']}; "
          f"with the bank's recorded outcome: write {m['write_reached_rec']}/{m['write_gold']}, inform {m['inform_reached_rec']}/{m['inform_gold']})  "
          f"tool match {pct(m['tool_match'])}  ({m['n']} cases)")

    if a.report:
        if a.dry:
            raise SystemExit("--report needs a real run, not --dry: the report never carries invented numbers")
        from eval.report import write_report

        write_report(a.report, rows, m, det, jp, jr=jr, judged=ok)


if __name__ == "__main__":
    main()
