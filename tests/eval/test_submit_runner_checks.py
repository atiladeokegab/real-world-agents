import json
from importlib import import_module
from types import SimpleNamespace

from tests.eval.conftest import KEYS


def cases_dir(tmp_path, numbers=("001",)):
    cases = tmp_path / "cases"
    for n in numbers:
        (cases / n).mkdir(parents=True)
        (cases / n / "index.md").write_text(f"# Case {n}\n")
    return cases


def test_no_key_exits_1_and_writes_nothing(tmp_path, monkeypatch, capsys):
    submit = import_module("eval.submit")
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY_DECISION", "only-decision")  # extraction still missing
    ran = []
    monkeypatch.setattr(submit, "run_case", lambda case, out: ran.append(case))
    out = tmp_path / "answers"
    assert submit.main([str(cases_dir(tmp_path)), "--out", str(out)]) == 1
    assert "ERROR: no Anthropic key for extraction; set it in .env" in capsys.readouterr().err
    assert not out.exists() and not ran

    monkeypatch.delenv("ANTHROPIC_API_KEY_DECISION")
    monkeypatch.setenv("ANTHROPIC_API_KEY_EXTRACTION", "only-extraction")  # shared by every stage
    assert submit.api_key("decision") == "only-extraction"  # so the check passes with one shared key


def test_agent_written_fallback_counts(tmp_path, monkeypatch, capsys):
    submit = import_module("eval.submit")

    def fake_run(case, folder):
        folder.mkdir(parents=True)
        (folder / "ANSWER.md").write_text("# Answer\n\n## Decision\n\nSYSTEM FAILURE — The extract stage failed.\n")
        (folder / "REASONING.md").write_text("# Reasoning\n")
        (folder / "run.json").write_text(json.dumps({"state": "failure", "fallback": case.name == "001"}))
        return case, 0, 1.0, ""

    monkeypatch.setattr(submit, "run_case", fake_run)
    monkeypatch.setattr(submit.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="abc\n"))
    out = tmp_path / "answers"
    assert submit.main([str(cases_dir(tmp_path, ("001", "002"))), "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    rows = {line.split("\t")[0]: line.split("\t") for line in printed.splitlines() if "\t" in line}
    assert rows["1"][4] == "y" and rows["2"][4] == "n"
    assert "total 2; fallback 1; missing 0" in printed
    assert "| y |" in (out / "README.md").read_text()  # README agrees: case 1 is a fallback
