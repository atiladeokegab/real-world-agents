"""§4.1 fallback parse — exactly one Claude call when explicit parsing can't.

Triggered when regex parsing yields zero events or the folder contains files we
don't recognise. The ingestor never crashes on input it can't parse: every
failure path degrades to an empty event list.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from agent.core.contracts import Event

_KNOWN_NAMES = {"index.md", "history.md", "attachments"}

_SYSTEM = (
    "You are structuring a bank case folder into events. Return every message, note "
    "and record you can find, in time order, as Event objects: id (event-001, "
    "event-002, ...), at (ISO 8601 datetime), channel, sender, recipient, body. "
    "Invent nothing; where a field is missing use an empty string."
)


class _EventList(BaseModel):
    events: list[Event] = []


def needs_fallback(case_dir: Path, events: list[Event]) -> bool:
    if not events:
        return True
    return any(p.name not in _KNOWN_NAMES for p in Path(case_dir).iterdir())


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
