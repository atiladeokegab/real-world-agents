"""§4.1 fallback parse — exactly one Claude call when explicit parsing can't.

Called by the ingestor when regex parsing yields zero events (on everything
received) or when the folder contains files it doesn't recognise (on those files
alone, appended — never replacing parsed events). Every failure path degrades to
an empty event list: the ingestor never crashes on input it can't parse.
"""

from __future__ import annotations

from pydantic import BaseModel

from agent.core.contracts import Event

_SYSTEM = (
    "You are structuring a bank case folder into events. Return every message, note "
    "and record you can find, in time order, as Event objects: id (event-001, "
    "event-002, ...), at (ISO 8601 datetime), channel, sender, recipient, body. "
    "Invent nothing; where a field is missing use an empty string."
)


class _EventList(BaseModel):
    events: list[Event] = []


def fallback_events(raw_files: dict[str, str]) -> list[Event]:
    try:
        from agent.core.llm import structured
    except ImportError:
        return []

    user = "\n\n".join(f"=== {name} ===\n{text}" for name, text in sorted(raw_files.items()))
    try:
        result = structured(stage="extraction", system=_SYSTEM, user=user, model=_EventList)
    except Exception:
        return []
    return list(result.events)
