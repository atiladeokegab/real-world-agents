import os
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from agent.core.cli import app

ROOT = Path(__file__).parents[2]


def test_run_always_answers_and_collect_lists_it(tmp_path):
    # A fresh process with the keys blanked (offline, free): whatever the areas' state,
    # `run` must exit 0 with all four files.
    env = {**os.environ, "ANTHROPIC_API_KEY": "", "ANTHROPIC_API_KEY_EXTRACTION": "",
           "ANTHROPIC_API_KEY_DECISION": ""}
    p = subprocess.run([sys.executable, "-c", "from agent.core.cli import app; app()", "run",
                        "--case", str(ROOT / "examples" / "044"), "--out", str(tmp_path / "044")],
                       capture_output=True, text=True, timeout=200, env=env)
    assert p.returncode == 0, p.stderr
    assert {f.name for f in (tmp_path / "044").iterdir()} >= {"ANSWER.md", "REASONING.md", "trace.log", "run.json"}

    (tmp_path / "045").mkdir()
    r = CliRunner().invoke(app, ["collect", "--out", str(tmp_path)])
    assert r.exit_code == 1 and "044" in r.output and "045  MISSING ANSWER.md" in r.output
