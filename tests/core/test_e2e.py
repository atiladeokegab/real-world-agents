"""First end-to-end run: real areas, real Claude. Skips until every area exists and a key is set."""

import importlib.util
import json
import os
from pathlib import Path

import pytest

from agent.core.loop import run_case

ROOT = Path(__file__).parents[2]
AREAS = ["agent.ingest", "agent.checks", "agent.llm", "agent.tools"]
missing = [a for a in AREAS if importlib.util.find_spec(a) is None]
has_key = any(os.environ.get(k) for k in
              ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY_EXTRACTION", "ANTHROPIC_API_KEY_DECISION"))

pytestmark = [pytest.mark.skipif(bool(missing), reason=f"areas not merged yet: {missing}"),
              pytest.mark.skipif(not has_key, reason="no Anthropic key set")]


@pytest.mark.parametrize("num", ["001", "044", "006"])
def test_case_end_to_end(tmp_path, num):
    out = run_case(ROOT / "examples" / num, tmp_path / num)
    run = json.loads((out / "run.json").read_text())
    assert not run["fallback"], (out / "REASONING.md").read_text()
    assert run["action"] in {"reply", "request_info", "escalate", "no_op"}
    assert {f.name for f in out.iterdir()} >= {"ANSWER.md", "REASONING.md", "trace.log", "run.json"}
