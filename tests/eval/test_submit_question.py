from importlib import import_module

from tests.eval.test_submit import cases, fake_uv

submit = import_module("eval.submit")


def test_file_question_wins_over_section(tmp_path):
    case = cases(tmp_path, "001") / "001"
    (case / "index.md").write_text("# Case\n\n## Question\nFrom index\n")
    (case / "Decision_point.txt").write_text("Should we refund?\n")
    (case / "history.md").write_text("x")
    assert submit.find_question(case) == "Should we refund?"


def test_index_section_questions_numbered(tmp_path):
    case = cases(tmp_path, "001") / "001"
    (case / "index.md").write_text("# Case\n\nintro\n\n## Question\nWhy declined?\n\n## Overview\nno\n\n### What should H&V do next?\nCheck it.\n")
    assert submit.find_question(case) == "1. Why declined?\n2. Check it."


def test_none(tmp_path):
    assert submit.find_question(cases(tmp_path, "001") / "001") is None


def test_question_is_passed_and_shown(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "001", "002")
    (root / "001" / "question.md").write_text("Is it safe?")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
a = sys.argv
out = pathlib.Path(a[a.index('--out') + 1])
out.mkdir(parents=True)
q = a[a.index('--question') + 1] if '--question' in a else 'none'
(out / 'ANSWER.md').write_text('## Decision\\n' + q + '\\n')
(out / 'REASONING.md').write_text('r')
""")
    out = tmp_path / "answers"
    assert submit.main([str(root), "--out", str(out)]) == 0
    table = capsys.readouterr().out
    assert "1\t0\t" in table and "Is it safe?\tn\ty" in table and "none\tn\tn" in table
