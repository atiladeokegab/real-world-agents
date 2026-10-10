"""§4.2 evidence checker — explicit code, no AI.

Runs between the ingestor and extraction; emits typed `Finding`s with the event
ids they rest on. The decision must address every finding, so a check only fires
on explicit textual evidence — precision over recall.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import date, timedelta

import dateutil.parser

from agent.core.contracts import Attachment, Case, Event, Finding

_BANK_SIDE_RE = re.compile(r"^(?:H&V\b|Harrow & Vale)")
# Service-looking senders are bank-side on internal channels; on External message
# they are third parties (a company name can end in "...Services").
_SERVICE_RE = re.compile(
    r"(?i)\b(service|journal|system|register|record|log|process|portal|team|agent|support|admin|bank)\b"
)
_PERSON_CHANNELS = {"secure chat", "verified call", "external message", "business portal"}

_AMOUNT_RE = re.compile(r"£\s?(\d[\d,]*(?:\.\d{2})?)")
_PAYEE_RE = re.compile(
    r"(?i:\b(?:to|payee|paying|paid|sent to|transfer(?:red)? to|payment to|charge by|debit for))\s+"
    r"([A-Z][\w&'.-]+(?:\s+(?:[A-Z][\w&'.-]+|of|the|and|&)){0,4})"
)
_PAYEE_STOP = {"the", "a", "an", "your", "my", "our", "this", "that", "you", "i", "we", "it", "h&v", "harrow"}
_TOTAL_RE = re.compile(r"(?i)\btotal\b[^£\n]{0,40}£\s?(\d[\d,]*(?:\.\d{2})?)")
_DUP_WORDS_RE = re.compile(
    r"(?i)\b(duplicat\w*|twice|two\s+(?:similar|separate|distinct|identical)|double(?:d)?|same\s+\w+\s+twice)\b"
)
_PAYMENT_NOUN_RE = re.compile(
    r"(?i)\b(transfer|payment|instruction|entry|entries|line|debit|charge|standing order|direct debit|transaction)\b"
)
_COLLECTION_STATUS_RE = re.compile(
    r"(?i)\b(batch|file|payroll|bulk|group|set)\b[^.\n]{0,60}?\b"
    r"(processed|completed?|paid|sent|approved|rejected|posted|released|successful|failed)\b"
    r"|\b(?:batch|file|payroll|bulk|group|set)\s+status\s*[:=]?\s*\w+"
)
_MEMBER_RE = re.compile(r"(?i)\b(row|line|entry|item|record)\s*(?:[A-Z]{1,4}-?\d+|’s status|'s status|status)\b")
_MEMBER_BAD_RE = re.compile(
    r"(?i)\b(rejected|failed|unpaid|pending|unclear|not paid|can(?:not|['’]t) tell|whether|different|missing)\b"
)
_LIMIT_RE = re.compile(
    r"(?i)\b(?:limit|maximum|max(?:imum)?|cap|ceiling)\b[^£\n]{0,50}?£\s?(\d[\d,]*(?:\.\d{2})?)"
)
_REQUEST_AMOUNT_RE = re.compile(
    r"(?i)\b(?:send|pay|transfer|release|arrange|make|increase|change|set|raise)\b[^£\n]{0,40}£\s?(\d[\d,]*(?:\.\d{2})?)"
)
_CUTOFF_WORD_RE = re.compile(r"(?i)\b(?:cut-?off|deadline)\b")
_CLOCK_RE = re.compile(r"(?i)\b(\d{1,2})(?::(\d{2})\s*(am|pm)?|\s*(am|pm)\b)")
_ROLE_DISCLAIM_RE = re.compile(
    r"(?i)\b(?:i(?:['’]m| am) not (?:the |an? )?[\w\s]*?(?:administrator|admin|signatory|approver)|"
    r"not (?:authoris|authoriz)ed|i can(?:['’]|no)t (?:approve|authorise|authorize|sign|release)|"
    r"(?:do|does) not have (?:the )?(?:authority|permission|mandate)|not allowed to approve)\b"
)
_HOLDER_RE = re.compile(
    r"(?im)^\s*(?:account holder|account name|customer name|registered to|issued to|prepared for)\s*[::]\s*"
    r"([A-Z][a-zA-Z'\-]+(?:[ \t]+[A-Z][a-zA-Z'\-]+){1,3})"
)
_HOLDER_STOP = {"the", "a", "an", "your", "my", "our", "and", "of", "not", "no", "none"}
_ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_LONG_DATE_RE = re.compile(
    r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{4})\b"
)
_DONE_BEFORE_DATE_RE = re.compile(
    r"(?i)\b(?:was|were|been|marked|recorded as|shown as)\s+(?:[\w-]+\s+){0,3}?"
    r"(sent|processed|completed?|paid|debited|posted|executed|taken|deducted|collected|transferred)\b"
    r"[^.\n]{0,30}?(\d{4}-\d{2}-\d{2}|\d{1,2}\s+(?:January|February|March|April|May|June|July|"
    r"August|September|October|November|December)\s+\d{4})"
)
_DUE_RE = re.compile(
    r"(?i)\b(?:due|deadline|expires?)\b[^.\n]{0,30}?"
    r"(\d{4}-\d{2}-\d{2}|\d{1,2}\s+(?:January|February|March|April|May|June|July|"
    r"August|September|October|November|December)\s+\d{4})"
)


def _money(raw: str) -> float:
    return float(raw.replace(",", "").lstrip("£").strip())


def _parse_day(raw: str) -> date | None:
    try:
        return dateutil.parser.parse(raw, dayfirst=True).date()
    except (ValueError, OverflowError):
        return None


def _bank_side(name: str) -> bool:
    return bool(_BANK_SIDE_RE.match(name.strip()))


def _inbound_person_events(case: Case) -> list[Event]:
    """Events a person sent to the bank on a customer-facing channel."""
    out = []
    for e in case.events:
        if e.channel.lower() == "internal note":
            continue
        if not (_bank_side(e.recipient) and not _bank_side(e.sender)):
            continue
        if e.channel.lower() != "external message" and _SERVICE_RE.search(e.sender):
            continue  # service senders are bank-side off the external channel
        if e.channel.lower() not in _PERSON_CHANNELS:
            continue
        out.append(e)
    return out


def _norm_name(sender: str) -> str:
    return sender.split(",")[0].strip().lower()


def _payee_spans(text: str) -> list[str]:
    spans = []
    for m in _PAYEE_RE.finditer(text):
        span = m.group(1).strip().rstrip(".,;:!?")
        span = re.sub(r"\s+(?:of|the|and|&)$", "", span, flags=re.I)
        words = span.lower().split()
        if words and words[0] in _PAYEE_STOP:
            continue
        if len(span) >= 3:
            spans.append(" ".join(words))
    return spans


def _csv_expected_total(attachment: Attachment) -> float | None:
    """The total a csv attachment implies: a total-named column, or one numeric column's sum."""
    try:
        rows = [r for r in csv.reader(io.StringIO(attachment.text)) if r]
    except csv.Error:
        return None
    if len(rows) < 2:
        return None
    header = [h.strip().lower() for h in rows[0]]
    totals_idx = [i for i, h in enumerate(header) if "total" in h]
    amount_idx = [i for i, h in enumerate(header)
                  if re.search(r"amount|gbp|value|fee|debit|credit|balance|price", h)]
    id_like = re.compile(r"^(row|row_?id|id|index|no\.?|#|num(?:ber)?|line|seq)\b", re.I)
    numeric_idx = []
    for i in range(len(header)):
        if id_like.search(header[i]):
            continue
        try:
            vals = [float(r[i]) for r in rows[1:] if len(r) > i and r[i].strip()]
        except ValueError:
            continue
        if vals:
            numeric_idx.append((i, vals))
    if totals_idx:
        for r in reversed(rows[1:]):
            if len(r) > totals_idx[0] and r[totals_idx[0]].strip():
                try:
                    return float(r[totals_idx[0]])
                except ValueError:
                    continue
        return None
    if amount_idx:
        cols = [c for c in numeric_idx if c[0] in amount_idx]
        if cols:
            return sum(cols[0][1])
    if len(numeric_idx) == 1:
        return sum(numeric_idx[0][1])
    return None


