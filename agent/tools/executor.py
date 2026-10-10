"""§4.7 executor: runs approved tool calls exactly once.

Every write carries an idempotency key computed here from the intent (case, tool, key fields);
the model never sees it. A per-case ledger in `ledger_dir` records each write before and after
the call, so a repeated intent returns the recorded result instead of acting twice."""

import hashlib
import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agent.tools import mock
from agent.tools._contracts import ToolResult, ToolSpec
from agent.tools.catalogue import CATALOGUE, service_of

Backend = Callable[[ToolSpec, dict, Any, list], ToolResult]

_WRITE_WORDS = re.compile(r"cancel|amend|change|block|release|return|revoke|remove|add|dispute|submit|register|"
                          r"place|send|update|stop|reissue")


def _norm(value: Any) -> str:
    s = re.sub(r"[£,\s]", "", str(value if value is not None else "")).lower()
    try:
        return f"{float(s):.2f}"
    except ValueError:
        return s


def intent_key(case_id: str, spec: ToolSpec, params: dict) -> str:
    intent = [case_id, spec.name, {f: _norm(params.get(f)) for f in spec.key_fields}]
    return hashlib.sha256(json.dumps(intent, sort_keys=True).encode()).hexdigest()


class Ledger:
    """One JSON file per case; replaced atomically so a killed run never leaves half a ledger."""

    def __init__(self, ledger_dir, case_id: str):
        self.path = Path(ledger_dir) / f"{re.sub(r'[^A-Za-z0-9_-]', '_', case_id or 'case')}.json"
        self.entries: dict[str, dict] = json.loads(self.path.read_text()) if self.path.exists() else {}

    def put(self, key: str, entry: dict) -> None:
        self.entries[key] = entry
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(self.entries, indent=1, default=str))
        os.replace(tmp, self.path)

    def clash(self, key: str, service: str, target: str) -> dict | None:
        return next((e for k, e in self.entries.items()
                     if k != key and e["service"] == service and e["target"] == target), None)


def _error(tool: str, params: dict, detail: str, **data) -> ToolResult:
    return ToolResult(tool=tool or "", params=params, status="error", data={"detail": detail, **data})


def _read(spec: ToolSpec, params: dict, case, practice_events: list, backend: Backend) -> ToolResult:
    for attempt in (1, 2):  # reads may retry once
        try:
            return backend(spec, params, case, practice_events)
        except TimeoutError:
            last = ToolResult(tool=spec.name, params=params, status="timeout", data={"attempts": attempt})
        except Exception as e:
            last = _error(spec.name, params, f"{type(e).__name__}: {e}", attempts=attempt)
    return last


def _write(spec: ToolSpec, params: dict, case, practice_events: list, backend: Backend, ledger_dir) -> ToolResult:
    case_id = getattr(case, "case_id", "") or ""
    ledger = Ledger(ledger_dir, case_id)
    key = intent_key(case_id, spec, params)
    if key in ledger.entries:  # same intent already done: return what happened, don't call again
        return ToolResult(**ledger.entries[key]["result"])
    service, target = service_of(spec.name), _norm(params.get(spec.key_fields[0]))
    other = ledger.clash(key, service, target)
    if other:
        return _error(spec.name, params, "a different change on the same target is already recorded; escalate",
                      blocked=True, recorded_tool=other["tool"])
    uncertain = ToolResult(tool=spec.name, params=params, status="uncertain",
                           data={"read_back": spec.read_back, "read_strength": spec.read_strength})
    entry = {"tool": spec.name, "service": service, "target": target, "params": params}
    ledger.put(key, {**entry, "result": uncertain.model_dump(mode="json")})  # in flight until it returns
    try:
        result = backend(spec, params, case, practice_events)
    except Exception as e:  # no write retries: the outcome is unknown
        result = uncertain.model_copy(update={"data": {**uncertain.data, "detail": f"{type(e).__name__}: {e}"}})
    ledger.put(key, {**entry, "result": result.model_dump(mode="json")})
    return result


def run(proposal, case, ledger_dir, practice_events: list | None = None, backend: Backend = mock.call) -> ToolResult:
    tool = getattr(proposal, "tool", None)
    params = dict(getattr(proposal, "params", None) or {})
    if getattr(proposal, "action", "tool_call") != "tool_call":
        return _error(tool, params, "not a tool_call")
    spec = CATALOGUE.get(tool or "")
    if spec is None:
        return _error(tool, params, f"unknown tool {tool!r}")
    if spec.risk == 1:
        verb = str(params.get("action") or params.get("operation") or "").lower()
        if _WRITE_WORDS.search(verb):  # a change asked of a read tool: never let it pass as a lookup
            writes = sorted(n for n in CATALOGUE if n.startswith(spec.name + "."))
            return _error(tool, params, f"{tool} only reads; changes use one of {writes}", write_tools=writes)
        return _read(spec, params, case, practice_events or [], backend)
    return _write(spec, params, case, practice_events or [], backend, ledger_dir)
