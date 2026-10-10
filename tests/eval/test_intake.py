import json
import tarfile
import zipfile
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

from eval.intake import normalise_input


def case_dirs(root: Path) -> dict[str, Path]:
    return {p.name: p for p in root.iterdir() if p.is_dir()}


def practice_case(folder: Path, n: str) -> Path:
    (folder / n).mkdir(parents=True)
    (folder / n / "index.md").write_text(f"# Case {n}: t\n\n## Initial request\n\nhelp {n}\n")
    (folder / n / "history.md").write_text("events")
    return folder / n


def test_folder_of_case_folders_is_used_as_is(tmp_path, capsys):
    for n in ("001", "002"):
        practice_case(tmp_path, n)
    assert normalise_input(tmp_path) == tmp_path
    assert "folder of case folders; 2 case(s)" in capsys.readouterr().out


def test_shared_top_level_files_reach_every_case(tmp_path):
    src = tmp_path / "in"
    for n in ("1", "2"):
        practice_case(src, n)
    (src / "tools.json").write_text('{"tools": ["transfer_journal"]}')
    out = normalise_input(src)
    assert out != src and set(case_dirs(out)) == {"1", "2"}
    for case in case_dirs(out).values():
        assert (case / "attachments" / "tools.json").read_text() == '{"tools": ["transfer_journal"]}'
        assert (case / "history.md").read_text() == "events"
    assert not (src / "1" / "attachments").exists()  # the input is never changed


def test_zip_with_a_wrapping_folder(tmp_path):
    src = tmp_path / "src" / "Banking"
    for n in ("003", "004"):
        practice_case(src, n)
    archive = tmp_path / "cases.zip"
    with zipfile.ZipFile(archive, "w") as z:
        for f in (tmp_path / "src").rglob("*"):
            z.write(f, f.relative_to(tmp_path / "src"))
    out = normalise_input(archive)
    assert set(case_dirs(out)) == {"003", "004"}
    assert (out / "003" / "index.md").read_text().startswith("# Case 003")


def test_tar_gz_of_loose_files(tmp_path):
    loose = tmp_path / "loose"
    loose.mkdir()
    (loose / "case_7.txt").write_text("Customer asks to cancel a standing order.")
    (loose / "case_8.md").write_text("Customer asks where a refund is.")
    archive = tmp_path / "cases.tar.gz"
    with tarfile.open(archive, "w:gz") as t:
        t.add(loose, arcname="loose")
    out = normalise_input(archive)
    assert set(case_dirs(out)) == {"7", "8"}


def test_loose_files_one_case_each_with_shared_data(tmp_path):
    (tmp_path / "case-12.md").write_text("Please block my card.")
    (tmp_path / "case-13.eml").write_text("Subject: refund\n\nWhere is my refund?")
    (tmp_path / "case-14.pdf").write_bytes(b"%PDF-1.4 fake")
    (tmp_path / "records.json").write_text('{"journal": []}')
    out = normalise_input(tmp_path)
    cases = case_dirs(out)
    assert set(cases) == {"12", "13", "14"}
    assert "Please block my card." in (cases["12"] / "index.md").read_text()
    assert "## Initial request" in (cases["13"] / "index.md").read_text()
    assert (cases["14"] / "attachments" / "case-14.pdf").read_bytes() == b"%PDF-1.4 fake"
    assert "See the attached file case-14.pdf." in (cases["14"] / "index.md").read_text()
    assert all((c / "attachments" / "records.json").is_file() for c in cases.values())


def test_markdown_file_split_on_case_headings_keeps_the_preamble(tmp_path):
    f = tmp_path / "reality.md"
    f.write_text("Bank: Harrow & Vale\n\n# Case 21\nCancel my DD.\n\n## Case 22\nWas my transfer sent?\n\n"
                 "Case 23: Card declined twice.\n")
    out = normalise_input(f)
    cases = case_dirs(out)
    assert set(cases) == {"21", "22", "23"}
    text = (cases["22"] / "index.md").read_text()
    assert "Was my transfer sent?" in text and "Bank: Harrow & Vale" in text and "Cancel my DD" not in text


