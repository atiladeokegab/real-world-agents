"""§4.6 verifier — explicit code, no AI.

The deterministic safety layer every proposal passes before anything runs.
Rules are evaluated in a fixed order; the first failure is returned naming
the exact rule, field and event so the one permitted retry (§12 [AD]) is
told where the error is. `ok=True` only when every applicable rule passes.
"""

from __future__ import annotations

import re

import dateutil.parser

from agent.core.contracts import (
    Case,
    CaseObject,
    Constraint,
    Finding,
    Proposal,
    ToolResult,
    Verdict,
)

# --- atoms the claim linter extracts from reply.text ---

_AMOUNT_RE = re.compile(r"£\s*(\d[\d,]*(?:\.\d{1,2})?)")
_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|"
    "November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
_DATE_RE = re.compile(
    rf"\b\d{{1,2}}\s+(?:{_MONTHS})\.?\s+\d{{4}}\b"                      # 19 July 2025
    rf"|\b(?:{_MONTHS})\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b"   # July 19, 2025
    r"|\b\d{4}-\d{2}-\d{2}\b"                                          # 2025-07-19
    r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b",                                   # 19/07/2025
    re.IGNORECASE,
)
# a token mixing letters and digits: SUP-17, REF-2024-081, dev-9F31AB
_REF_RE = re.compile(r"\b(?=[\w-]*[A-Za-z])(?=[\w-]*\d)[A-Za-z0-9][\w-]{2,}\b")
_NAME_SPAN_RE = re.compile(r"[A-Z][\w'&.-]*(?:\s+[A-Z][\w'&.-]*)+")
_CAP_WORD_RE = re.compile(r"[A-Z][\w'&.-]*")
# a ". " inside a span is a sentence end after a lower-case word ending in
# 3+ letters ("sent. Your") or an upper/digit token ("H&V. We", "SENT. You",
# "PIN. That") — abbreviations (St., Mr., Dr.) stay together; a newline
# always ends the span
_SENT_END_IN_SPAN_RE = re.compile(
    r"(?<=[a-z]{3})\.\s+(?=[A-Z])"
    r"|(?<=[A-Z0-9&'])\.\s+(?=[A-Z])"
    r"|\n+"
)
# possessive tail: "Northmere Studio Ltd's" -> "Northmere Studio Ltd"
_POSSESSIVE_RE = re.compile(r"(?i)'s\b")
# a leading "The" folds into phrase allow-list entries
_THE_RE = re.compile(r"(?i)^the\s+")

