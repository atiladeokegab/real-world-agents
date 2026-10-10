"""Judgement cases: a practice case plus an injected fault where acting is wrong (AGENT_SPEC 4.8, 4.10)."""
import json
from pathlib import Path

CASES = json.loads((Path(__file__).parent / "judgement.json").read_text())


def judge(entry: dict, action: str | None, kind: str | None) -> bool:
    """Pass when the action is an expected one and not forbidden; 'tool_call:write' forbids write calls only."""
    forbidden = {action, f"{action}:{kind}"} & set(entry["forbidden"])
    return action in entry["expect"] and not forbidden
