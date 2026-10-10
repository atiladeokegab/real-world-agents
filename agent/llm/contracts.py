"""Contract shapes: the core's when merged (#11), otherwise the local mirror."""

try:
    from agent.core.contracts import (  # type: ignore[import-not-found]
        Case,
        CaseObject,
        Finding,
        Proposal,
        ToolResult,
        Verdict,
    )
except ImportError:
    from agent.llm._contracts import Case, CaseObject, Finding, Proposal, ToolResult, Verdict

__all__ = ["Case", "CaseObject", "Finding", "Proposal", "ToolResult", "Verdict"]
