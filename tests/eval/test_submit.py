import os
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


def test_numbered_cases_limit_and_summary(tmp_path, monkeypatch, capsys):
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

    assert sorted(p.name for p in out.iterdir()) == ["001", "002"]
    assert all((out / n / "REASONING.md").is_file() for n in ("001", "002"))
    table = capsys.readouterr().out
    assert "001" in table and "002" in table and "escalate" in table
    assert "fallback" in table and "HEAD" in table
