"""§4.3 mock services. Practice cases: a call is answered from the bank's own journal note in the
hidden later events. Unseen cases: no journal exists, so the result is `pending`, never a fact."""

import re
from typing import Any

from agent.tools._contracts import ToolResult, ToolSpec
from agent.tools.catalogue import service_of

# Which senders of an internal note count as which service (lower-case substrings).
SENDERS: dict[str, list[str]] = {
    "transfer_journal": ["transfer journal", "payment journal", "payment instruction journal", "payment team",
                         "incoming-payment", "incoming-entry", "transaction journal", "instruction journal"],
    "standing_order_journal": ["standing-order", "standing order", "instruction register", "instruction log"],
    "mandate_journal": ["mandate", "direct debit"],
    "card_service": ["card", "access team"],
    "profile_service": ["profile", "access log", "security team", "data team"],
    "statements_service": ["statement", "archive", "data service", "document service"],
    "fees_service": ["tariff", "fee", "request log", "transaction records"],
    "business_service": ["import", "signing", "limit register", "admin process", "acquiring", "business"],
    "case_journal": ["case journal", "case record", "request log"],
    "portal_delivery": ["portal", "document service", "access team"],
}

# §4.3 "Derived from" table: practice cases each service was built from.
CASES: dict[str, set[int]] = {
    "transfer_journal": {*range(1, 11), 40, 48, 50},
    "standing_order_journal": set(range(11, 20)),
    "mandate_journal": {14, 15, 16},
    "card_service": {*range(21, 28), 30},
    "profile_service": {28, 29, 36, 37, 39},
    "statements_service": {31, 32, 33, 38},
    "fees_service": {34, 35},
    "business_service": {*range(41, 48), 49},
}


def _get(obj: Any, key: str, default: Any = "") -> Any:
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def is_journal_note(event: Any) -> bool:
    """An internal note written by a bank system, journal or team, not by the agent handling the case."""
    return _get(event, "channel").strip().lower() == "internal note" and "agent" not in _get(event, "sender").lower()


def _case_number(case_id: str) -> int | None:
    m = re.search(r"\d+", case_id or "")
    return int(m.group()) if m else None


def matches(service: str, event: Any, case_id: str = "") -> bool:
    sender = _get(event, "sender").lower()
    return any(k in sender for k in SENDERS.get(service, [])) or _case_number(case_id) in CASES.get(service, set())


def find_note(service: str, practice_events: list, case_id: str = "") -> Any | None:
    return next((e for e in practice_events if is_journal_note(e) and matches(service, e, case_id)), None)


def note_data(service: str, event: Any) -> dict:
    body = _get(event, "body").strip()
    return {"service": service, "from": _get(event, "sender"), "note": body,
            "lines": [line.strip() for line in body.splitlines() if line.strip()]}


def call(spec: ToolSpec, params: dict, case: Any, practice_events: list) -> ToolResult:
    """One call to the mock service behind `spec`. Raises only when a fault wrapper makes it."""
    service = service_of(spec.name)
    if not practice_events:
        return ToolResult(tool=spec.name, params=params, status="pending",
                          data={"service": service, "detail": "requested, pending result"})
    note = find_note(service, practice_events, _get(case, "case_id"))
    if note is None:
        status = "pending" if spec.risk > 1 else "not_found"
        return ToolResult(tool=spec.name, params=params, status=status, data={"service": service})
    return ToolResult(tool=spec.name, params=params, status="ok", data=note_data(service, note),
                      source_event=_get(note, "id"))