def _check_amounts(case: Case) -> list[Finding]:
    findings = []
    quoted: dict[str, dict[str, set[str]]] = {}
    for e in case.events:
        for payee in _payee_spans(e.body):
            for raw in _AMOUNT_RE.findall(e.body):
                quoted.setdefault(payee, {}).setdefault(f"{_money(raw):.2f}", set()).add(e.id)
    for payee, amounts in quoted.items():
        if len(amounts) > 1:
            ids = sorted({i for ids in amounts.values() for i in ids})
            findings.append(
                Finding(id="", kind="conflict", check="amounts",
                        detail=f"the same payee '{payee}' is quoted with different amounts: "
                               + ", ".join(sorted(amounts)),
                        events=ids)
            )

    expectations = [(a.name, t) for a in case.attachments
                    if a.kind == "csv" and (t := _csv_expected_total(a)) is not None]
    stated = [(e.id, _money(m)) for e in case.events for m in _TOTAL_RE.findall(e.body)]
    stated += [(f"attachment:{a.name}", _money(m)) for a in case.attachments
               for m in _TOTAL_RE.findall(a.text)]
    for name, expected in expectations:
        for src, value in stated:
            if abs(value - expected) > 0.005:
                findings.append(
                    Finding(id="", kind="conflict", check="amounts",
                            detail=f"stated total £{value:,.2f} ({src}) does not match the "
                                   f"£{expected:,.2f} implied by {name}",
                            events=[src] if src.startswith("event-") else [])
                )
    return findings


