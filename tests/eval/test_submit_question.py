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


def test_unreadable_question_does_not_stop_the_run(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "001")

    def boom(case):
        raise PermissionError("denied")

    monkeypatch.setattr(submit, "find_question", boom)
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
out = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('## Decision\\nok\\n')
(out / 'REASONING.md').write_text('r')
""")
    assert submit.main([str(root), "--out", str(tmp_path / "a")]) == 0
    assert "case 001: could not read a question" in capsys.readouterr().err


def test_folder_without_index_or_history_is_still_a_case(tmp_path, monkeypatch):
    root = cases(tmp_path, "1")
    odd = root / "2"
    odd.mkdir()
    (odd / "request.md").write_text("help")
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("x")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
out = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('## Decision\\nok\\n')
(out / 'REASONING.md').write_text('r')
""")
    out = tmp_path / "a"
    assert submit.main([str(root), "--out", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir() if p.is_dir()) == ["1", "2"]


def test_duplicate_case_numbers_are_all_run(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "case-1", "Case 01", "2")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
out = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('## Decision\\nok\\n')
(out / 'REASONING.md').write_text('r')
""")
    out = tmp_path / "a"
    assert submit.main([str(root), "--out", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir() if p.is_dir()) == ["1", "2", "3"]
    assert "duplicate case number" in capsys.readouterr().err
