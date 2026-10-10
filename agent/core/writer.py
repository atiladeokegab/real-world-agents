"""§4.9 writer: ANSWER.md, REASONING.md, trace.log, run.json. Fixed schema, atomic writes.

Headings, labels and wording follow docs/design.md §Copy and §States exactly.
"""

import json
import os
from pathlib import Path

from agent.core.contracts import Case, CaseObject, Finding, Proposal, ToolResult, Verdict

# §States: every case ends in exactly one of these. state -> (badge, glyph, colour)
STATES = {
    "done": ("DONE", "●", "#1F9D6B"),
    "requested": ("REQUESTED", "◐", "#D99A1E"),
    "info": ("NEEDS INFO", "?", "#3A6FF7"),
    "escalated": ("ESCALATED", "▲", "#E5533D"),
    "noop": ("NO ACTION", "○", "#8A8F98"),
    "failure": ("SYSTEM FAILURE", "■", "#B03A8C"),
}

# §Copy "Actions": done / requested — pending result / not done / uncertain
OUTCOME = {"ok": "done", "not_found": "done — no record found", "pending": "requested — pending result",
           "timeout": "not done — timed out", "error": "not done — error", "uncertain": "uncertain"}

# §Copy reply templates
HOLDING_REPLY = "We've received your request and passed it to {team}. We'll reply here."  # system failure (#68)
ESCALATION_REPLY = ("Thank you for your message. We've passed your request to {team}, who will review it "
                    "and reply to you here. We haven't made any changes to your account while this is reviewed.")
DEFAULT_TEAM = "our team"

# §Copy handover note fields, in order. Brain's keys -> the design's labels.
HANDOVER = [("who", "Take it"), ("urgency", "Urgency"), ("type", "Type"), ("verified", "Verified"),
            ("claimed", "Only claimed"), ("conflicts", "Conflicts"), ("did", "We did"),
            ("not_done", "We did not"), ("question", "Question for you"), ("holding_reply", "Safe to send now")]
# Keys the model sometimes writes instead of brain's; folded into the design's fields.
ALIASES = {"team": "who", "claimed_only": "claimed", "done": "did", "actions_taken": "did",
           "did_not": "not_done", "deliberately_not_done": "not_done", "question_for_human": "question",
           "safe_to_send_now": "holding_reply"}
URGENCY = {"urgent": "Urgent", "high": "Today", "today": "Today", "normal": "Routine", "low": "Routine",
           "routine": "Routine"}
RISK = {1: "read — autonomous", 2: "inform — autonomous after the claim linter",
        3: "change or move money — needs verified identity, mandate and no open conflict"}
NONE = "None."


def team_phrase(team: str | None) -> str:
    """The team as it reads in a customer sentence: 'Business Payments' -> 'our business payments'."""
    if not team:
        return DEFAULT_TEAM
    return team if team.lower().startswith(("the ", "our ")) else f"our {team.lower()}"


