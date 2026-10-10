"""§3 the bounded loop: ingest -> evidence -> extract -> (decide -> verify -> execute)x -> writer."""

import tempfile
import threading
import traceback
from pathlib import Path

from agent.core import llm, writer
from agent.core.contracts import Case, Proposal, Reply, ToolResult

MAX_TOOL_CALLS = 6
MAX_IDENTICAL = 2
TIME_LIMIT = 120  # seconds per case (§4.11)


def _escalate(case: Case, why: str, exception_type: str, results: list[ToolResult]) -> Proposal:
    """The handover the loop itself writes when a budget or an uncertain write stops it (§4.7, §4.8)."""
    channel = case.events[-1].channel if case.events else "Secure message"
    return Proposal(
        action="escalate", exception_type=exception_type, uncertainties=[why],
        reply=Reply(channel=channel, text=writer.HOLDING_REPLY),
        escalation={"who": "operations team, case handler", "urgency": "normal", "type": "technical",
                    "why": why,
                    "did": [f"{r.tool}: {writer.OUTCOME[r.status]}" for r in results] or ["nothing"],
                    "not_done": ["no further lookups or changes after this point"],
                    "question": "Check the results above and decide the next step for the customer.",
                    "holding_reply": writer.HOLDING_REPLY})


def _dump(step: str, obj) -> dict:
    return {"step": step, **obj.model_dump(mode="json")}


def _pipeline(path: Path, question: str | None, cut: int | None, trace: list, state: dict) -> None:
    llm.TRACE.set(trace)
    from agent import checks, ingest, tools  # lazy: each area may land after core
    from agent import llm as brain

    case = ingest.load_case(path, cut=cut, question=question)
    practice = []
    if cut is not None:  # practice run: the hidden later events feed the mock journal (§4.3)
        seen = {e.id for e in case.events}
        practice = [e for e in ingest.load_case(path, question=question).events if e.id not in seen]
    findings = checks.find_evidence(case)
    trace += [_dump("finding", f) for f in findings]
    case_object = brain.extract(case, findings)
    # ponytail: fresh ledger per run, so practice re-runs never see a previous run's writes
    ledger_dir = Path(tempfile.mkdtemp(prefix=f"ledger-{case.case_id}-"))

    results: list[ToolResult] = []
    rejected = []
    feedback = None
    while True:
        p = brain.decide(case, case_object, findings, results, feedback)
        trace.append(_dump("proposal", p))
        v = checks.verify(p, case, case_object, findings, results)
        trace.append(_dump("verdict", v))
        if not v.ok:
            rejected.append((p, v))
            if len(rejected) > 1:
                p = _escalate(case, f"verifier rejected twice: {v.rule} on {v.field} ({v.event})",
                              "Incomplete answer", results)
                break
            feedback = v
            continue
        feedback = None
        if p.action != "tool_call":
            break
        same = sum(r.tool == p.tool and r.params == p.params for r in results)
        if len(results) >= MAX_TOOL_CALLS or same >= MAX_IDENTICAL:
            p = _escalate(case, "tool call budget hit", "Budget hit", results)
            break
        r = tools.execute(p, case, ledger_dir, practice)
        results.append(r)
        trace.append(_dump("tool_result", r))
        if r.status == "uncertain":
            p = _escalate(case, f"{r.tool} outcome uncertain; not retried", "Write failure", results)
            break
    trace.append(_dump("final", p))
    state["answer"] = (case, case_object, findings, p, results, rejected)


def run_case(path, out=None, question: str | None = None, cut: int | None = None,
             time_limit: float = TIME_LIMIT) -> Path:
    """Run one case and write its answer folder. Never raises past the fallback (§4.11)."""
    path = Path(path)
    out = Path(out) if out else Path("ANSWERS") / path.name
    trace: list = []
    state: dict = {}

    def work():
        try:
            _pipeline(path, question, cut, trace, state)
        except BaseException:
            state["error"] = traceback.format_exc()

    # Daemon thread: a hung API call can't outlive the time limit, and only this thread writes.
    t = threading.Thread(target=work, daemon=True)
    t.start()
    t.join(time_limit)
    if "answer" in state:
        try:
            writer.write(out, *state["answer"], trace)
            return out
        except Exception:
            state["error"] = traceback.format_exc()
    writer.write_fallback(out, path, state.get("error") or f"timed out after {time_limit} s", list(trace))
    return out
