import os
import time
from importlib import import_module


def fake_uv(tmp_path, monkeypatch, body):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    command = bin_dir / "uv"
    command.write_text("#!/usr/bin/env python3\n" + body)
    command.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


def cases(tmp_path, *names):
    root = tmp_path / "cases"
    root.mkdir()
    for name in names:
        folder = root / name
        folder.mkdir()
        (folder / "index.md").write_text(f"Case {name}\n")
    return root


def test_zero_padded_cases_use_unpadded_output_numbers(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "003", "001", "002", "notes")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
assert sys.argv[1:4] == ['run', 'agent', 'run']
assert sys.argv[4] == '--case' and sys.argv[6] == '--out'
case = pathlib.Path(sys.argv[5])
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('# Case\\n\\n## Decision\\nescalate\\n')
(out / 'REASONING.md').write_text('# Reasoning\\n')
""")
    out = tmp_path / "answers"

    assert import_module("eval.submit").main(
        [str(root), "--out", str(out), "--workers", "2", "--limit", "2"]
    ) == 0

    assert sorted(p.name for p in out.iterdir()) == ["1", "2"]
    assert all((out / n / "REASONING.md").is_file() for n in ("1", "2"))
    table = capsys.readouterr().out
    assert "001 -> 1" in table and "002 -> 2" in table and "escalate" in table
    assert "fallback" in table and "HEAD" in table


def test_case_prefixed_folder_is_discovered_and_numbered(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "case-1")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('## Decision\\nrequest_info\\n')
(out / 'REASONING.md').write_text('# Reasoning\\n')
""")
    out = tmp_path / "answers"

    assert import_module("eval.submit").main([str(root), "--out", str(out)]) == 0
    assert (out / "1" / "ANSWER.md").is_file()
    assert "case-1 -> 1" in capsys.readouterr().out


def test_unnumbered_folders_get_sorted_unused_numbers(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "beta", "case-2", "alpha")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('## Decision\\nrequest_info\\n')
(out / 'REASONING.md').write_text('# Reasoning\\n')
""")
    out = tmp_path / "answers"

    assert import_module("eval.submit").main([str(root), "--out", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["1", "2", "3"]
    mapping = capsys.readouterr().out
    assert "alpha -> 1" in mapping and "case-2 -> 2" in mapping and "beta -> 3" in mapping


def test_empty_cases_dir_exits_with_named_error(tmp_path, capsys):
    root = cases(tmp_path, "notes")
    (root / "notes" / "index.md").unlink()

    assert import_module("eval.submit").main([str(root)]) == 1
    assert str(root) in capsys.readouterr().err


def test_workers_run_cases_at_the_same_time(tmp_path, monkeypatch):
    root = cases(tmp_path, "001", "002")
    sync = tmp_path / "sync"
    sync.mkdir()
    monkeypatch.setenv("FAKE_SYNC_DIR", str(sync))
    fake_uv(tmp_path, monkeypatch, """import os, pathlib, sys, time
case = pathlib.Path(sys.argv[5])
sync = pathlib.Path(os.environ['FAKE_SYNC_DIR'])
(sync / case.name).touch()
end = time.monotonic() + 1
while len(list(sync.iterdir())) < 2:
    if time.monotonic() > end:
        sys.exit(9)
    time.sleep(0.01)
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('## Decision\\nno-op\\n')
(out / 'REASONING.md').write_text('# Reasoning\\n')
""")
    out = tmp_path / "answers"

    assert import_module("eval.submit").main([str(root), "--out", str(out), "--workers", "2"]) == 0
    assert all((out / n / "ANSWER.md").read_text().endswith("no-op\n") for n in ("1", "2"))


def test_malformed_answer_text_does_not_stop_other_cases(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "001", "002")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_bytes(b'\\xff\\n## Decision\\nno-op\\n')
(out / 'REASONING.md').write_text('# Reasoning\\n')
""")
    out = tmp_path / "answers"

    assert import_module("eval.submit").main([str(root), "--out", str(out)]) == 0
    assert "total 2; fallback 0; missing 0" in capsys.readouterr().out


