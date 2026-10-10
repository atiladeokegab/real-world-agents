"""The one door to Claude: every model call in the agent goes through structured()."""

import hashlib
import json
import os
from contextvars import ContextVar
from typing import Literal, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

DEFAULT_MODEL = "claude-opus-5-5"
# Opus 5.5 defaults to "medium"; set it explicitly. Other stages (ingest's fallback) get medium.
EFFORT = {"extraction": "medium", "decision": "high"}
T = TypeVar("T", bound=BaseModel)

# The loop sets this to the case's trace list; each call appends one record (§4.9 trace.log).
TRACE: ContextVar[list | None] = ContextVar("TRACE", default=None)


def _client(stage: str) -> anthropic.Anthropic:
    # Other stages (e.g. ingest's fallback parse) share the extraction key unless given their own.
    key = (os.environ.get(f"ANTHROPIC_API_KEY_{stage.upper()}") or os.environ.get("ANTHROPIC_API_KEY")
           or os.environ.get("ANTHROPIC_API_KEY_EXTRACTION"))
    # The SDK retries 429/5xx with exponential backoff; 6 retries rides out a busy minute.
    return anthropic.Anthropic(api_key=key, max_retries=6)


def _constrainable(schema) -> bool:
    """False if any object is free-form (a dict[str, Any] field). The SDK silently rewrites
    those to `{"properties": {}, "additionalProperties": false}`, forcing them empty, so
    structured outputs would lose Proposal.params, escalation, ToolResult.data and the like."""
    if isinstance(schema, dict):
        if schema.get("type") == "object" and "properties" not in schema:
            return False
        return all(_constrainable(v) for v in schema.values())
    if isinstance(schema, list):
        return all(_constrainable(v) for v in schema)
    return True


def _record(stage, model_id, system, user, run, path, output, error):
    trace = TRACE.get()
    if trace is not None:
        trace.append({"step": "model_call", "stage": stage, "model": model_id, "path": path,
                      "prompt_version": hashlib.sha1(system.encode()).hexdigest()[:8],
                      "run": run, "user": user, "output": output,
                      "error": str(error) if error else None})


def _refused(resp, stage):
    if resp.stop_reason == "refusal":  # the loop's crash fallback escalates it
        raise RuntimeError(f"{stage}: model refused ({getattr(resp, 'stop_details', None)})")


def structured(stage: Literal["extraction", "decision"] | str, system: str, user: str,
               model: type[T], model_id: str = DEFAULT_MODEL) -> T:
    """One Claude call whose answer is a validated `model` instance.

    Structured outputs (messages.parse) when the schema can be constrained exactly; otherwise,
    or if parse() rejects the schema, the tool path below. No `thinking`: adaptive is the default.
    """
    effort = {"effort": EFFORT.get(stage, "medium")}
    if _constrainable(model.model_json_schema()):
        try:
            resp = _client(stage).messages.parse(
                model=model_id, max_tokens=16000, system=system, output_format=model,
                messages=[{"role": "user", "content": user}], output_config=effort)
        except (anthropic.BadRequestError, TypeError) as e:
            _record(stage, model_id, system, user, 1, "parse", None, e)
        else:
            _refused(resp, stage)
            _record(stage, model_id, system, user, 1, "parse",
                    resp.parsed_output.model_dump_json() if resp.parsed_output else None, None)
            if resp.parsed_output is not None:
                return resp.parsed_output

    # Tool path: Opus 5.5 rejects a forced tool_choice (400), so the tool is offered with
    # `auto` and the prompt says to call it; one re-ask if it doesn't.
    tool = {"name": model.__name__, "description": f"Return the {model.__name__}.",
            "input_schema": model.model_json_schema()}
    system = f"{system}\n\nAnswer only by calling the {model.__name__} tool, exactly once."
    error = None
    for attempt in (1, 2):
        resp = _client(stage).messages.create(
            model=model_id, max_tokens=16000, system=system, tools=[tool],
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=[{"role": "user", "content": user}], output_config=effort,
        )
        _refused(resp, stage)
        block = next((b for b in resp.content if b.type == "tool_use"), None)
        try:
            if block is None:
                raise ValueError(f"no {model.__name__} tool call (stop_reason={resp.stop_reason})")
            out = model.model_validate(block.input)
            error = None
        except (ValidationError, ValueError) as e:
            error = e
        _record(stage, model_id, system, user, attempt, "tool",
                json.dumps(block.input, default=str) if block else None, error)
        if error is None:
            return out
    raise RuntimeError(f"{stage}: {error}")
