"""A spoken request becomes an examples-format case folder, runs through run_case, and the customer reply comes back."""

import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BANK = "Harrow & Vale Bank plc"


def _neutralise(text: str) -> str:
    """Caller words must never parse as markup: no anchors, headings or field lines, so ingest sees one event."""
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return "\n".join(" " + l if l.lstrip().startswith(("#", "- **", "---")) else l for l in text.splitlines())


def build_case(text: str, caller: str = "Caller", verified: bool = False, root: Path | None = None) -> Path:
    """Write index.md + history.md. Authority comes from the channel: only a platform-verified call is `Verified call`."""
    text = _neutralise(text)
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    path = Path(tempfile.mkdtemp(prefix="voice-", dir=root))
    (path / "index.md").write_text(
        f"# Case voice-{now:%H%M%S}: Spoken request\n\n## Case details\n\n- **Source role:** Bank customer\n"
        f"- **Created:** {stamp}\n\n## Initial request\n\n{text}\n", encoding="utf-8")
    (path / "history.md").write_text(
        f"# Case voice history — Spoken request\n\nTotal events: 1\n\n"
        f'<a id="event-001"></a>\n## {stamp} — event 001\n\n'
        f"- **Channel:** {'Verified call' if verified else 'External message'}\n"
        f"- **From:** {caller}\n- **To:** {BANK}\n\n{text}\n", encoding="utf-8")
    return path


def customer_reply(answer_dir: Path) -> str:
    m = re.search(r"## Customer (?:reply|message)\n\n?(?:Channel:[^\n]*\n\n)?(.*?)\n*(?:\n## |\Z)", (answer_dir / "ANSWER.md").read_text(encoding="utf-8"), re.S)  # new and old heading
    return m.group(1).strip() if m else ""


def handle(text: str, caller: str = "Caller", verified: bool = False, out: Path | None = None, run_case=None) -> str:
    if run_case is None:
        from agent.core.loop import run_case  # lazy: the loop may land after this module
    out = Path(out) if out else Path(tempfile.mkdtemp(prefix="voice-out-"))
    out.mkdir(parents=True, exist_ok=True)
    return customer_reply(Path(run_case(build_case(text, caller, verified, root=out), out / "answer")))
