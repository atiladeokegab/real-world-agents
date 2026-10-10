"""Decision: Claude, one proposal per loop turn (AGENT_SPEC §4.5)."""

from __future__ import annotations

import re

from agent.llm import _client
from agent.llm.contracts import Case, CaseObject, Finding, Proposal, ToolResult, Verdict
from agent.llm.exceptions import EXCEPTIONS, normalise
from agent.llm.prompts import DECISION_SYSTEM, decision_user

NO_OP_UNANSWERED = Verdict(
    ok=False, rule="completion", field="action",
    message=("no_op leaves the customer's ask without a reply. Reply instead: with what the records show, or, "
             "while a lookup is pending, in the pending wording: "
             "\"We've asked <team> to <check>. We'll reply here once they've confirmed.\""),
)


NOT_FOUND_IS_AN_ANSWER = Verdict(
    ok=False, rule="exceptions", field="exception_type",
    message=("not_found is a normal answer, not a read_failure: read_failure is only a timeout or error. "
             "Reply honestly: \"We can't see a record of <x> yet; we've asked <team> to check and we'll reply here\", "
             "or request_info if the customer can give a reference."),
)

_FAILED = ("timeout", "error")


def misreads_not_found(proposal: Proposal, results: list[ToolResult]) -> bool:
    return (proposal.exception_type == "read_failure" and proposal.action != "tool_call"
            and not any(r.status in _FAILED for r in results))


def leaves_customer_waiting(proposal: Proposal, case_object: CaseObject) -> bool:
    return proposal.action == "no_op" and bool(case_object.asks) and not (proposal.reply and proposal.reply.text)


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

    def ask(verdict: Verdict | None) -> Proposal:
        user = decision_user(case, case_object, findings, results, verdict, authority)
        return normalise(_client.call("decision", decision_system(), user, Proposal), case, case_object, findings, results)

    proposal = ask(feedback)
    problem = _problem(proposal, case_object, results)
    if problem:
        proposal = ask(problem[0])
        problem = _problem(proposal, case_object, results)
        if problem and problem[1]:
            proposal = normalise(proposal.model_copy(update=problem[1]), case, case_object, findings, results)
    return proposal


_INCOMPLETE = {"action": "escalate", "exception_type": "incomplete_answer", "reply": None}


def _problem(proposal: Proposal, case_object: CaseObject, results: list[ToolResult]) -> tuple[Verdict, dict | None] | None:
    """A proposal the brain sends back once, and what it becomes if the retry repeats it (None: keep it)."""
    if leaves_customer_waiting(proposal, case_object):
        return NO_OP_UNANSWERED, _INCOMPLETE
    if misreads_not_found(proposal, results):
        return NOT_FOUND_IS_AN_ANSWER, None
    return None