def test_text_file_split_on_rules_numbered_in_order(tmp_path):
    f = tmp_path / "cases.txt"
    f.write_text("first request\n---\nsecond request\n---\nthird request\n")
    cases = case_dirs(normalise_input(f))
    assert set(cases) == {"1", "2", "3"}
    assert "second request" in (cases["2"] / "index.md").read_text()


def test_json_list_with_tools_as_attachment(tmp_path):
    f = tmp_path / "cases.json"
    f.write_text(json.dumps([
        {"id": "case-31", "request": "Stop my standing order", "tools": [{"name": "so_journal"}]},
        {"id": "case-32", "request": "Fee query", "records": {"fee": 4.5}},
    ]))
    cases = case_dirs(normalise_input(f))
    assert set(cases) == {"31", "32"}
    assert "request: Stop my standing order" in (cases["31"] / "index.md").read_text()
    assert json.loads((cases["31"] / "attachments" / "tools.json").read_text()) == {"tools": [{"name": "so_journal"}]}
    assert json.loads((cases["32"] / "attachments" / "tools.json").read_text()) == {"records": {"fee": 4.5}}


def test_json_dict_of_cases(tmp_path):
    f = tmp_path / "cases.json"
    f.write_text(json.dumps({"case 41": "Block card", "case 42": {"message": "Refund?"}}))
    cases = case_dirs(normalise_input(f))
    assert set(cases) == {"41", "42"} and "message: Refund?" in (cases["42"] / "index.md").read_text()


def test_csv_one_row_per_case(tmp_path):
    f = tmp_path / "cases.csv"
    f.write_text("case_id,customer,message\n51,Ann,Cancel DD\n52,Bo,Where is my money\n")
    cases = case_dirs(normalise_input(f))
    assert set(cases) == {"51", "52"} and "message: Where is my money" in (cases["52"] / "index.md").read_text()


def test_unsplittable_file_is_one_case(tmp_path):
    f = tmp_path / "case_60.txt"
    f.write_text("One long messy customer complaint with no headings at all.")
    cases = case_dirs(normalise_input(f))
    assert set(cases) == {"60"}
    assert (cases["60"] / "attachments" / "case_60.txt").read_text().startswith("One long messy")


def test_corrupt_archive_still_gives_a_case(tmp_path, capsys):
    f = tmp_path / "cases.zip"
    f.write_bytes(b"not a zip")
    cases = case_dirs(normalise_input(f))
    assert len(cases) == 1 and "one case per file" in capsys.readouterr().out


def test_submit_runs_a_single_file(tmp_path, monkeypatch):
    submit = import_module("eval.submit")
    f = tmp_path / "reality.md"
    f.write_text("# Case 1\nfirst\n# Case 2\nsecond\n")
    seen = []

    def fake_run(case, folder):
        seen.append((case / "index.md").read_text())
        folder.mkdir(parents=True)
        (folder / "ANSWER.md").write_text("# Answer\n\n## Decision\n\nDONE — ok.\n")
        (folder / "REASONING.md").write_text("# Reasoning\n")
        return case, 0, 1.0, ""

    monkeypatch.setattr(submit, "run_case", fake_run)
    monkeypatch.setattr(submit.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="abc\n"))
    out = tmp_path / "answers"
    assert submit.main([str(f), "--out", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir() if p.is_dir()) == ["1", "2"]
    assert any("second" in s for s in seen)


def test_track_name_survives_the_copy(tmp_path):
    src = tmp_path / "Banking & Financial Services"
    practice_case(src, "1")
    (src / "README.md").write_text("Rules for these cases.")
    out = normalise_input(src)
    assert out.name == "Banking & Financial Services"  # ingest reads the track from the parent's name
    assert (out / "1" / "attachments" / "README.md").read_text() == "Rules for these cases."
