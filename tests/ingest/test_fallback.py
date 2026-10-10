import sys
import types
from pathlib import Path

from pydantic import BaseModel

from agent.core.contracts import Event
from agent.ingest import load_case

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "examples"


class _SpyLLM:
    """Stands in for agent.core.llm: records calls, returns canned events."""

    def __init__(self, events=None, error=None):
        self.calls = []
        self._events = events or []
        self._error = error

    def structured(self, stage, system, user, model):
        self.calls.append({"stage": stage, "system": system, "user": user, "model": model})
        if self._error:
            raise self._error
        return model(events=self._events)


def _install(monkeypatch, spy):
    module = types.SimpleNamespace(structured=spy.structured)
    monkeypatch.setitem(sys.modules, "agent.core.llm", module)
    return spy


def _empty_case(tmp_path: Path) -> Path:
    case_dir = tmp_path / "901"
    case_dir.mkdir()
    (case_dir / "index.md").write_text("# Case 901: Odd format\n\n## Initial request\n\nhelp\n")
    (case_dir / "history.md").write_text("this file has no event anchors at all\n")
    return case_dir


def test_fallback_fires_once_on_zero_events(tmp_path, monkeypatch):
    events = [
        Event(id="event-001", at="2025-01-01T09:00:00Z", channel="Secure chat",
              sender="Mara", recipient="H&V agent", body="help"),
    ]
    spy = _install(monkeypatch, _SpyLLM(events=events))

    case = load_case(_empty_case(tmp_path))

    assert len(spy.calls) == 1
    assert spy.calls[0]["stage"] == "extraction"
    assert issubclass(spy.calls[0]["model"], BaseModel)
    assert [e.id for e in case.events] == ["event-001"]


def test_model_written_events_never_set_authority(tmp_path, monkeypatch):
    # §4.1: authority comes from channel metadata the code parsed — not from
    # model-written events, even a "Verified call".
    events = [
        Event(id="event-001", at="2025-01-01T09:00:00Z", channel="Verified call",
              sender="Mara", recipient="H&V agent", body="help"),
    ]
    _install(monkeypatch, _SpyLLM(events=events))
    assert load_case(_empty_case(tmp_path)).authority.identity == "unverified"


def _history_case(tmp_path: Path, name="902") -> Path:
    case_dir = tmp_path / name
    case_dir.mkdir()
    (case_dir / "index.md").write_text("# Case 902: T\n\n## Initial request\n\nhelp\n")
    (case_dir / "history.md").write_text(
        "<a id=\"event-001\"></a>\n## 2025-01-01 09:00:00 UTC — event 001\n\n"
        "- **Channel:** External message\n- **From:** X\n- **To:** H&V agent\n\nhi\n"
    )
    return case_dir


def test_unrecognised_file_falls_back_on_that_file_alone(tmp_path, monkeypatch):
    case_dir = _history_case(tmp_path)
    (case_dir / "mystery.dat").write_bytes(b"\x00\x01\x02")

    spy = _install(monkeypatch, _SpyLLM(events=[]))
    case = load_case(case_dir)

    assert len(spy.calls) == 1
    assert "mystery.dat" in spy.calls[0]["user"]
    assert "hi" not in spy.calls[0]["user"]  # parsed events are not re-sent
    assert "mystery.dat" in case.raw_files  # unknown files read as text, never crash
    assert [e.id for e in case.events] == ["event-001"]  # parsed events kept


def test_unrecognised_file_appends_model_events(tmp_path, monkeypatch):
    case_dir = _history_case(tmp_path)
    (case_dir / "mystery.dat").write_bytes(b"\x00\x01\x02")
    extra = [Event(id="event-001", at="2025-01-01T10:00:00Z", channel="External message",
                   sender="Y", recipient="H&V agent", body="from the dat file")]
    _install(monkeypatch, _SpyLLM(events=extra))

    case = load_case(case_dir)

    # model events appended after the parsed ones, renumbered to avoid id clashes
    assert [e.id for e in case.events] == ["event-001", "event-002"]
    assert case.events[1].body == "from the dat file"


def test_fallback_error_keeps_parsed_events(tmp_path, monkeypatch):
    case_dir = _history_case(tmp_path)
    (case_dir / "mystery.dat").write_bytes(b"\x00\x01\x02")
    _install(monkeypatch, _SpyLLM(error=RuntimeError("api down")))

    case = load_case(case_dir)
    assert [e.id for e in case.events] == ["event-001"]


def test_dotfiles_do_not_trigger_fallback(tmp_path, monkeypatch):
    case_dir = _history_case(tmp_path)
    (case_dir / ".DS_Store").write_bytes(b"\x00\x01\x02")

    spy = _install(monkeypatch, _SpyLLM())
    case = load_case(case_dir)

    assert spy.calls == []
    assert ".DS_Store" not in case.raw_files
    assert [e.id for e in case.events] == ["event-001"]


def test_fallback_prompt_strips_answer_sections_in_practice_mode(tmp_path, monkeypatch):
    case_dir = _empty_case(tmp_path)
    (case_dir / "index.md").write_text(
        "# Case 901: T\n\n## Initial request\n\nhelp\n\n"
        "## Overview\n\nthe agreed answer is XYZ\n\n## Outcome\n\nsecret outcome\n"
    )
    spy = _install(monkeypatch, _SpyLLM(events=[]))
    load_case(case_dir, cut=2)

    assert len(spy.calls) == 1
    assert "secret outcome" not in spy.calls[0]["user"]
    assert "the agreed answer is XYZ" not in spy.calls[0]["user"]


def test_no_fallback_on_normal_case(monkeypatch):
    spy = _install(monkeypatch, _SpyLLM())
    case = load_case(EXAMPLES / "001")
    assert spy.calls == []
    assert len(case.events) == 5


def test_fallback_error_degrades_to_empty_events(tmp_path, monkeypatch):
    _install(monkeypatch, _SpyLLM(error=RuntimeError("api down")))
    case = load_case(_empty_case(tmp_path))
    assert case.events == []


def test_missing_llm_module_degrades(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "agent.core.llm", None)  # import raises
    case = load_case(_empty_case(tmp_path))
    assert case.events == []
