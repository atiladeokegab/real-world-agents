"""Contract shapes: the core's when merged (#11), otherwise the local mirror."""

try:
    from agent.core.contracts import (  # type: ignore[import-not-found]
        Attachment,
        Authority,
        Case,
        CaseObject,
        Event,
        Finding,
        Proposal,
        ToolResult,
        Verdict,
    )
except ImportError:
    from agent.llm._contracts import (
        Attachment,
        Authority,
        Case,
        CaseObject,
        Event,
        Finding,
        Proposal,
        ToolResult,
        Verdict,
    )

__all__ = ["Attachment", "Authority", "Case", "CaseObject", "Event", "Finding", "Proposal", "ToolResult", "Verdict"]
