import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FakeStructured:
    """Stands in for agent.core.llm.structured: records each call, returns the queued answers."""

    def __init__(self):
        self.calls = []
        self.answers = []

    def __call__(self, stage, system, user, model):
        self.calls.append({"stage": stage, "system": system, "user": user, "model": model})
        answer = self.answers.pop(0)
        return model.model_validate(answer) if isinstance(answer, dict) else answer


@pytest.fixture
def fake_llm(monkeypatch):
    fake = FakeStructured()
    try:
        import agent.core.llm as core_llm
    except ImportError:
        core = types.ModuleType("agent.core")
        core_llm = types.ModuleType("agent.core.llm")
        core.llm = core_llm
        monkeypatch.setitem(sys.modules, "agent.core", core)
        monkeypatch.setitem(sys.modules, "agent.core.llm", core_llm)
    monkeypatch.setattr(core_llm, "structured", fake, raising=False)
    return fake
