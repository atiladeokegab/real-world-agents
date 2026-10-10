"""Shared shapes: core's when merged (#11), else a mirror of the brief's Contract."""

try:
    from agent.core.contracts import Case, Event, Proposal, ToolResult, ToolSpec
except ImportError:  # core not merged yet
    from datetime import datetime
    from typing import Any, Literal

    from pydantic import BaseModel

    class Authority(BaseModel):
        identity: Literal["verified", "authenticated", "unverified"] = "unverified"
        role: str | None = None

    class Event(BaseModel):
        id: str
        at: datetime
        channel: str
        sender: str
        recipient: str
        body: str

    class Case(BaseModel):
        track: str
        case_id: str
        title: str
        source_role: str
        created: datetime | None = None
        initial_request: str
        events: list[Event] = []
        attachments: list[Any] = []
        authority: Authority = Authority()
        raw_files: dict[str, str] = {}
        question: str | None = None

    class Proposal(BaseModel):
        action: Literal["tool_call", "reply", "request_info", "escalate", "no_op"]
        tool: str | None = None
        params: dict[str, Any] = {}

    class ToolSpec(BaseModel):
        name: str
        inputs: dict[str, str] = {}
        roles: list[str] = []
        risk: Literal[1, 2, 3]
        required_reads: list[str] = []
        read_back: str | None = None
        read_strength: Literal["strong", "lagging"] = "strong"
        key_fields: list[str] = []

    class ToolResult(BaseModel):
        tool: str
        params: dict[str, Any] = {}
        status: Literal["ok", "not_found", "pending", "timeout", "error", "uncertain"]
        data: dict[str, Any] = {}
        source_event: str | None = None

__all__ = ["Case", "Event", "Proposal", "ToolResult", "ToolSpec"]
