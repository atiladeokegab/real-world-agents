"""Fault injection on the tools layer for the eval (§4.3, §4.10.3).

`with_faults(fault, seed)` returns an `execute` with the same signature whose mock services
misbehave; `AGENT_TOOL_FAULT=<fault>` (and `AGENT_TOOL_FAULT_SEED`) does the same for every
`agent.tools.execute` call, so the eval can inject through the real loop."""

import os
import random
import re

from agent.tools import mock
from agent.tools._contracts import ToolResult
from agent.tools.executor import Backend, run

FAULTS = ("timeout", "wrong_amount", "dropped_row")
AMOUNT = re.compile(r"£(\d[\d,]*(?:\.\d+)?)")


def _shift(text: str, factor: float) -> str:
    return AMOUNT.sub(lambda m: f"£{float(m.group(1).replace(',', '')) * factor:,.2f}", text)


def _wrong_amount(r: ToolResult, rng: random.Random) -> ToolResult:
    factor = 1 + rng.choice([-1, 1]) * rng.uniform(0.2, 0.6)
    data = {}
    for k, v in r.data.items():
        if isinstance(v, str):
            v = _shift(v, factor)
        elif isinstance(v, list):
            v = [_shift(x, factor) if isinstance(x, str) else x for x in v]
        elif k == "amount" and isinstance(v, (int, float)):
            v = round(v * factor, 2)
        data[k] = v
    return r.model_copy(update={"data": data})


def _dropped_row(r: ToolResult, rng: random.Random) -> ToolResult:
    lists = [k for k, v in r.data.items() if isinstance(v, list) and v]
    if not lists:
        return r
    k = max(lists, key=lambda k: len(r.data[k]))
    rows = list(r.data[k])
    rows.pop(rng.randrange(len(rows)))
    data = {**r.data, k: rows}
    if k == "lines" and "note" in data:
        data["note"] = "\n".join(rows)
    return r.model_copy(update={"data": data})


def backend(fault: str, seed: int = 0, inner: Backend = mock.call) -> Backend:
    if fault not in FAULTS:
        raise ValueError(f"unknown fault {fault!r}; one of {FAULTS}")
    rng = random.Random(seed)

    def call(spec, params, case, practice_events):
        if fault == "timeout":
            if spec.risk > 1:
                inner(spec, params, case, practice_events)  # the write lands, then the reply is lost
            raise TimeoutError(f"{spec.name} timed out (injected)")
        r = inner(spec, params, case, practice_events)
        return (_wrong_amount if fault == "wrong_amount" else _dropped_row)(r, rng)
    return call


def with_faults(fault: str | None, seed: int = 0):
    """An `execute(proposal, case, ledger_dir, practice_events=[])` with `fault` injected; None = clean."""
    b = backend(fault, seed) if fault else mock.call

    def execute(proposal, case, ledger_dir, practice_events=[]):
        return run(proposal, case, ledger_dir, list(practice_events), b)
    return execute


def from_env() -> Backend:
    fault = os.environ.get("AGENT_TOOL_FAULT", "").strip()
    return backend(fault, int(os.environ.get("AGENT_TOOL_FAULT_SEED", "0"))) if fault else mock.call
