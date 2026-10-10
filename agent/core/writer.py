"""§4.9 writer: ANSWER.md, REASONING.md, trace.log, run.json. Fixed schema, atomic writes."""

import json
import os
from pathlib import Path

from agent.core.contracts import Case, CaseObject, Finding, Proposal, ToolResult, Verdict

OUTCOME = {"ok": "done", "not_found": "done, no record found", "pending": "requested, pending result",
           "timeout": "not done, timed out", "error": "not done, error", "uncertain": "uncertain"}

HOLDING_REPLY = ("Thank you for your message. A colleague is reviewing your request and will "
                 "contact you. No changes have been made to your account.")


def _put(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _bullets(items, empty="none") -> str:
    return "\n".join(f"- {i}" for i in items) or f"- {empty}"


def _note(escalation: dict) -> str:
    lines = []
    for k, v in escalation.items():
        if isinstance(v, list):
            lines.append(f"- {k}:" + "".join(f"\n  - {i}" for i in v))
        else:
            lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _trace_log(raw_files: dict[str, str], case_object: CaseObject | None, trace: list) -> str:
    parts = [f"== raw file: {name} ==\n{text}" for name, text in raw_files.items()]
    if case_object is not None:
        parts.append("== case object the model saw ==\n" + case_object.model_dump_json(indent=2))
    parts += [f"== {r.get('step', 'step')} ==\n" + json.dumps(r, indent=2, default=str) for r in trace]
    return "\n\n".join(parts) + "\n"


def _cost(trace: list) -> dict:
    calls = [r for r in trace if r.get("step") == "model_call"]
    return {"model_calls": len(calls),
            **{k: sum(r.get(k) or 0 for r in calls) for k in ("input_tokens", "output_tokens", "seconds")}}


def write(out: Path, case: Case, case_object: CaseObject, findings: list[Finding],
          proposal: Proposal, results: list[ToolResult],
          rejected: list[tuple[Proposal, Verdict]], trace: list) -> None:
    out.mkdir(parents=True, exist_ok=True)
    escalated = proposal.action == "escalate"
    addressed = set(proposal.asks_addressed)
    not_done = [f"{a.id}: {a.text}" for a in case_object.asks if a.id not in addressed]
    if escalated and proposal.escalation:
        not_done += [str(i) for i in proposal.escalation.get("not_done", [])]

    answer = [f"# Case {case.case_id}: {case.title}", "",
              "## Decision", f"{proposal.action}" + (f" ({proposal.exception_type})" if proposal.exception_type else "")]
    if case.question:
        answer += ["", "## Answer to the question", f"Question: {case.question}", "",
                   proposal.question_answer or "No direct answer; see the handover note."]
    answer += ["", "## Actions", _bullets(
        f"{r.tool}({json.dumps(r.params, default=str)}): {OUTCOME[r.status]}" for r in results)]
    reply = proposal.reply
    answer += ["", "## Customer message",
               f"Channel: {reply.channel}\n\n{reply.text}" if reply else "None sent."]
    answer += ["", "## Not done", _bullets(not_done)]
    answer += ["", "## Evidence used", _bullets(proposal.claims_relied_on)]
    if escalated:
        answer += ["", "## Handover note", _note(proposal.escalation or {"holding_reply": HOLDING_REPLY})]

    fixed = set(proposal.findings_addressed)
    reasoning = [f"# Reasoning: case {case.case_id}", "",
                 "## Facts and claims", _bullets(
                     f"{c.subject} {c.predicate} {c.value} ({c.source_actor}, {c.channel}, {c.event})"
                     for c in case_object.claims),
                 "", "## Unknowns", _bullets(case_object.unknowns),
                 "", "## Findings", _bullets(
                     f"{f.id} [{f.kind}/{f.check}] {f.detail} ({', '.join(f.events)}): "
                     + ("addressed" if f.id in fixed else "not addressed") for f in findings),
                 "", "## Policy checks", _bullets(
                     f"rejected {p.action}: {v.rule} on {v.field} ({v.event}): {v.message}" for p, v in rejected),
                 "", "## Exception", proposal.exception_type or "none",
                 "", "## Alternatives rejected", _bullets(f"{p.action} {p.tool or ''}".strip() for p, _ in rejected),
                 "", "## Uncertainties", _bullets(proposal.uncertainties)]

    run = {"track": case.track, "case_id": case.case_id, "action": proposal.action,
           "escalated": escalated, "exception_type": proposal.exception_type,
           "outcome": "escalated" if escalated else "answered", "tool_calls": len(results),
           "fallback": False, **_cost(trace)}

    _put(out / "ANSWER.md", "\n".join(answer) + "\n")
    _put(out / "REASONING.md", "\n".join(reasoning) + "\n")
    _put(out / "trace.log", _trace_log(case.raw_files, case_object, trace))
    _put(out / "run.json", json.dumps(run, indent=2) + "\n")


def write_fallback(out: Path, case_path: Path, error: str, trace: list) -> None:
    """§4.11: crash, timeout or API failure still leaves a valid escalated answer."""
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in Path(case_path).rglob("*") if p.is_file()) if Path(case_path).is_dir() else []
    raw = {str(p.relative_to(case_path)): p.read_text(encoding="utf-8", errors="replace") for p in files}
    received = _bullets((f"{name} ({len(text)} chars)" for name, text in raw.items()), "nothing readable")

    answer = [f"# Case {Path(case_path).name}", "",
              "## Decision", "escalate (system failure)",
              "", "## Actions", "- none",
              "", "## Customer message", f"Channel: same as the request\n\n{HOLDING_REPLY}",
              "", "## Not done", "- every request in this case: the agent failed before deciding",
              "", "## Evidence used", "- none",
              "", "## Handover note",
              _note({"who": "operations team, case handler", "urgency": "normal", "type": "technical",
                     "what happened": "escalated: system failure; here is what we received",
                     "received": [f"{n} ({len(t)} chars)" for n, t in raw.items()] or ["nothing readable"],
                     "did": "nothing", "did_not": "no lookup, change or reply was made",
                     "question": "What does the customer need, and is it safe to do?",
                     "holding_reply": HOLDING_REPLY})]
    reasoning = [f"# Reasoning: case {Path(case_path).name}", "",
                 "## What failed", f"```\n{error.strip()}\n```",
                 "", "## What we received", received,
                 "", "## Exception", "system failure: escalated with nothing done"]
    run = {"track": None, "case_id": Path(case_path).name, "action": "escalate", "escalated": True,
           "exception_type": "system_failure", "outcome": "system_failure", "tool_calls": 0,
           "fallback": True}

    _put(out / "ANSWER.md", "\n".join(answer) + "\n")
    _put(out / "REASONING.md", "\n".join(reasoning) + "\n")
    _put(out / "trace.log", _trace_log(raw, None, trace + [{"step": "error", "error": error}]))
    _put(out / "run.json", json.dumps(run, indent=2) + "\n")