def _check_identity(case: Case) -> list[Finding]:
    findings = []
    inbound = _inbound_person_events(case)
    request_event = inbound[0] if inbound else None
    requester = _norm_name(request_event.sender) if request_event else None

    for a in case.attachments:
        for holder in _HOLDER_RE.findall(a.text):
            if holder.split()[0].lower() in _HOLDER_STOP:
                continue
            if requester and holder.strip().lower() != requester:
                detail = (f"{a.name} names '{holder}' while the requester is "
                          f"'{request_event.sender.split(',')[0]}'")
                findings.append(Finding(id="", kind="anomaly", check="identity",
                                        detail=detail, events=[request_event.id]))

    for e in inbound:
        if _ROLE_DISCLAIM_RE.search(e.body):
            findings.append(
                Finding(id="", kind="anomaly", check="identity",
                        detail="the requester says they lack the role for what they ask",
                        events=[e.id])
            )

    senders = {_norm_name(e.sender): e.id for e in inbound}
    if len(senders) > 1:
        findings.append(
            Finding(id="", kind="anomaly", check="identity",
                    detail="more than one person writes to the bank on this case: "
                           + ", ".join(sorted(senders)),
                    events=list(senders.values()))
        )
    return findings


def _check_time(case: Case) -> list[Finding]:
    findings = []
    for prev, cur in zip(case.events, case.events[1:]):
        if cur.at < prev.at:
            findings.append(
                Finding(id="", kind="anomaly", check="time",
                        detail=f"{cur.id} is timestamped before {prev.id}", events=[prev.id, cur.id])
            )
    for e in case.events:
        for m in _DONE_BEFORE_DATE_RE.finditer(e.body):
            day = _parse_day(m.group(2))
            if day and day > e.at.date() + timedelta(days=1):
                findings.append(
                    Finding(id="", kind="anomaly", check="time",
                            detail=f"{e.id} reports '{m.group(1)}' dated {day}, after the event itself",
                            events=[e.id])
                )
    if case.created:
        for e in case.events:
            for m in _DUE_RE.finditer(e.body):
                day = _parse_day(m.group(1))
                if day and day < case.created.date():
                    findings.append(
                        Finding(id="", kind="anomaly", check="time",
                                detail=f"{e.id} mentions a due/deadline date already past: {day}",
                                events=[e.id])
                    )
    return findings


def _check_duplicates(case: Case) -> list[Finding]:
    # Only the text describing a possible duplicate fires: two events restating
    # the same payee+amount is usually one transaction discussed twice, not two.
    flagged = [e.id for e in case.events
               if _DUP_WORDS_RE.search(e.body) and _PAYMENT_NOUN_RE.search(e.body)]
    if flagged:
        return [
            Finding(id="", kind="anomaly", check="duplicates",
                    detail="the case text describes a possible duplicate payment/instruction",
                    events=flagged)
        ]
    return []


def _check_status(case: Case) -> list[Finding]:
    collections = [e.id for e in case.events if _COLLECTION_STATUS_RE.search(e.body)]
    members = [e.id for e in case.events
               if _MEMBER_RE.search(e.body) and _MEMBER_BAD_RE.search(e.body)]
    if collections and members:
        return [
            Finding(id="", kind="anomaly", check="status",
                    detail="a collection-level status is asserted while a member line's "
                           "status is unclear or contradicts it",
                    events=collections[:1] + members)
        ]
    return []


def _check_limits(case: Case) -> list[Finding]:
    findings = []
    stated = [(e.id, _money(m)) for e in case.events for m in _LIMIT_RE.findall(e.body)]
    stated += [(f"attachment:{a.name}", _money(m)) for a in case.attachments
               for m in _LIMIT_RE.findall(a.text)]
    asked = [(e.id, _money(m)) for e in case.events for m in _REQUEST_AMOUNT_RE.findall(e.body)]
    for limit_src, limit in stated:
        for ask_src, amount in asked:
            if amount > limit:
                ids = sorted({s for s in (limit_src, ask_src) if s.startswith("event-")})
                findings.append(
                    Finding(id="", kind="anomaly", check="limits",
                            detail=f"a £{amount:,.2f} action is asked against a stated "
                                   f"£{limit:,.2f} limit ({limit_src})",
                            events=ids)
                )

    for e in case.events:
        for m in _CUTOFF_WORD_RE.finditer(e.body):
            window = e.body[max(0, m.start() - 40): m.end() + 40]
            for t in _CLOCK_RE.finditer(window):
                meridiem = t.group(3) or t.group(4)
                hour = int(t.group(1))
                if meridiem:
                    hour = hour % 12 + (12 if meridiem.lower() == "pm" else 0)
                minute = int(t.group(2) or 0)
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    continue
                for other in case.events:
                    if other.id != e.id and other.at.date() == e.at.date() and (
                        other.at.hour, other.at.minute
                    ) > (hour, minute):
                        findings.append(
                            Finding(id="", kind="anomaly", check="limits",
                                    detail=f"activity on {other.id} sits after the cut-off stated in {e.id}",
                                    events=[e.id, other.id])
                        )
    return findings


_CHECKS = (_check_amounts, _check_identity, _check_time, _check_duplicates, _check_status, _check_limits)


def find_evidence(case: Case) -> list[Finding]:
    """Every typed finding the deterministic checks raise, ids renumbered in order."""
    findings = [f for check in _CHECKS for f in check(case)]
    for i, f in enumerate(findings, start=1):
        f.id = f"finding-{i}"
    return findings
