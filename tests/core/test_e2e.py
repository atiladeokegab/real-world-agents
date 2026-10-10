"""End-to-end runs: real areas, real Claude. Skips until every area exists and a key is set.

The smoke runs one case (044 at its decision point) so it stays inside its 2-minute budget;
the rest are `slow`, run with RUN_SLOW=1.
"""

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
slow = [pytest.mark.slow,
        pytest.mark.skipif(os.environ.get("RUN_SLOW") != "1", reason="slow: set RUN_SLOW=1")]


def check(num: str, tmp_path, time_limit: float, cut: int | None = None) -> None:
    out = run_case(ROOT / "examples" / num, tmp_path / num, cut=cut, time_limit=time_limit)
    run = json.loads((out / "run.json").read_text())
    assert not run["fallback"], (out / "REASONING.md").read_text()
    assert run["action"] in {"reply", "request_info", "escalate", "no_op"}
    assert {f.name for f in out.iterdir()} >= {"ANSWER.md", "REASONING.md", "trace.log", "run.json"}
    assert (out / "ANSWER.md").read_text().startswith(f"# Case {num}")


def test_044_at_decision_point(tmp_path):
    from eval.cut import cut_index
    check("044", tmp_path, 150, cut_index(ROOT / "examples" / "044" / "history.md"))


@pytest.mark.parametrize("num", [pytest.param(n, marks=slow) for n in ("001", "044", "006")])
def test_case_end_to_end(tmp_path, num):
    check(num, tmp_path, 240)
