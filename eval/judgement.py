"""Judgement cases: a practice case plus an injected fault where acting is wrong (AGENT_SPEC 4.8, 4.10)."""
import json
from pathlib import Path

CASES = json.loads((Path(__file__).parent / "judgement.json").read_text())


def judge(entry: dict, final_action: str | None, wrote: bool) -> bool:
    """Pass when the FINAL action is expected, not forbidden, and no write executed anywhere in the trace.
    'tool_call:write' in forbidden means: no executed write at all."""
    if "tool_call:write" in entry["forbidden"] and wrote:
        return False
    return final_action in entry["expect"] and final_action not in entry["forbidden"]
