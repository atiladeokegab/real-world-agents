import json
import sys
import time
import types

import pytest

from agent.core.contracts import Case, CaseObject, Proposal, Reply, ToolResult, Verdict
from agent.core.loop import run_case

READ = Proposal(action="tool_call", tool="business_service", params={"row": "SUP-17"})
REPLY = Proposal(action="reply", reply=Reply(channel="Secure portal", text="Row SUP-17 is pending."))


def fake_areas(monkeypatch, proposals, verdicts=None, status="pending", decide_delay=0):
    """Stand-ins for agent.ingest/checks/llm/tools, which other teammates build."""
    proposals, verdicts = iter(proposals), iter(verdicts or [])
    case = Case(track="banking", case_id="044", title="t", source_role="r", initial_request="q",
                raw_files={"index.md": "# Case 044"})

    def decide(*a):
        time.sleep(decide_delay)
        return next(proposals)

    mods = {
        "agent.ingest": dict(load_case=lambda path, cut=None, question=None: case),
        "agent.checks": dict(find_evidence=lambda c: [],
                             verify=lambda *a: next(verdicts, Verdict(ok=True))),
        "agent.llm": dict(extract=lambda c, f: CaseObject(requester={"name": "L"}, unknowns=[]),
                          decide=decide),
        "agent.tools": dict(CATALOGUE={}, execute=lambda p, c, d, practice_events=[]:
                            ToolResult(tool=p.tool, params=p.params, status=status)),
    }
    for name, attrs in mods.items():
        monkeypatch.setitem(sys.modules, name, types.SimpleNamespace(**attrs))
        monkeypatch.setattr(sys.modules["agent"], name.split(".")[1], sys.modules[name], raising=False)


def run(tmp_path, **kw):
    out = run_case(tmp_path / "044", tmp_path / "out", **kw)
    return json.loads((out / "run.json").read_text()), (out / "ANSWER.md").read_text()


def test_read_then_reply(tmp_path, monkeypatch):
    fake_areas(monkeypatch, [READ, REPLY])
    r, answer = run(tmp_path)
    assert (r["action"], r["tool_calls"], r["fallback"]) == ("reply", 1, False)
    assert "requested, pending result" in answer and "Row SUP-17 is pending." in answer


def test_second_rejection_escalates(tmp_path, monkeypatch):
    bad = Verdict(ok=False, rule="citation", field="claims_relied_on", event="event-009")
    fake_areas(monkeypatch, [REPLY, REPLY], [bad, bad])
    r, answer = run(tmp_path)
    assert r["escalated"] and "verifier rejected twice" in answer
    assert r["exception_type"] == "incomplete_answer"


def test_identical_calls_are_capped(tmp_path, monkeypatch):
    fake_areas(monkeypatch, [READ] * 10)
    r, _ = run(tmp_path)
    assert r["escalated"] and r["tool_calls"] == 2 and r["exception_type"] == "read_failure"


def test_uncertain_write_escalates(tmp_path, monkeypatch):
    fake_areas(monkeypatch, [READ], status="uncertain")
    r, _ = run(tmp_path)
    assert r["exception_type"] == "write_failure"


@pytest.mark.parametrize("area", ["agent.ingest", "agent.llm"])
def test_missing_area_writes_fallback(tmp_path, monkeypatch, area):
    fake_areas(monkeypatch, [REPLY])
    monkeypatch.setitem(sys.modules, area, None)  # import raises ImportError
    monkeypatch.delattr(sys.modules["agent"], area.split(".")[1], raising=False)
    r, answer = run(tmp_path)
    assert r["fallback"] and "escalate (system failure)" in answer


def test_timeout_writes_fallback(tmp_path, monkeypatch):
    fake_areas(monkeypatch, [REPLY], decide_delay=2)
    r, _ = run(tmp_path, time_limit=0.2)
    assert r["fallback"]
    assert "timed out" in (tmp_path / "out" / "REASONING.md").read_text()
