"""The handover note on every escalation (AGENT_SPEC §4.8), and how it reads in ANSWER.md."""

from __future__ import annotations

from typing import Any

from agent.llm import copy

TEAMS = {
    "transfer_journal": "Payments operations",
    "standing_order_journal": "Payments operations",
    "mandate_journal": "Payments operations (Direct Debits)",
    "card_service": "Cards team",
    "profile_service": "Customer records team",
    "statements_service": "Statements team",
    "fees_service": "Fees team",
    "business_service": "Business banking operations",
    "case_journal": "Case review team",
    "portal_delivery": "Secure portal team",
}
EMOTIONAL_TEAM = "Customer care (vulnerable customers)"
_URGENCY = ["low", "normal", "high", "urgent"]


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def request_info_reply(question: str) -> str:
    return copy.REQUEST_INFO_REPLY.format(question=question.rstrip("?."))


def _team(data: dict, results) -> str:
    tools = [data.get("tool")] + [_get(r, "tool") for r in reversed(results)]
    for t in tools:
        if t in TEAMS:
            return TEAMS[t]
    return copy.DEFAULT_TEAM


def _list(existing, extra) -> list[str]:
    out = [str(x) for x in (existing or []) if x]
    out += [x for x in extra if x and x not in out]
    return out


def build(data: dict, case, case_object, findings, results, kind: str, why: str = "") -> dict:
    """Fill every field of the handover note, keeping what the model wrote. Keys follow core's loop (#12)."""
    note = dict(data.get("escalation") or {})
    if "team" in note and "who" not in note:
        note["who"] = note.pop("team")
    if "done" in note and "did" not in note:
        note["did"] = note.pop("done")
    note["type"] = "emotional" if kind == "emotional" else (note.get("type") or "technical")
    note["who"] = note.get("who") or (EMOTIONAL_TEAM if note["type"] == "emotional" else _team(data, results))
    note["why"] = note.get("why") or why or (data.get("exception_type") or "the agent could not safely finish this case")

    urgency = note.get("urgency") if note.get("urgency") in _URGENCY else "normal"
    state = _get(case_object, "emotional_state") or {}
    floor = "normal"
    if _get(state, "level") in ("distressed", "vulnerable"):
        floor = "high"
    if any(_get(r, "status") == "uncertain" for r in results):
        floor = "urgent"
    note["urgency"] = max(urgency, floor, key=_URGENCY.index)

    authority = case.authority
    verified = [f"identity {_get(authority, 'identity')} via channel"
                + (f", role {_get(authority, 'role')}" if _get(authority, "role") else "")]
    verified += [f"tool:{_get(r, 'tool')} returned {_get(r, 'data')}" for r in results if _get(r, "status") == "ok"]
    note["verified"] = _list(note.get("verified"), verified)

    claims = _get(case_object, "claims", []) or []
    note["claimed"] = _list(note.get("claimed"), [
        f"{_get(c, 'subject')} {_get(c, 'predicate')} {_get(c, 'value')} ({_get(c, 'source_actor')}, {_get(c, 'event')})"
        for c in claims[:8]])

    conflicts = [f"{_get(f, 'id')} {_get(f, 'kind')}/{_get(f, 'check')}: {_get(f, 'detail')} ({', '.join(_get(f, 'events', []))})"
                 for f in findings]
    for i, c in enumerate(claims):
        for j in _get(c, "conflicts_with", []) or []:
            if i < j < len(claims):
                conflicts.append(f"{_get(c, 'event')} conflicts with {_get(claims[j], 'event')}: "
                                 f"{_get(c, 'value')} vs {_get(claims[j], 'value')}")
    note["conflicts"] = _list(note.get("conflicts"), conflicts)

    note["did"] = _list(note.get("did"), [
        f"tool:{_get(r, 'tool')} {_get(r, 'params')} -> {_get(r, 'status')}" for r in results])

    addressed = set(data.get("asks_addressed") or [])
    not_done = [f"{_get(a, 'id')} not answered: {_get(a, 'text')}" for a in _get(case_object, "asks", []) or []
                if _get(a, "id") not in addressed]
    changed = any(_get(r, "status") == "ok" and _risk(_get(r, "tool"), _get(r, "params")) >= 3 for r in results)
    if not changed:
        not_done.append("no change made to the account")
    note["not_done"] = _list(note.get("not_done"), not_done)

    unknowns = _get(case_object, "unknowns", []) or []
    note["question"] = note.get("question") or case.question or (
        f"Please establish: {unknowns[0]}" if unknowns else f"What is the right next step on case {case.case_id}?")
    note["holding_reply"] = note.get("holding_reply") or copy.HOLDING_REPLY.format(team=_customer_team(note["who"]))
    order = list(copy.HANDOVER_LABELS)
    return {k: note[k] for k in order if k in note} | {k: v for k, v in note.items() if k not in order}


def _risk(tool, params) -> int:
    from agent.llm.exceptions import tool_risk

    return tool_risk(tool, params)


def _customer_team(team: str) -> str:
    return team if team.startswith("the ") else f"our {team[0].lower()}{team[1:]}"


def render(note: Any) -> str:
    """Markdown for ANSWER.md (the writer in core may call this)."""
    lines = [copy.HANDOVER_HEADING, ""]
    for key, label in copy.HANDOVER_LABELS.items():
        value = _get(note, key)
        if isinstance(value, list):
            lines.append(f"**{label}:**")
            lines += [f"- {v}" for v in value] or [f"- {copy.NONE}"]
        else:
            lines.append(f"**{label}:** {value or copy.NONE}")
    return "\n".join(lines) + "\n"
