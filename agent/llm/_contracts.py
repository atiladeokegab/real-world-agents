"""Local mirror of the #11 contract shapes, used only until agent.core.contracts exists."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Authority(BaseModel):
    identity: Literal["verified", "authenticated", "unverified"] = "unverified"
    role: str | None = None


class Event(BaseModel):
    id: str
    at: datetime | str
    channel: str = ""
    sender: str = ""
    recipient: str = ""
    body: str = ""


class Attachment(BaseModel):
    name: str
    kind: Literal["csv", "pdf", "text", "image", "other"] = "other"
    text: str = ""


class Case(BaseModel):
    track: str = ""
    case_id: str
    title: str = ""
    source_role: str = ""
    created: datetime | str | None = None
    initial_request: str = ""
    events: list[Event] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    authority: Authority = Field(default_factory=Authority)
    raw_files: dict[str, str] = Field(default_factory=dict)
    question: str | None = None


class Finding(BaseModel):
    id: str
    kind: Literal["conflict", "anomaly"]
    check: Literal["amounts", "identity", "time", "duplicates", "status", "limits"]
    detail: str = ""
    events: list[str] = Field(default_factory=list)


class ToolResult(BaseModel):
    tool: str
    params: dict[str, Any] = Field(default_factory=dict)
    status: Literal["ok", "not_found", "pending", "timeout", "error", "uncertain"]
    data: dict[str, Any] = Field(default_factory=dict)
    source_event: str | None = None


class Verdict(BaseModel):
    ok: bool
    rule: str | None = None
    field: str | None = None
    event: str | None = None
    message: str = ""


# §4.4 case object

class Requester(BaseModel):
    name: str = ""
    evidence_events: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    subject: str
    predicate: str
    value: str = ""
    source_actor: str = ""
    channel: str = ""
    event: str
    conflicts_with: list[int] = Field(default_factory=list)


class Ask(BaseModel):
    id: str
    text: str
    event: str = ""


class Constraint(BaseModel):
    type: Literal["channel", "scope", "timing"]
    rule: str
    source: str = ""


class EmotionalState(BaseModel):
    level: Literal["calm", "frustrated", "distressed", "vulnerable"] = "calm"
    trend: Literal["steady", "worsening"] = "steady"
    events: list[str] = Field(default_factory=list)


class AttachmentSummary(BaseModel):
    file: str
    key_fields: dict[str, Any] = Field(default_factory=dict)


class CaseObject(BaseModel):
    requester: Requester = Field(default_factory=Requester)
    claims: list[Claim] = Field(default_factory=list)
    asks: list[Ask] = Field(default_factory=list)
    unknowns: list[str]
    constraints: list[Constraint] = Field(default_factory=list)
    emotional_state: EmotionalState = Field(default_factory=EmotionalState)
    attachments_summary: list[AttachmentSummary] = Field(default_factory=list)


# §4.5 proposal

class Reply(BaseModel):
    channel: str = ""
    text: str = ""


class Escalation(BaseModel):
    team: str = ""
    urgency: Literal["low", "normal", "high", "urgent"] = "normal"
    type: Literal["technical", "emotional"] = "technical"
    verified: list[str] = Field(default_factory=list)
    claimed: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    done: list[str] = Field(default_factory=list)
    not_done: list[str] = Field(default_factory=list)
    question: str = ""
    holding_reply: str = ""


class Proposal(BaseModel):
    action: Literal["tool_call", "reply", "request_info", "escalate", "no_op"]
    tool: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    reply: Reply | None = None
    question_answer: str | None = None
    asks_addressed: list[str] = Field(default_factory=list)
    claims_relied_on: list[str] = Field(default_factory=list)
    findings_addressed: list[str] = Field(default_factory=list)
    exception_type: str | None = None
    escalation: Escalation | None = None
    uncertainties: list[str] = Field(default_factory=list)