_WORD_STOP = {
    # function words that may be capitalised mid-sentence
    "a", "an", "the", "you", "your", "yours", "we", "our", "ours", "my", "mine",
    "he", "she", "it", "its", "they", "their", "this", "that", "these", "those",
    "there", "here", "who", "what", "which", "when", "where", "how", "why",
    "if", "then", "so", "as", "of", "at", "by", "for", "with", "about",
    "into", "through", "during", "before", "after", "above", "below", "to",
    "from", "up", "down", "in", "out", "on", "off", "over", "under", "again",
    "once", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "shall", "should", "can",
    "could", "may", "might", "must", "not", "no", "yes", "and", "or", "but",
    "per", "via", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "only", "own", "same", "than", "too", "very", "just",
    "now", "also", "still", "even", "new", "next", "last", "first",
    # months / weekdays / time words
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "jan", "feb", "mar",
    "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "mon", "tue", "tues", "wed", "thu", "thur", "thurs", "fri",
    "sat", "sun", "today", "tomorrow", "yesterday", "utc", "gmt", "bst",
    # greetings and sign-offs
    "dear", "hello", "hi", "hey", "thank", "thanks", "please", "regards",
    "best", "kind", "sincerely", "faithfully", "good", "morning",
    "afternoon", "evening", "welcome", "sorry", "ok", "okay",
    # banking boilerplate and channel names used as single words
    "account", "accounts", "payment", "payments", "transfer", "transfers",
    "balance", "statement", "statements", "amount", "amounts", "fee", "fees",
    "charge", "charges", "credit", "debit", "date", "time", "number", "sort",
    "code", "reference", "ref", "id", "name", "subject", "note", "notes",
    "bank", "banking", "customer", "case", "agent", "team", "support",
    "service", "services", "portal", "chat", "email", "phone", "call",
    "message", "letter", "form", "request", "requests", "reply", "response",
    "question", "answer", "result", "results", "check", "checks",
    "transaction", "transactions", "invoice", "receipt", "refund", "claim",
    "claims", "secure", "verified", "external", "internal", "business",
    "online", "mobile", "app", "web", "direct", "standing", "order",
    "orders", "gbp", "eur", "usd", "currency", "total", "subtotal", "vat",
    "tax", "batch", "journal", "session", "device", "devices",
    # titles and organisations' legal suffixes
    "mr", "mrs", "ms", "miss", "dr", "prof", "sir", "dame", "madam",
    "ltd", "plc", "llc", "inc", "co", "uk", "eu", "us", "re", "fw", "fwd",
    "cc", "bcc", "ps", "etc",
    # pronouns and product words the linter must never call a name
    "i", "i'm", "i've", "i'll", "i'd", "me",
    "we're", "we've", "we'll", "we'd",
    "you're", "you've", "you'll", "you'd",
    "he's", "she's", "it's", "they're", "they've", "they'll",
    "profile", "pin",
}
_PHRASE_STOP_RAW = {
    "secure chat", "verified call", "external message", "business portal",
    "internal note", "sort code", "account number", "account holder",
    "direct debit", "standing order", "good morning", "good afternoon",
    "good evening", "kind regards", "best regards", "thank you",
    "yours sincerely", "yours faithfully", "dear sir", "dear madam",
    "customer service", "customer services", "online banking", "mobile app",
    "terms and conditions", "bank customer", "authorised business user",
    "case journal", "h&v", "h&v agent", "h&v bank", "h&v team",
    "harrow & vale", "harrow and vale",
    # the bank's own names and product words, seen capitalised in replies
    "vale bank", "h&v bank plc",
    "harrow & vale bank", "harrow and vale bank",
    "harrow & vale bank plc", "harrow and vale bank plc",
    "direct debits", "standing orders",
    "secure portal", "pin number", "personal profile",
}

# --- no fabricated execution ---

_DONE_RE = re.compile(
    r"(?i)\b(sent|processed|completed?|paid|cancelled|canceled|refunded|"
    r"transferred|released|debited|credited|posted|executed|charged|"
    r"confirmed|updated|amended|changed|deleted|removed|added|downloaded|"
    r"uploaded|submitted|approved|rejected|issued|activated|blocked|frozen|"
    r"closed|opened|checked|verified|reviewed|done|stopped|returned|"
    r"reversed|applied|taken|deducted|collected|declined|failed|unpaid|"
    r"unprocessed|uncancelled)\b"
)
# negators/hedges that turn "was sent" into "was not sent" / "still pending",
# and conditionals that make a done-word describe a future event, not a claim:
# "once it has been changed", "until we have verified", "when it is sent"
_NEGATION_RE = re.compile(
    r"(?i)\b(not|n't|never|no|without|cannot|can't|unable|pending|awaiting|"
    r"will|would|could|should|may|might|due|yet|once|until|when|whenever|"
    r"if)\b"
)
_AFTER_HEDGE_RE = re.compile(r"(?i)^\s*(?:yet|until|still pending)\b")

# --- material conflict ---

_LOOKUP_NAME_RE = re.compile(
    r"(?i)lookup|look_?up|check|fetch|read|query|search|statement|balance|"
    r"history|status|detail|verify|inspect|journal|service|list|find|get"
)

# --- disclosure ---

