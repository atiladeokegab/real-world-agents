from pathlib import Path

import pytest

from agent.ingest import load_case

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "examples"

WITH_ATTACHMENTS = sorted(p for p in EXAMPLES.iterdir() if (p / "attachments").is_dir())


def test_nine_practice_cases_have_attachments():
    assert len(WITH_ATTACHMENTS) == 9


@pytest.mark.parametrize("case_dir", WITH_ATTACHMENTS, ids=lambda p: p.name)
def test_every_attachment_becomes_text(case_dir):
    case = load_case(case_dir)
    on_disk = sorted(f.name for f in (case_dir / "attachments").iterdir() if f.is_file())

    assert [a.name for a in case.attachments] == on_disk
    for a in case.attachments:
        assert a.kind in {"csv", "pdf", "text"}
        assert a.text.strip()
        assert case.raw_files[f"attachments/{a.name}"] == a.text


def test_csv_attachment():
    case = load_case(EXAMPLES / "033")
    (a,) = case.attachments
    assert a.name == "transactions-033.csv"
    assert a.kind == "csv"
    assert "amount_gbp" in a.text
    assert "-8.40" in a.text


def test_pdf_attachment():
    case = load_case(EXAMPLES / "031")
    (a,) = case.attachments
    assert a.name == "statement-031.pdf"
    assert a.kind == "pdf"
    assert len(a.text) > 20
    assert "Harrow" in a.text or "statement" in a.text.lower()


def test_txt_attachment():
    case = load_case(EXAMPLES / "039")
    (a,) = case.attachments
    assert a.name == "sessions-039.txt"
    assert a.kind == "text"
    assert "ALLOWED SESSION" in a.text


def _make_case(tmp_path: Path, attachment_files: dict[str, bytes]) -> Path:
    case_dir = tmp_path / "999"
    (case_dir / "attachments").mkdir(parents=True)
    (case_dir / "index.md").write_text("# Case 999: T\n\n## Case details\n\n- **Source role:** Bank customer\n\n## Initial request\n\nhelp\n")
    (case_dir / "history.md").write_text("# h\n\n<a id=\"event-001\"></a>\n## 2025-01-01 09:00:00 UTC — event 001\n\n- **Channel:** External message\n- **From:** X\n- **To:** H&V agent\n\nhi\n")
    for name, data in attachment_files.items():
        (case_dir / "attachments" / name).write_bytes(data)
    return case_dir


def test_unknown_extension_read_as_text(tmp_path):
    case_dir = _make_case(tmp_path, {"notes.foo": b"plain text content"})
    (a,) = load_case(case_dir).attachments
    assert a.kind == "other"
    assert a.text == "plain text content"


def test_unreadable_pdf_never_crashes(tmp_path):
    case_dir = _make_case(tmp_path, {"broken.pdf": b"not a pdf at all"})
    (a,) = load_case(case_dir).attachments
    assert a.kind == "other"
    assert a.text


def test_image_registered_without_text(tmp_path):
    case_dir = _make_case(tmp_path, {"scan.png": b"\x89PNG\r\n\x1a\nfake"})
    (a,) = load_case(case_dir).attachments
    assert a.kind == "image"
