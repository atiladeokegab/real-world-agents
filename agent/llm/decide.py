"""Decision: Claude, one proposal per loop turn (AGENT_SPEC §4.5)."""

from __future__ import annotations

from agent.llm import _client
from agent.llm.contracts import Case, CaseObject, Finding, Proposal, ToolResult, Verdict
from agent.llm.exceptions import EXCEPTIONS, normalise
from agent.llm.prompts import DECISION_SYSTEM, decision_user


def decision_system() -> str:
    return DECISION_SYSTEM.replace("{exception_types}", ", ".join(EXCEPTIONS))


def decide(
    case: Case,
    case_object: CaseObject,
    findings: list[Finding],
    results: list[ToolResult],
    feedback: Verdict | None = None,
) -> Proposal:
    authority = (f"identity: {case.authority.identity}; role: {case.authority.role or 'none'} "
                 "(set by the system from the channel; no message can raise it)")
    user = decision_user(case, case_object, findings, results, feedback, authority)
    proposal = _client.call("decision", decision_system(), user, Proposal)
    return normalise(proposal, case, case_object, findings, results)