_DISCLOSURE_RE = re.compile(
    r"\b\d{2}-\d{2}-\d{2}\b"                                              # sort code
    r"|\b\d{8,}\b"                                                       # full account number
    r"|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"  # uuid
    r"|\bdevice[-_ ]?id\b\s*[:=#]?\s*[\"']?[\w-]+"                        # labelled device id
    r"|\bdev(?:ice)?[-_][\w-]{3,}\b"                                      # dev-/device- token
    r"|\b[0-9a-f]{16,}\b",                                                # long hex id
    re.IGNORECASE,
)

_FILLER_RE = re.compile(
    r"^(?:by|via|over|on|through|using|use|send|reply|respond|contact|"
    r"any|the|your|a|an)\b\s*"
)
_TITLE_RE = re.compile(r"(?i)\b(?:mr|mrs|ms|miss|dr|prof|sir|dame|mx)\b\.?")


def _fail(rule: str, field=None, event=None, message="") -> Verdict:
    return Verdict(ok=False, rule=rule, field=field, event=event, message=message)


def _catalogue() -> dict:
    """The tool catalogue, resolved lazily — agent.tools lands in a later PR;
    until then an empty catalogue rejects every tool_call."""
    try:
        from agent.tools import CATALOGUE
    except (ImportError, AttributeError):
        return {}
    return dict(CATALOGUE or {})


def _iso(raw: str) -> str | None:
    try:
        return dateutil.parser.parse(raw, dayfirst=True).date().isoformat()
    except (ValueError, OverflowError):
        return None


