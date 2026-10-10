from agent.llm import _client
from agent.llm.contracts import Verdict


def test_call_goes_through_structured_and_returns_the_schema(fake_llm):
    fake_llm.answers.append({"ok": True, "message": "fine"})
    out = _client.call("decision", "sys", "usr", Verdict)
    assert isinstance(out, Verdict) and out.ok
    assert fake_llm.calls[0]["stage"] == "decision"
    assert fake_llm.calls[0]["model"] is Verdict
