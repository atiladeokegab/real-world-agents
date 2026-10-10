"""End-to-end runs: real areas, real Claude. Skips until every area exists and a key is set.

The smoke runs one case (044 at its decision point) so it stays inside its 2-minute budget;
the rest are `slow`, run with RUN_SLOW=1.
"""

import importlib.util
import json
import os
import re
from pathlib import Path

import anthropic
import pytest

from agent.core.loop import run_case

ROOT = Path(__file__).parents[2]
# What run_case calls. An area merged only in part (e.g. checks without verify) still skips,
# so the smoke stays green until the whole loop can run.
NEEDS = {"agent.ingest": ["load_case"], "agent.checks": ["find_evidence", "verify"],
         "agent.llm": ["extract", "decide"], "agent.tools": ["CATALOGUE", "execute"]}


def _missing() -> list[str]:
    out = []
    for mod, names in NEEDS.items():
        if importlib.util.find_spec(mod) is None:
            out.append(mod)
        else:
            m = importlib.import_module(mod)
            out += [f"{mod}.{n}" for n in names if not hasattr(m, n)]
    return out


missing = _missing()
has_key = any(os.environ.get(k) for k in
              ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY_EXTRACTION", "ANTHROPIC_API_KEY_DECISION"))

e2e = [pytest.mark.skipif(bool(missing), reason=f"areas not merged yet: {missing}"),
       pytest.mark.skipif(not has_key, reason="no Anthropic key set")]
slow = e2e + [pytest.mark.slow,
        pytest.mark.skipif(os.environ.get("RUN_SLOW") != "1", reason="slow: set RUN_SLOW=1")]


# The API being busy or slow is not a bug in the merge under test: skip, don't fail (and revert).
TRANSIENT = (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError,
             anthropic.InternalServerError, anthropic.OverloadedError, anthropic.ServiceUnavailableError,
             anthropic.DeadlineExceededError)
TRANSIENT_IN_TRACE = re.compile(
    r"\b(" + "|".join(e.__name__ for e in TRANSIENT) + r")\b"
    r"|Error code: (429|5\d\d)\b"      # an APIStatusError 429 or 5xx (529 overloaded included)
    r"|no answer within the .* limit|timed out after .* s")  # the per-case time limit (core's wording)


def check(num: str, tmp_path, time_limit: float, cut: int | None = None) -> None:
    try:
        out = run_case(ROOT / "examples" / num, tmp_path / num, cut=cut, time_limit=time_limit)
    except TRANSIENT as e:
        pytest.skip(f"Anthropic API transient error: {type(e).__name__}: {e}")
    run = json.loads((out / "run.json").read_text())
    if run["fallback"]:
        cause = TRANSIENT_IN_TRACE.search((out / "trace.log").read_text())
        if cause:
            pytest.skip(f"fallback caused by a transient API error ({cause.group(0)})")
    assert not run["fallback"], (out / "REASONING.md").read_text()
    assert run["action"] in {"reply", "request_info", "escalate", "no_op"}
    assert {f.name for f in out.iterdir()} >= {"ANSWER.md", "REASONING.md", "trace.log", "run.json"}
    title = (out / "ANSWER.md").read_text().splitlines()[0]
    assert title.startswith("# ") and num in title  # the wording is the design's; the number must be there


@pytest.mark.skipif(bool(missing), reason=f"areas not merged yet: {missing}")
@pytest.mark.skipif(not has_key, reason="no Anthropic key set")
def test_044_at_decision_point(tmp_path):
    from eval.cut import cut_index
    check("044", tmp_path, 150, cut_index(ROOT / "examples" / "044" / "history.md"))


@pytest.mark.parametrize("num", [pytest.param(n, marks=slow) for n in ("001", "044", "006")])
def test_case_end_to_end(tmp_path, num):
    check(num, tmp_path, 240)


def test_transient_fallbacks_skip_and_real_ones_fail(tmp_path, monkeypatch):
    """check() itself, with a faked run: runs without areas or keys."""
    import sys

    from agent.core.writer import write_fallback
    me = sys.modules[__name__]
    (tmp_path / "examples" / "001").mkdir(parents=True)
    monkeypatch.setattr(me, "ROOT", tmp_path)

    def fallback_with(error):
        def fake_run_case(path, out, **kw):
            write_fallback(out, path, error, [])
            return out
        monkeypatch.setattr(me, "run_case", fake_run_case)

    for transient in ("anthropic.RateLimitError: Error code: 429",
                      "anthropic.InternalServerError: Error code: 529 overloaded",
                      "TimeoutError: no answer within the 150 s limit"):
        fallback_with(f"Traceback...\n{transient}")
        with pytest.raises(pytest.skip.Exception):
            check("001", tmp_path / "out", 1)
    fallback_with("Traceback...\nAttributeError: 'Proposal' object has no attribute 'x'")
    with pytest.raises(AssertionError):
        check("001", tmp_path / "out", 1)
