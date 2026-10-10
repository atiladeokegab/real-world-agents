"""Extraction: Claude call #1 (AGENT_SPEC §4.4)."""

from __future__ import annotations

from agent.llm import _client
from agent.llm.contracts import Case, CaseObject, Finding
from agent.llm.prompts import EXTRACTION_SYSTEM, extraction_user


def extract(case: Case, findings: list[Finding]) -> CaseObject:
    obj = _client.call("extraction", EXTRACTION_SYSTEM, extraction_user(case, findings), CaseObject)
    known = {e.id for e in case.events}
    for i, claim in enumerate(obj.claims):
        if claim.event not in known:
            obj.unknowns.append(f"claim {i} cites {claim.event or 'no event'}, which is not in the case")
    return obj