def test_rerun_preserves_existing_answer_and_fills_partial_case(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "001", "002")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True, exist_ok=True)
(out / 'ANSWER.md').write_text('## Decision\\nchanged\\n')
(out / 'REASONING.md').write_text('# Reasoning\\n')
""")
    out = tmp_path / "answers"
    (out / "1").mkdir(parents=True)
    original = "## Decision\nescalate (needs review)\n"
    (out / "1" / "ANSWER.md").write_text(original)

    assert import_module("eval.submit").main([str(root), "--out", str(out)]) == 0

    assert (out / "1" / "ANSWER.md").read_text() == original
    assert "system failure" in (out / "1" / "REASONING.md").read_text()
    assert (out / "2" / "ANSWER.md").read_text().endswith("changed\n")
    assert "1\tskipped\t" in capsys.readouterr().out


def test_failed_case_gets_fallback_without_stopping_next_case(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "001", "002")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys
case = pathlib.Path(sys.argv[5])
if case.name == '001':
    sys.exit(7)
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('## Decision\\nno-op\\n')
(out / 'REASONING.md').write_text('# Reasoning\\n')
""")
    out = tmp_path / "answers"

    assert import_module("eval.submit").main([str(root), "--out", str(out)]) == 0

    assert "escalate (system failure)" in (out / "1" / "ANSWER.md").read_text()
    assert "index.md" in (out / "1" / "REASONING.md").read_text()
    assert (out / "2" / "ANSWER.md").read_text().endswith("no-op\n")
    table = capsys.readouterr().out
    assert "1\t7\t" in table and "2\t0\t" in table
    assert "system failure" in table and "total 2; fallback 1; missing 0" in table


def test_timeout_keeps_written_answer_and_fills_missing_reasoning(tmp_path, monkeypatch, capsys):
    root = cases(tmp_path, "001", "002")
    fake_uv(tmp_path, monkeypatch, """import pathlib, sys, time
case = pathlib.Path(sys.argv[5])
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True)
(out / 'ANSWER.md').write_text('## Decision\\nescalate (needs review)\\n')
if case.name == '001':
    time.sleep(1)
(out / 'REASONING.md').write_text('# Reasoning\\n')
""")
    monkeypatch.setattr(import_module("eval.submit"), "CASE_TIMEOUT", 0.1)
    out = tmp_path / "answers"

    assert import_module("eval.submit").main([str(root), "--out", str(out), "--workers", "2"]) == 0

    assert (out / "1" / "ANSWER.md").read_text() == "## Decision\nescalate (needs review)\n"
    assert "system failure" in (out / "1" / "REASONING.md").read_text()
    assert (out / "2" / "REASONING.md").read_text() == "# Reasoning\n"
    assert "fallback 1; missing 0" in capsys.readouterr().out


def test_timeout_stops_child_before_it_can_change_fallback(tmp_path, monkeypatch):
    root = cases(tmp_path, "001")
    fake_uv(tmp_path, monkeypatch, """import pathlib, subprocess, sys, time
out = pathlib.Path(sys.argv[7])
out.mkdir(parents=True)
subprocess.Popen([sys.executable, '-c',
    'import pathlib,sys,time; time.sleep(0.35); pathlib.Path(sys.argv[1]).write_text("late")',
    str(out / 'late.txt')])
time.sleep(1)
""")
    monkeypatch.setattr(import_module("eval.submit"), "CASE_TIMEOUT", 0.1)
    out = tmp_path / "answers"

    assert import_module("eval.submit").main([str(root), "--out", str(out)]) == 0
    time.sleep(0.4)

    assert "system failure" in (out / "1" / "ANSWER.md").read_text()
    assert not (out / "1" / "late.txt").exists()
