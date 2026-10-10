"""Decision: Claude, one proposal per loop turn (AGENT_SPEC §4.5)."""

from __future__ import annotations

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
    proposal = normalise(_client.call("decision", decision_system(), user, Proposal),
                         case, case_object, findings, results)
    if leaves_customer_waiting(proposal, case_object):
        user = decision_user(case, case_object, findings, results, NO_OP_UNANSWERED, authority)
        proposal = normalise(_client.call("decision", decision_system(), user, Proposal),
                             case, case_object, findings, results)
    if leaves_customer_waiting(proposal, case_object):
        forced = proposal.model_copy(update={"action": "escalate", "exception_type": "incomplete_answer", "reply": None})
        proposal = normalise(forced, case, case_object, findings, results)
    return proposal
