"""Verbatim copy of agent/core/contracts.py from #11 (branch 11-core-contracts), used only until it merges."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# §4.1 ingest

class Authority(BaseModel):
    """Set by the ingestor from channel metadata; the model can never raise it."""
    identity: Literal["verified", "authenticated", "unverified"] = "unverified"
    role: str | None = None


class Event(BaseModel):
    id: str  # "event-001"
    at: datetime
    channel: str
    sender: str
    recipient: str
    body: str


class Attachment(BaseModel):
    name: str
    kind: Literal["csv", "pdf", "text", "image", "other"]
    text: str


class Case(BaseModel):
    track: str
    case_id: str
    title: str
    source_role: str
    created: datetime | None = None
    initial_request: str
    events: list[Event] = []
    attachments: list[Attachment] = []
    authority: Authority = Authority()
    raw_files: dict[str, str] = {}  # file name -> text, for trace.log
    question: str | None = None


# §4.2 evidence checker

class Finding(BaseModel):
    id: str  # "finding-1"
    kind: Literal["conflict", "anomaly"]
    check: Literal["amounts", "identity", "time", "duplicates", "status", "limits"]
    detail: str
    events: list[str] = []


# §4.4 extraction

class Requester(BaseModel):
    name: str
    evidence_events: list[str] = []


class Claim(BaseModel):
    subject: str
    predicate: str
    value: str
    source_actor: str
    channel: str
    event: str
    conflicts_with: list[int] = []  # indexes into CaseObject.claims


class Ask(BaseModel):
    id: str  # "ask-1"
    text: str
    event: str


class Constraint(BaseModel):
    type: Literal["channel", "scope", "timing"]
    rule: str
    source: str


class EmotionalState(BaseModel):
    level: Literal["calm", "frustrated", "distressed", "vulnerable"] = "calm"
    trend: Literal["steady", "worsening"] = "steady"
    events: list[str] = []


class AttachmentSummary(BaseModel):
    file: str
    key_fields: dict[str, Any] = {}


class CaseObject(BaseModel):
    requester: Requester
    claims: list[Claim] = []
    asks: list[Ask] = []
    unknowns: list[str]  # required, so gaps can't be silently hallucinated away
    constraints: list[Constraint] = []
    emotional_state: EmotionalState = EmotionalState()
    attachments_summary: list[AttachmentSummary] = []


# §4.5 decision

class Reply(BaseModel):
    channel: str
    text: str


class Proposal(BaseModel):
    action: Literal["tool_call", "reply", "request_info", "escalate", "no_op"]
    tool: str | None = None
    params: dict[str, Any] = {}
    reply: Reply | None = None
    question_answer: str | None = None
    asks_addressed: list[str] = []
    claims_relied_on: list[str] = []  # "event-NNN" or "tool:X"
    findings_addressed: list[str] = []
    exception_type: str | None = None  # a §4.8 registry name
    escalation: dict[str, Any] | None = None  # §4.8 handover note
    uncertainties: list[str] = []


# §4.3 tools, §4.7 executor

class ToolSpec(BaseModel):
    name: str
    inputs: dict[str, str] = {}  # param name -> type name
    roles: list[str] = []
    risk: Literal[1, 2, 3]
    required_reads: list[str] = []
    read_back: str | None = None
    read_strength: Literal["strong", "lagging"] = "strong"
    key_fields: list[str] = []  # params hashed into the idempotency key


class ToolResult(BaseModel):
    tool: str
    params: dict[str, Any] = {}
    status: Literal["ok", "not_found", "pending", "timeout", "error", "uncertain"]
    data: dict[str, Any] = {}
    source_event: str | None = None


# §4.6 verifier

class Verdict(BaseModel):
    ok: bool
    rule: str | None = None
    field: str | None = None
    event: str | None = None
    message: str = ""