def _norm(text: str) -> str:
    """Lowercase, fold thousand-separators and dates to ISO, drop punctuation."""
    s = text.lower()
    s = re.sub(r"(?<=\d),(?=\d)", "", s)  # 1,250.00 -> 1250.00
    s = _DATE_RE.sub(lambda m: _iso(m.group(0)) or m.group(0), s)
    s = re.sub(r"[£$€&]", " ", s)
    s = re.sub(r"\band\b", " ", s)
    s = re.sub(r"[^\w\s.-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


_WORD_STOP = {_norm(w) for w in _WORD_STOP}
_PHRASE_STOP = {_norm(p) for p in _PHRASE_STOP_RAW}
# words that may open a capitalised span without making it a name:
# function words, greetings and pronoun contractions — titles stay, so
# "Dear Ms Shah" still lints as "Ms Shah" against the requester
_LEAD_STOP = (_WORD_STOP - {_norm(t) for t in
                            ("mr mrs ms miss dr prof sir dame madam mx").split()}) | {
    _norm(w) for w in (
        "i i'm i've i'll i'd me you're you've you'll you'd "
        "we're we've we'll we'd he's she's it's they're they've they'll"
    ).split()
}


def _flatten(obj) -> str:
    if isinstance(obj, dict):
        return " ".join(_flatten(k) + " " + _flatten(v) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return " ".join(_flatten(x) for x in obj)
    return str(obj)


def _haystack(case_object: CaseObject, results: list[ToolResult]) -> str:
    """The evidence a reply may cite: the requester's name, every claim's
    text, plus every result's data."""
    parts = []
    req = getattr(case_object, "requester", None)
    if req is not None:
        parts.append(req.get("name", "") if isinstance(req, dict)
                     else getattr(req, "name", "") or "")
    for c in case_object.claims:
        parts.extend([c.subject, c.predicate, c.value])
    for r in results:
        parts.append(_flatten(r.data))
    return _norm(" ".join(parts))


def _reply_atoms(text: str) -> list[tuple[str, str]]:
    """(kind, raw) atoms in reply.text that must be evidenced elsewhere."""
    atoms: list[tuple[str, str]] = []
    claimed: list[tuple[int, int]] = []  # char spans already taken by extractors
    for m in _AMOUNT_RE.finditer(text):
        atoms.append(("amount", m.group(1)))
        claimed.append(m.span())
    for m in _DATE_RE.finditer(text):
        atoms.append(("date", m.group(0)))
        claimed.append(m.span())
    for m in _REF_RE.finditer(text):
        atoms.append(("reference", m.group(0)))
        claimed.append(m.span())
    for m in _NAME_SPAN_RE.finditer(text):
        if any(m.start() < e and m.end() > s for s, e in claimed):
            continue  # the span sits inside a date/amount/reference match
        claimed.append(m.span())
        # a capital at a sentence start proves nothing — drop that first word
        at_boundary = not text[:m.start()].strip() or bool(
            re.search(r"[.!?:]\s*$|\n\s*$", text[:m.start()]))
        for i, frag in enumerate(_SENT_END_IN_SPAN_RE.split(m.group(0))):
            words = frag.strip(" .,;:!?\"'").split()
            if words and (i > 0 or at_boundary):
                words = words[1:]  # split frags always start a new sentence
            while words and _norm(words[0]) in _LEAD_STOP:
                words = words[1:]  # greetings, titles, pronouns, stop words
            frag = " ".join(words)
            if len(words) >= 2 and _norm(frag) not in _PHRASE_STOP \
                    and _norm(_THE_RE.sub("", frag)) not in _PHRASE_STOP:
                atoms.append(("name", frag))
    for m in _CAP_WORD_RE.finditer(text):
        if any(m.start() >= s and m.end() <= e for s, e in claimed):
            continue  # part of a span or another atom already
        prev = text[:m.start()].rstrip()
        if not prev or prev[-1] in ".!?\n":
            continue  # sentence start — capitalisation proves nothing
        word = m.group(0).rstrip(".")
        if len(word) <= 2 or word.isupper():
            continue  # too short to pin down, or an acronym
        if _norm(word) in _WORD_STOP:
            continue
        atoms.append(("name", word))
    return atoms


def _atom_variants(kind: str, raw: str) -> set[str]:
    base = _norm(raw)
    variants = {base}
    if kind == "amount":
        if "." in base:
            variants.add(base.split(".", 1)[0])
        if base.endswith(".00"):
            variants.add(base[:-3])
    elif kind == "name":
        variants.add(_norm(_TITLE_RE.sub("", raw)))  # "Ms Ellison" -> "Ellison"
        variants.add(_norm(raw.replace("-", " ").replace("'", " ").replace(".", " ")))
        variants.add(_norm(_POSSESSIVE_RE.sub("", raw)))  # "Ltd's" -> "Ltd"
    elif kind == "reference":
        variants.add(base.replace("-", " "))
    return {v for v in variants if v}


def _in_hay(atom_norm: str, hay: str, dot_suffix: bool = False) -> bool:
    """Bounded containment: '420' must not pass on '4200' or '1420'.
    `dot_suffix` lets a reference be a prefix of a longer one
    ('batch-041' inside 'batch-041.csv') while still refusing 'batch-0412'."""
    tail = r"(?![\w-])" if dot_suffix else r"(?![\w.-])"
    if re.fullmatch(r"[\w.-]+", atom_norm):
        return re.search(rf"(?<![\w.-]){re.escape(atom_norm)}{tail}", hay) is not None
    return re.search(rf"(?<!\w){re.escape(atom_norm)}(?!\w)", hay) is not None


def _token_in_hay(token: str, hay: str) -> bool:
    """A name token bounded by word characters only — 'approver.' at a
    sentence end still counts (the '. ' bound is for amounts/refs)."""
    return re.search(rf"(?<!\w){re.escape(token)}(?!\w)", hay) is not None


def _atom_ok(kind: str, raw: str, hay: str) -> bool:
    """A reply atom is evidenced: names pass when every token appears anywhere
    in the case text (a name may be reordered or carry a title/possessive);
    references match as a prefix of a case reference; the rest need bounded
    containment of a variant."""
    variants = _atom_variants(kind, raw)
    if kind == "name":
        return any(v and all(_token_in_hay(t, hay) for t in v.split())
                   for v in variants)
    return any(_in_hay(v, hay, dot_suffix=(kind == "reference")) for v in variants)


def _claims_execution(text: str) -> str | None:
    """A done-word asserting a check/change happened, outside negated clauses."""
    for m in _DONE_RE.finditer(text):
        boundary = max(text.rfind(c, 0, m.start()) for c in ".!?\n") + 1
        window = text[boundary:m.start()]
        if re.search(r"(?i)\b(?:be|being|to)\s*$", window):
            continue  # subjunctive/infinitive: "requested it be sent", "to be
            # paid" — but "has been sent" IS a completion claim and must fire
        if _NEGATION_RE.search(window):
            continue
        if _AFTER_HEDGE_RE.match(text[m.end():]):
            continue
        return m.group(1)
    return None


def _channel_violation(constraints: list[Constraint], channel: str) -> Constraint | None:
    """A channel Constraint forbidding the reply's channel, or naming an
    exclusive channel ('secure chat only') the reply isn't on."""
    c = (channel or "").lower().strip()
    if not c:
        return None
    for con in constraints:
        if getattr(con, "type", None) != "channel":
            continue
        r = con.rule.lower()
        for m in re.finditer(r"(?:not|never|avoid|without|except|don't|do not|no)\b", r):
            seg = re.split(r"[.,;!?]|\bbut\b|\binstead\b|\bonly\b",
                           r[m.end():], maxsplit=1)[0]
            for _ in range(4):
                seg = _FILLER_RE.sub("", seg.strip()).strip()
            if c in seg:
                return con
        if "only" in r and c not in r.replace("only", " "):
            return con
    return None


def _resolved(finding: Finding, results: list[ToolResult], catalogue: dict) -> bool:
    """An ok lookup result resolves a conflict: it cites one of the finding's
    events, is a risk-1 read in the catalogue, or is a lookup by name."""
    for r in results:
        if r.status != "ok":
            continue
        if r.source_event and r.source_event in finding.events:
            return True
        spec = catalogue.get(r.tool)
        if spec is not None and getattr(spec, "risk", None) == 1:
            return True
        if "." not in r.tool and _LOOKUP_NAME_RE.search(r.tool):
            return True
    return False


def verify(
    proposal: Proposal,
    case: Case,
    case_object: CaseObject,
    findings: list[Finding],
    results: list[ToolResult],
) -> Verdict:
    reply_text = proposal.reply.text if proposal.reply else ""

    # 1. citation — every claims_relied_on id exists in the case or the trace
    event_ids = {e.id for e in case.events}
    result_tools = {r.tool for r in results}
    for cite in proposal.claims_relied_on:
        if cite.startswith("tool:"):
            if cite[5:] not in result_tools:
                return _fail("citation", "claims_relied_on", None,
                             f"citation '{cite}' has no matching tool result")
        elif cite not in event_ids:
            event = cite if re.fullmatch(r"event-\d+", cite) else None
            return _fail("citation", "claims_relied_on", event,
                         f"citation '{cite}' is not an event in the case")

    # 2. claim linter — every amount/date/name/reference in reply.text is evidenced
    if reply_text:
        hay = _haystack(case_object, results)
        # names and references may be evidenced by the wider case text: the
        # request, the title, and every event's sender, recipient and body —
        # claims and results alone are too narrow
        name_hay = hay + " " + _norm(" ".join(
            [case.initial_request or "", getattr(case, "title", "") or ""]
            + [getattr(e, "body", "") or "" for e in case.events]
            + [getattr(e, "sender", "") or "" for e in case.events]
            + [getattr(e, "recipient", "") or "" for e in case.events]))
        for kind, raw in _reply_atoms(reply_text):
            pool = name_hay if kind in ("name", "reference") else hay
            if not _atom_ok(kind, raw, pool):
                return _fail("claim_linter", "reply.text", None,
                             f"{kind} '{raw}' in the reply is not in a claim "
                             "or a tool result")

    # 3. no fabricated execution — a reported check/change needs an ok result;
    #    "requested — pending result" never becomes "done" (§4.3). Only the
    #    reply action's text is a completion claim: an escalate or
    #    request_info reply is holding text that asserts nothing was done.
    if proposal.action == "reply" and reply_text:
        claimed = _claims_execution(reply_text)
        if claimed and not any(r.status == "ok" for r in results):
            event = next((r.source_event for r in results if r.source_event), None)
            return _fail("fabricated_execution", "reply.text", event,
                         f"the reply claims '{claimed}' but no tool result has "
                         "status 'ok'")

    # 4. question answered — a supplied --question gets a non-empty answer
    if case.question and not (proposal.question_answer or "").strip():
        return _fail("question", "question_answer", None,
                     f"case question is unanswered: {case.question!r}")

    # 5. findings — every evidence-checker finding is addressed
    addressed = set(proposal.findings_addressed)
    for f in findings:
        if f.id not in addressed:
            return _fail("findings", "findings_addressed",
                         f.events[0] if f.events else None,
                         f"{f.id} ({f.kind}/{f.check}) is not addressed")

    # 6. authority, risk and channel — tool calls stay inside role, identity
    #    and prior-read limits; channel constraints apply to any reply
    if proposal.action == "tool_call":
        spec = _catalogue().get(proposal.tool or "")
        if spec is None:
            return _fail("catalogue", "tool", None,
                         f"tool '{proposal.tool}' is not in the catalogue")
        spec_name = getattr(spec, "name", proposal.tool)
        risk = getattr(spec, "risk", 3)
        roles = getattr(spec, "roles", []) or []
        if risk >= 2 and roles and case.authority.role not in roles:
            return _fail("authority", "action", None,
                         f"role '{case.authority.role}' may not call "
                         f"'{spec_name}' (roles: {', '.join(roles)})")
        if risk == 3:
            if case.authority.identity != "verified":
                return _fail("risk", "action", None,
                             f"'{spec_name}' is risk 3 and needs verified "
                             f"identity, not '{case.authority.identity}'")
            missing = [
                r for r in getattr(spec, "required_reads", []) or []
                if not any(res.tool == r and res.status == "ok" for res in results)
            ]
            if missing:
                return _fail("risk", "tool", None,
                             f"'{spec_name}' is missing required prior reads: "
                             + ", ".join(missing))
    if proposal.reply is not None:
        con = _channel_violation(case_object.constraints, proposal.reply.channel)
        if con is not None:
            event = con.source if con.source.startswith("event-") else None
            return _fail("channel", "reply.channel", event,
                         f"constraint '{con.rule}' forbids channel "
                         f"'{proposal.reply.channel}'")

    # 7. completion — every ask handled (escalate/request_info counts as handling)
    if proposal.action not in {"escalate", "request_info"}:
        done = set(proposal.asks_addressed)
        for ask in case_object.asks:
            if ask.id not in done:
                return _fail("completion", "asks_addressed", ask.event or None,
                             f"ask '{ask.id}' is not addressed: {ask.text!r}")

    # 8. material conflict — an unresolved conflict forces escalation; the
    #    model can't override it
    catalogue = _catalogue()
    for f in findings:
        if f.kind == "conflict" and not _resolved(f, results, catalogue):
            if proposal.action != "escalate":
                return _fail("conflict", "action",
                             f.events[0] if f.events else None,
                             f"unresolved conflict {f.id} forces escalation: "
                             f"{f.detail!r}")

    # 9. disclosure — no withheld identifiers in reply.text
    if reply_text:
        m = _DISCLOSURE_RE.search(reply_text)
        if m:
            return _fail("disclosure", "reply.text", None,
                         f"reply contains a withheld identifier: '{m.group(0)}'")

    return Verdict(ok=True, message="ok")
