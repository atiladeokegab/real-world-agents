import json

from agent.core.contracts import Ask, Case, CaseObject, Proposal, Reply, ToolResult, Verdict
from agent.core.writer import write, write_fallback

FILES = {"ANSWER.md", "REASONING.md", "trace.log", "run.json"}


def test_write_all_four_files(tmp_path):
    case = Case(track="banking", case_id="044", title="One line", source_role="business user",
                initial_request="Was SUP-17 paid?", question="Was SUP-17 paid?",
                raw_files={"index.md": "# Case 044"})
    co = CaseObject(requester={"name": "Leona"}, unknowns=["row status"],
                    asks=[Ask(id="ask-1", text="SUP-17 status", event="event-001"),
                          Ask(id="ask-2", text="other rows", event="event-001")])
    p = Proposal(action="reply", reply=Reply(channel="Secure portal", text="Row SUP-17 was rejected."),
                 question_answer="Rejected.", asks_addressed=["ask-1"])
    r = ToolResult(tool="business_service", status="pending")
    write(tmp_path, case, co, [], p, [r], [(p, Verdict(ok=False, rule="citation", message="x"))], [])
    assert {f.name for f in tmp_path.iterdir()} == FILES
    a = (tmp_path / "ANSWER.md").read_text()
    assert "Rejected." in a and "requested, pending result" in a and "ask-2" in a
    assert json.loads((tmp_path / "run.json").read_text())["escalated"] is False


def test_fallback_is_escalated(tmp_path):
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "index.md").write_text("# Case 9")
    out = tmp_path / "out"
    write_fallback(out, case_dir, "ImportError: no agent.ingest", [])
    assert {f.name for f in out.iterdir()} == FILES
    assert "escalate (system failure)" in (out / "ANSWER.md").read_text()
    assert "index.md" in (out / "ANSWER.md").read_text()
    assert json.loads((out / "run.json").read_text())["fallback"] is True


def test_exception_names_its_handling(monkeypatch):
    import sys
    import types
    from agent.core.writer import _exception
    monkeypatch.setitem(sys.modules, "agent.llm", types.SimpleNamespace(handling_for=lambda n: "escalate"))
    assert _exception("read_failure") == "read_failure: escalate"
    monkeypatch.setitem(sys.modules, "agent.llm", None)
    assert _exception("read_failure") == "read_failure"
    assert _exception(None) == "none"
