import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent.tools._contracts import Case, Event

EXAMPLES = Path(__file__).parents[2] / "examples"
BLOCK = re.compile(r'<a id="(event-\d+)"></a>\s*## (.+?) UTC — event \d+\s*\n(.*?)(?=<a id="event-|\Z)', re.S)


def events_of(num: str) -> list[Event]:
    out = []
    for eid, at, rest in BLOCK.findall((EXAMPLES / num / "history.md").read_text(encoding="utf-8")):
        fields = dict(re.findall(r"- \*\*(.+?):\*\* (.*)", rest))
        out.append(Event(id=eid, at=datetime.strptime(at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
                         channel=fields.get("Channel", ""), sender=fields.get("From", ""),
                         recipient=fields.get("To", ""), body=rest.split("\n\n", 1)[-1].strip()))
    return out


def practice(num: str, cut: int | None = None) -> tuple[Case, list[Event]]:
    """The case cut before the agent's first internal note, and the hidden later events."""
    evs = events_of(num)
    if cut is None:
        cut = next((i for i, e in enumerate(evs) if e.channel == "Internal note" and "agent" in e.sender.lower()),
                   max(1, len(evs) - 2))
    case = Case(track="Banking & Financial Services", case_id=num, title=num, source_role="Bank customer",
                initial_request="", events=evs[:cut])
    return case, evs[cut:]


@pytest.fixture
def load():
    return practice
