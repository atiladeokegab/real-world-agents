"""§4.1 ingestor — explicit code, no AI on the fast path.

Parses a case folder exactly as the organisers ship it (index.md + history.md +
optional attachments/) into the shared `Case` contract. Authority is derived here
from channel metadata; the model can never raise it.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from agent.core.contracts import Authority, Case, Event
from agent.ingest.attachments import read_attachments
from agent.ingest.fallback import fallback_events

_ANCHOR_RE = re.compile(r'<a id="(event-\d+)"></a>')
_HEADER_RE = re.compile(r"\s*##\s*(?P<at>.+?)\s*—\s*event\s*\d+\s*\n")
_FIELD_RE = re.compile(r"-\s*\*\*(?P<key>[^*]+):\*\*\s*(?P<value>.+)")
_TS_FORMAT = "%Y-%m-%d %H:%M:%S UTC"

_BANK_SIDE_RE = re.compile(r"^(?:H&V\b|Harrow & Vale)")

# §4.1: authority comes from the channel, never the model.
_CHANNEL_IDENTITY = {
    "verified call": "verified",
    "secure portal": "authenticated",
    "secure chat": "authenticated",
    "business portal": "authenticated",
}

# In practice mode the agreed answer is stripped so it can never leak into the input.
_HIDDEN_SECTIONS = ("Overview", "Next action at escalation", "Outcome")
_HIDDEN_MARK = "[hidden in practice mode]"

_TRACK_ALIASES = {"examples": "Banking & Financial Services"}


def load_case(path, cut: int | None = None, question: str | None = None) -> Case:
    """Load one case folder into a `Case`. Never raises on unparseable input."""
    path = Path(path)
    index = _read(path / "index.md")
    history = _read(path / "history.md")

    parsed = _parse_events(history)
    attachments = read_attachments(path)
    details = _details(index)

    raw_files = {"index.md": index, "history.md": history}
    unknown = [
        e.name
        for e in sorted(path.iterdir())
        if e.is_file() and e.name not in raw_files and not e.name.startswith(".")
    ]
    for name in unknown:
        raw_files[name] = _read(path / name)  # unknown files read as text
    for a in attachments:
        raw_files[f"attachments/{a.name}"] = a.text

    if cut is not None:
        # strip before any fallback prompt so the agreed answer can't leak in
        raw_files["index.md"] = _strip_sections(index)
        raw_files["history.md"] = _truncate_history(history, cut)

    if not parsed:
        # regex found nothing — one structured() call over everything received
        events = _renumbered(fallback_events(raw_files))
    else:
        events = parsed
        if unknown:
            # unrecognised files: one structured() call on them alone, appended —
            # a stray file can never replace or poison the parsed events
            extra = _renumbered(
                fallback_events({n: raw_files[n] for n in unknown}), start=len(events) + 1
            )
            events = events + extra

    if cut is not None:
        events = [e for e in events if _event_number(e.id) <= cut]
        parsed = [e for e in parsed if _event_number(e.id) <= cut]

    return Case(
        track=_TRACK_ALIASES.get(path.parent.name, path.parent.name),
        case_id=path.name,
        title=_title(index),
        source_role=details.get("Source role", ""),
        created=_parse_ts(details.get("Created")),
        initial_request=_section(index, "Initial request"),
        events=events,
        attachments=attachments,
        # authority reads only the regex-parsed events; the model can never raise it
        authority=_authority(_first_inbound(parsed), details.get("Source role", "")),
        raw_files=raw_files,
        question=question,
    )


def _renumbered(events: list[Event], start: int = 1) -> list[Event]:
    for i, e in enumerate(events, start):
        e.id = f"event-{i:03d}"
    return events


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_events(history: str) -> list[Event]:
    """Split history.md on its anchors; the format is machine-generated and uniform."""
    parts = _ANCHOR_RE.split(history)
    events = []
    for eid, block in zip(parts[1::2], parts[2::2]):
        header = _HEADER_RE.match(block)
        rest = block[header.end():].lstrip("\n") if header else block
        field_text, sep, body = rest.partition("\n\n")
        if "- **" not in field_text:
            field_text, body = "", rest
        fields = {m.group("key").strip(): m.group("value").strip() for m in _FIELD_RE.finditer(field_text)}
        events.append(
            Event(
                id=eid,
                at=(_parse_ts(header.group("at")) or _EPOCH) if header else _EPOCH,
                channel=fields.get("Channel", ""),
                sender=fields.get("From", ""),
                recipient=fields.get("To", ""),
                body=body.strip(),
            )
        )
    return events


_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _parse_ts(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        return datetime.strptime(text.strip(), _TS_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        return _EPOCH  # never crash on a bad date


def _event_number(event_id: str) -> int:
    try:
        return int(event_id.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def _details(index: str) -> dict[str, str]:
    block = _section(index, "Case details")
    return {m.group("key").strip(): m.group("value").strip() for m in _FIELD_RE.finditer(block)}


def _title(index: str) -> str:
    m = re.search(r"^#\s*(?:Case\s+\d+:\s*)?(?P<title>.+)$", index, re.M)
    return m.group("title").strip() if m else ""


def _section(text: str, name: str) -> str:
    m = re.search(
        rf"^##\s+{re.escape(name)}\s*\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
        re.S | re.M,
    )
    return m.group("body").strip() if m else ""


def _strip_sections(index: str) -> str:
    for name in _HIDDEN_SECTIONS:
        index = re.sub(
            rf"(^##\s+{re.escape(name)}\s*\n).*?(?=^##\s|\Z)",
            rf"\1\n{_HIDDEN_MARK}\n\n",
            index,
            flags=re.S | re.M,
        )
    return index


def _truncate_history(history: str, cut: int) -> str:
    for m in _ANCHOR_RE.finditer(history):
        if _event_number(m.group(1)) > cut:
            return history[: m.start()]
    return history


def _first_inbound(events: list[Event]) -> Event | None:
    """The request event: first event to the bank on a customer-facing channel."""
    for e in events:
        if e.channel.lower() == "internal note":
            continue
        if _BANK_SIDE_RE.match(e.recipient) and not _BANK_SIDE_RE.match(e.sender):
            return e
    return None


def _authority(request: Event | None, source_role: str) -> Authority:
    if request is None:
        return Authority(identity="unverified", role=source_role or None)
    identity = _CHANNEL_IDENTITY.get(request.channel.lower(), "unverified")
    role = source_role or None
    # §4.1: on Business portal the sender carries the role — "Mara Ellison, authorised file uploader".
    if request.channel.lower() == "business portal" and "," in request.sender:
        role = request.sender.rsplit(",", 1)[1].strip() or role
    return Authority(identity=identity, role=role)
