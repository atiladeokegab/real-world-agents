"""§4.1 attachments -> text. Every file becomes text; nothing raises."""

from __future__ import annotations

from pathlib import Path

from agent.core.contracts import Attachment

_KIND_BY_SUFFIX = {
    ".csv": "csv",
    ".pdf": "pdf",
    ".txt": "text",
    ".md": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
}


def read_attachments(case_dir: Path) -> list[Attachment]:
    attach_dir = Path(case_dir) / "attachments"
    if not attach_dir.is_dir():
        return []
    return [_read_one(f) for f in sorted(attach_dir.iterdir()) if f.is_file()]


def _read_one(path: Path) -> Attachment:
    kind = _KIND_BY_SUFFIX.get(path.suffix.lower(), "other")
    try:
        if kind == "pdf":
            text = _pdf_text(path)
        elif kind == "image":
            # The shared contract exposes no vision call; the name still reaches the case.
            text = ""
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # unreadable input must never crash the ingestor
        kind, text = "other", f"[unreadable attachment: {type(exc).__name__}]"
    return Attachment(name=path.name, kind=kind, text=text)


def _pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
