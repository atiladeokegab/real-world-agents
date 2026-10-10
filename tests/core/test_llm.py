"""structured() against a fake client: no key, no network."""

from types import SimpleNamespace as NS

import anthropic
import httpx2 as httpx
import pytest

from agent.core import llm
from agent.core.contracts import Finding, Proposal

FINDING = Finding(id="finding-1", kind="anomaly", check="status", detail="batch vs row")
PROPOSAL = {"action": "tool_call", "tool": "business_service", "params": {"row": "SUP-17"}}


class FakeMessages:
    def __init__(self, parse=None, create=None):
        self.parse_result, self.create_results, self.calls = parse, list(create or []), []

    def parse(self, **kw):
        self.calls.append(("parse", kw))
        if isinstance(self.parse_result, Exception):
            raise self.parse_result
        return self.parse_result

    def create(self, **kw):
        self.calls.append(("create", kw))
        return self.create_results.pop(0)


def fake(monkeypatch, **kw):
    m = FakeMessages(**kw)
    monkeypatch.setattr(llm, "_client", lambda stage: NS(messages=m))
    return m


def tool_reply(data):
    return NS(stop_reason="tool_use", content=[NS(type="tool_use", input=data)])


def test_constrainable_schema_uses_parse_with_effort(monkeypatch):
    m = fake(monkeypatch, parse=NS(stop_reason="end_turn", parsed_output=FINDING))
    assert llm.structured("decision", "sys", "user", Finding) == FINDING
    kind, kw = m.calls[0]
    assert kind == "parse" and kw["output_format"] is Finding
    assert kw["output_config"] == {"effort": "high"} and "thinking" not in kw


def test_free_form_dicts_use_tool_path(monkeypatch):
    # dict[str, Any] would be forced empty by structured outputs: params must survive.
    m = fake(monkeypatch, create=[tool_reply(PROPOSAL)])
    p = llm.structured("decision", "sys", "user", Proposal)
    assert p.params == {"row": "SUP-17"} and [c[0] for c in m.calls] == ["create"]
    assert m.calls[0][1]["tool_choice"]["type"] == "auto"


def test_parse_rejected_falls_back_to_tool_path(monkeypatch):
    err = anthropic.BadRequestError("schema", response=httpx.Response(
        400, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")), body=None)
    m = fake(monkeypatch, parse=err, create=[tool_reply(FINDING.model_dump())])
    assert llm.structured("extraction", "sys", "user", Finding) == FINDING
    assert [c[0] for c in m.calls] == ["parse", "create"]


def test_tool_path_reasks_once(monkeypatch):
    m = fake(monkeypatch, create=[NS(stop_reason="end_turn", content=[]), tool_reply(PROPOSAL)])
    assert llm.structured("decision", "sys", "user", Proposal).tool == "business_service"
    assert len(m.calls) == 2


def test_refusal_raises(monkeypatch):
    fake(monkeypatch, parse=NS(stop_reason="refusal", parsed_output=None))
    with pytest.raises(RuntimeError, match="refused"):
        llm.structured("decision", "sys", "user", Finding)