def _put(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _bullets(items) -> str:
    return "\n".join(f"- {i}" for i in items if i is not None and i != "") or NONE


def verdict_text(v) -> str:
    """'rule on field (event): message', leaving out whatever the verdict doesn't have (never "None")."""
    return (f"{v.rule or 'rejected'}" + (f" on {v.field}" if v.field else "") + (f" ({v.event})" if v.event else "")
            + (f": {v.message}" if v.message else ""))


def _clause(text) -> str:
    """Model or error text about to get our own full stop: drop its trailing one, so it never reads '..'."""
    return str(text).rstrip().rstrip(".").rstrip()


def _n(k: int, word: str) -> str:
    return f"{k} {word}{'' if k == 1 else 's'}"


def _short(data, limit: int = 200) -> str:
    text = json.dumps(data, default=str, ensure_ascii=False) if not isinstance(data, str) else data
    return text if len(text) <= limit else text[:limit] + "…"


def _customer_channel(case: Case | None) -> str:
    for e in reversed(case.events if case else []):
        if "internal" not in e.channel.lower() and not e.sender.startswith("H&V"):
            return e.channel
    return "Same channel as the request"


def _trace_log(raw_files: dict[str, str], case_object: CaseObject | None, trace: list) -> str:
    parts = [f"== raw file: {name} ==\n{text}" for name, text in raw_files.items()]
    if case_object is not None:
        parts.append("== case object the model saw ==\n" + case_object.model_dump_json(indent=2))
    parts += [f"== {r.get('step', 'step')} ==\n" + json.dumps(r, indent=2, default=str) for r in trace]
    return "\n\n".join(parts) + "\n"


def _handling(name: str | None) -> str:
    """§4.8: the exception type and its fixed handling (brain's registry)."""
    if not name:
        return NONE
    try:
        from agent.llm import handling_for
        return f"{name} → {handling_for(name)}"
    except ImportError:  # brain not merged: the type alone
        return name


def _risk(tools: list[str]) -> str:
    if not tools:
        return "no tool used"
    try:
        from agent.tools import CATALOGUE
        level = max(getattr(CATALOGUE.get(t), "risk", 1) for t in tools)
    except ImportError:
        return f"{', '.join(tools)} (risk not known: tool catalogue missing)"
    return RISK[level]


def _cost(trace: list) -> dict:
    calls = [r for r in trace if r.get("step") == "model_call"]
    return {"model_calls": len(calls),
            **{k: sum(r.get(k) or 0 for r in calls) for k in ("input_tokens", "output_tokens", "seconds")}}


def state_of(proposal: Proposal, results: list[ToolResult]) -> str:
    if proposal.action == "escalate":
        return "escalated"
    if proposal.action == "request_info":
        return "info"
    if proposal.action == "no_op":
        return "noop"
    return "requested" if any(r.status == "pending" for r in results) else "done"


def handover(escalation: dict | None, holding: str) -> dict:
    """The note in the design's fields: aliases folded in, every field present."""
    note: dict = {}
    for key, value in (escalation or {}).items():
        canon = ALIASES.get(key, key)
        if isinstance(value, list) or isinstance(note.get(canon), list):
            old = note.get(canon) or []
            old = old if isinstance(old, list) else [old]
            new = value if isinstance(value, list) else [value]
            note[canon] = old + [v for v in new if v not in old]
        elif value and (canon not in note or key != canon):
            note[canon] = value  # an alias is the model's own words: it beats brain's generic fill
    note.setdefault("holding_reply", holding)
    note["urgency"] = URGENCY.get(str(note.get("urgency", "")).lower(), "Routine")
    note["type"] = str(note.get("type") or "technical").capitalize()
    return note


def _note(note: dict) -> str:
    lines = []
    for key, label in HANDOVER + [(k, k.replace("_", " ").capitalize()) for k in note
                                  if k not in dict(HANDOVER) and k != "why"]:
        value = note.get(key)
        if isinstance(value, list):
            lines.append(f"**{label}:**\n" + _bullets(value))
        else:
            lines.append(f"**{label}:** {value or NONE}")
    return "\n\n".join(lines)


def received(case: Case | None, raw_names: list[str], cut: int | None = None) -> str:
    """§Copy "What we received": files, event count, cut point, identity level."""
    parts = [", ".join(f"`{n}`" for n in raw_names) or "no readable files"]
    if case is not None:
        parts += [_n(len(case.attachments), "attachment"), _n(len(case.events), "event")]
        if cut is not None and case.events:
            parts.append(f"cut at `{case.events[-1].id}`")
        role = f" {case.authority.role}" if case.authority.role else ""
        parts.append(f"identity: {case.authority.identity}{role} ({_customer_channel(case)})")
    return " · ".join(parts)


def _actions(results: list[ToolResult], rejected: list[tuple[Proposal, Verdict]]) -> list[str]:
    lines = []
    for r in results:
        detail = f" → {_short(r.data)}" if r.status == "ok" and r.data else ""
        lines.append(f"`{r.tool}({_short(r.params, 120)})` — **{OUTCOME[r.status]}**{detail}")
    for p, v in rejected:
        if p.action == "tool_call":
            lines.append(f"`{p.tool}({_short(p.params, 120)})` — **not done**, rejected by the verifier ({v.rule or 'rejected'}).")
    return lines


def _decision(state: str, proposal: Proposal, results: list[ToolResult], note: dict | None) -> str:
    tools = ", ".join(dict.fromkeys(r.tool for r in results))
    channel = proposal.reply.channel if proposal.reply else None
    if state == "escalated":
        why = (proposal.escalation or {}).get("why") or proposal.exception_type or "the agent must not resolve it alone"
        why = _clause(why)
        return f"Handed to {_clause(note['who'])}: {why}." if note and note.get("who") else f"Handed to a person: {why}."
    if state == "info":
        return "Asked the customer to confirm what we need before acting."
    if state == "noop":
        return "Nothing needs doing, and doing something would be wrong."
    if state == "requested":
        return f"Asked {tools} for a result. No result yet."
    if tools:
        return f"Checked {tools} and replied" + (f" on {_clause(channel)}." if channel else ".")
    return f"Replied on {_clause(channel)}." if channel else "Done."


def summary(state: str, proposal: Proposal | None, results: list[ToolResult], note: dict | None) -> str:
    """§States terminal outcome line, after the badge."""
    if state == "done":
        return f"{_n(len(results), 'action')} · 0 escalations"
    if state == "requested":
        return "pending result from " + ", ".join(dict.fromkeys(r.tool for r in results if r.status == "pending"))
    if state == "info":
        return "1 question to the customer"
    if state == "escalated":
        return f"handover to {note.get('who') or 'a person'}, {note['urgency'].lower()}"
    if state == "noop":
        return "nothing to do"
    return "escalated with what we received"


def write(out: Path, case: Case, case_object: CaseObject, findings: list[Finding],
          proposal: Proposal, results: list[ToolResult],
          rejected: list[tuple[Proposal, Verdict]], trace: list, cut: int | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    state = state_of(proposal, results)
    badge = STATES[state][0]
    note = None
    if state == "escalated":
        who = (proposal.escalation or {}).get("who") or (proposal.escalation or {}).get("team")
        note = handover(proposal.escalation, ESCALATION_REPLY.format(team=team_phrase(who)))

    addressed = set(proposal.asks_addressed)
    not_done = [f"{_clause(a.text)} ({a.id}) — because this run did not close it"
                for a in case_object.asks if a.id not in addressed]
    not_done += [f"{p.action}{' ' + p.tool if p.tool else ''} — because the verifier rejected it "
                 f"({verdict_text(v)})" for p, v in rejected]
    not_done += [f"`{r.tool}` — because it {r.status.replace('_', ' ')}" for r in results
                 if r.status in ("timeout", "error")]
    if note:
        not_done += [i if "because" in str(i) else f"{_clause(i)} — because the case was handed to a person"
                     for i in (note.get("not_done") or [])]

    cited = set(proposal.claims_relied_on)
    evidence = [f"`{c}`" for c in proposal.claims_relied_on]
    evidence += [f"`tool:{r.tool}` {OUTCOME[r.status]}" for r in results if f"tool:{r.tool}" not in cited]

    failures = [f"`{r.tool}` — {OUTCOME[r.status]}" for r in results if r.status in ("timeout", "error", "uncertain")]
    pending = ", ".join(dict.fromkeys(r.tool for r in results if r.status == "pending"))
    if failures:
        failed = _bullets(failures)
    elif rejected:
        failed = "Nothing. The verifier's rejection is the system working."
    elif pending:
        failed = f"Nothing. {pending} has no live connection here, so the check is recorded as requested."
    else:
        failed = "Nothing."

    reply = proposal.reply
    answer = [f"# Answer — Case {case.case_id}", "",
              "## Decision", "", f"{badge} — {_decision(state, proposal, results, note)}", "",
              "## What we received", "", received(case, list(case.raw_files), cut), "",
              "## Actions", "", _bullets(_actions(results, rejected)), ""]
    if case.question:
        answer += ["## Answer to the question", "", f"Question: {case.question}", "",
                   proposal.question_answer or "No direct answer; see the handover.", ""]
    answer += ["## Customer reply", "",
               f"Channel: {reply.channel}\n\n{reply.text}" if reply and reply.text else "None needed.", "",
               "## Not done", "", _bullets(not_done), "",
               "## Evidence used", "", _bullets(evidence), ""]
    if note:
        answer += ["## Handover", "", _note(note), ""]
    answer += ["## What failed", "", failed]

    fixed = set(proposal.findings_addressed)
    facts = [f"Claim: {c.subject} {c.predicate} {c.value} ({c.source_actor}, {c.channel}, `{c.event}`)"
             for c in case_object.claims]
    facts += [f"Fact: `tool:{r.tool}` returned {_short(r.data)}" for r in results if r.status == "ok"]
    closed = sum(a.id in addressed for a in case_object.asks)
    checks = [f"Identity: {case.authority.identity} ({_customer_channel(case)})",
              f"Authority: role {case.authority.role or 'none recorded'}",
              f"Risk level: {_risk(list(dict.fromkeys([r.tool for r in results] + ([proposal.tool] if proposal.tool else []))))}",
              f"Completion: {closed} of {_n(len(case_object.asks), 'ask')} closed"]
    checks += [f"Verifier: ✗ {verdict_text(v)}" for _, v in rejected]
    checks.append("Verifier: ✓ approved the final proposal" if state != "escalated" or not rejected
                  else "Verifier: rejected twice, so the case was escalated")
    reasoning = [f"# Reasoning — Case {case.case_id}", "",
                 "## Facts and claims", "", _bullets(facts), "",
                 "## Findings", "", _bullets(
                     f"**{f.id} · {f.check}** ({f.kind}) — {_clause(f.detail)} ({', '.join(f.events)}). "
                     + ("Addressed." if f.id in fixed else "Not addressed.") for f in findings), "",
                 "## Policy checks", "", _bullets(checks), "",
                 "## Exception and handling", "", _handling(proposal.exception_type), "",
                 "## Alternatives rejected", "", _bullets(
                     f"{p.action}{' ' + p.tool if p.tool else ''} — {verdict_text(v)}" for p, v in rejected), "",
                 "## Uncertainties", "", _bullets(list(case_object.unknowns) + list(proposal.uncertainties))]

    run = {"track": case.track, "case_id": case.case_id, "action": proposal.action,
           "escalated": state == "escalated", "exception_type": proposal.exception_type,
           "outcome": "escalated" if state == "escalated" else "answered", "tool_calls": len(results),
           "fallback": False, **_cost(trace), "state": state,
           "summary": summary(state, proposal, results, note)}

    _put(out / "ANSWER.md", "\n".join(answer) + "\n")
    _put(out / "REASONING.md", "\n".join(reasoning) + "\n")
    _put(out / "trace.log", _trace_log(case.raw_files, case_object, trace))
    _put(out / "run.json", json.dumps(run, indent=2) + "\n")


def write_fallback(out: Path, case_path: Path, error: str, trace: list,
                   stage: str | None = None, case: Case | None = None, cut: int | None = None) -> None:
    """§4.11: crash, timeout or API failure still leaves a valid escalated answer, every heading kept."""
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in Path(case_path).rglob("*") if p.is_file()) if Path(case_path).is_dir() else []
    raw = {str(p.relative_to(case_path)): p.read_text(encoding="utf-8", errors="replace") for p in files}
    case_id = case.case_id if case else Path(case_path).name
    where = stage or "run"
    last = (error.strip().splitlines() or ["unknown error"])[-1]
    reply = HOLDING_REPLY.format(team=DEFAULT_TEAM)
    note = handover({
        "who": "Operations service queue", "urgency": "today", "type": "technical",
        "verified": [f"identity {case.authority.identity} ({_customer_channel(case)})"] if case else [],
        "claimed": [], "conflicts": ["None found."],
        "did": [f"Ran the case up to the {where} stage, which failed."],
        "not_done": ["Check, change or reply with any status."],
        "question": "What does the customer need, and is it safe to do?"}, reply)

    answer = [f"# Answer — Case {case_id}", "",
              "## Decision", "", f"SYSTEM FAILURE — The {where} stage failed. Escalated with everything received so far.", "",
              "## What we received", "", received(case, list(raw), cut), "",
              "## Actions", "", NONE, ""]
    if case is not None and case.question:
        answer += ["## Answer to the question", "", f"Question: {case.question}", "",
                   "No answer: the run failed before deciding. See the handover.", ""]
    answer += ["## Customer reply", "", f"Channel: {_customer_channel(case)}\n\n{reply}", "",
               "## Not done", "", f"- Everything the case asked — because the {where} stage didn't complete.", "",
               "## Evidence used", "", NONE, "",
               "## Handover", "", _note(note), "",
               "## What failed", "",
               f"**{where}**: {_clause(last)}. "
               + ("No stage completed." if where == "ingest" else "The stages before it completed.")
               + " Their output and the full error are in `trace.log`."]
    reasoning = [f"# Reasoning — Case {case_id}", "",
                 "## Facts and claims", "", "Not reached: the run failed before a decision. Received: "
                 + (", ".join(f"`{n}`" for n in raw) or "no readable files") + ".", "",
                 "## Findings", "", "Not reached.", "",
                 "## Policy checks", "", "Not reached.", "",
                 "## Exception and handling", "",
                 f"system failure in {where} → escalate with what was received (§4.11).", "",
                 "## Alternatives rejected", "", "- Leave the case blank — a blank answer helps nobody.", "",
                 "## Uncertainties", "", "- Everything the decision would have settled."]
    run = {"track": case.track if case else None, "case_id": case_id, "action": "escalate", "escalated": True,
           "exception_type": "system_failure", "outcome": "system_failure", "tool_calls": 0,
           "fallback": True, **_cost(trace), "state": "failure", "summary": summary("failure", None, [], None)}

    _put(out / "ANSWER.md", "\n".join(answer) + "\n")
    _put(out / "REASONING.md", "\n".join(reasoning) + "\n")
    _put(out / "trace.log", _trace_log(raw, None, trace + [{"step": "error", "stage": stage, "error": error}]))
    _put(out / "run.json", json.dumps(run, indent=2) + "\n")
