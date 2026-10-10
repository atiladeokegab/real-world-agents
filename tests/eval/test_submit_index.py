import json
from importlib import import_module
from types import SimpleNamespace


def test_submit_writes_index_for_three_cases_with_missing_run_json(tmp_path, monkeypatch):
    submit = import_module("eval.submit")
    cases = tmp_path / "cases"
    cases.mkdir()
    for number in ("001", "002", "003"):
        (cases / number).mkdir()
        (cases / number / "index.md").write_text(f"# Case {number}\n")
    out = tmp_path / "answers"
    runs = {
        "001": ("DONE — Checked transfer_journal and replied on Secure chat.", {"state": "done"}),
        "002": ("ESCALATED — Handed to Payments | fraud: new bank details.",
                {"state": "escalated", "escalated": True}),
        "003": ("NO ACTION — Nothing needs doing.", None),  # no run.json written
    }

    def fake_run(case, folder):
        line, run = runs[case.name]
        folder.mkdir(parents=True)
        question = "\n## Answer to the question\n\nYes.\n" if case.name == "002" else ""
        (folder / "ANSWER.md").write_text(f"# Answer — Case {case.name}\n\n## Decision\n\n{line}\n{question}")
        (folder / "REASONING.md").write_text("# Reasoning\n")
        if run:
            (folder / "run.json").write_text(json.dumps({"escalated": False, "fallback": False, **run}))
        return case, 0, 12.34, ""

    monkeypatch.setattr(submit, "run_case", fake_run)
    monkeypatch.setattr(submit.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="abc123\n"))
    before = {p: p.read_bytes() for p in out.rglob("*")} if out.exists() else {}

    assert submit.main([str(cases), "--out", str(out)]) == 0
    index = (out / "README.md").read_text()
    assert "| [1](1/ANSWER.md) | DONE | Checked transfer_journal and replied on Secure chat. | n | n | n | 12.3 |" in index
    assert "| [2](2/ANSWER.md) | ESCALATED | Handed to Payments \\| fraud: new bank details. | y | n | y | 12.3 |" in index
    assert "| [3](3/ANSWER.md) | unknown | NO ACTION — Nothing needs doing. | unknown | unknown | n | 12.3 |" in index
    assert "**Totals:** 3 cases · DONE 1 · REQUESTED 0 · NEEDS INFO 0 · ESCALATED 1 · NO ACTION 0 · SYSTEM FAILURE 0 · unknown 1" in index
    assert "**Commit:** `abc123`" in index
    assert not before and sorted(p.name for p in out.iterdir()) == ["1", "2", "3", "README.md"]
    assert (out / "3" / "ANSWER.md").read_text().startswith("# Answer — Case 003")  # case files untouched


def test_index_reads_only_and_never_crashes_on_broken_files(tmp_path):
    submit = import_module("eval.submit")
    (tmp_path / "7").mkdir()
    (tmp_path / "7" / "run.json").write_text("{not json")
    (tmp_path / "notes").mkdir()  # not a case folder: ignored
    submit.write_index(tmp_path, None)
    index = (tmp_path / "README.md").read_text()
    assert "| [7](7/ANSWER.md) | unknown | unknown | unknown | unknown | unknown | unknown |" in index
    assert "notes" not in index and "Commit" not in index
    assert (tmp_path / "7" / "run.json").read_text() == "{not json"


def test_index_failure_only_warns(tmp_path, monkeypatch, capsys):
    submit = import_module("eval.submit")
    cases = tmp_path / "cases"
    (cases / "001").mkdir(parents=True)
    (cases / "001" / "index.md").write_text("# Case 001\n")
    out = tmp_path / "answers"

    def fake_run(case, folder):
        folder.mkdir(parents=True)
        (folder / "ANSWER.md").write_text("# Answer — Case 001\n\n## Decision\n\nDONE — Replied.\n")
        (folder / "REASONING.md").write_text("# Reasoning\n")
        return case, 0, 1.0, ""

    def broken_index(*a, **k):
        raise RuntimeError("disk full")

    monkeypatch.setattr(submit, "run_case", fake_run)
    monkeypatch.setattr(submit, "write_index", broken_index)
    monkeypatch.setattr(submit.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="abc123\n"))
    assert submit.main([str(cases), "--out", str(out)]) == 0
    assert "WARNING: could not write" in capsys.readouterr().err
    assert (out / "1" / "ANSWER.md").read_text().endswith("DONE — Replied.\n")
    assert not (out / "README.md").exists()
