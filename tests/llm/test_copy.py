from pathlib import Path

from agent.llm import copy, handover

DESIGN = (Path(__file__).resolve().parents[2] / "docs" / "design.md").read_text(encoding="utf-8")


def _design(template: str) -> str:
    return f'"{template}"'


def test_reply_templates_match_design_copy_verbatim():
    for template in (copy.HOLDING_REPLY, copy.REQUEST_INFO_REPLY, copy.PENDING_REPLY):
        assert _design(template) in DESIGN


def test_filled_templates():
    assert handover.request_info_reply("which payment you mean?") == (
        "To make sure we act on the right request, please confirm: which payment you mean")
    assert handover.pending_reply("our payments team", "register the return request.") == (
        "We've asked our payments team to register the return request. We'll reply here once they've confirmed.")
