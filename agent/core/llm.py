"""The one door to Claude: every model call in the agent goes through structured()."""

import hashlib
import json
import os
from contextvars import ContextVar
from typing import Literal, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

DEFAULT_MODEL = "claude-opus-5-5"
T = TypeVar("T", bound=BaseModel)

# The loop sets this to the case's trace list; each call appends one record (§4.9 trace.log).
TRACE: ContextVar[list | None] = ContextVar("TRACE", default=None)


def _client(stage: str) -> anthropic.Anthropic:
    # Other stages (e.g. ingest's fallback parse) share the extraction key unless given their own.
    key = (os.environ.get(f"ANTHROPIC_API_KEY_{stage.upper()}") or os.environ.get("ANTHROPIC_API_KEY")
           or os.environ.get("ANTHROPIC_API_KEY_EXTRACTION"))
    # The SDK retries 429/5xx with exponential backoff; 6 retries rides out a busy minute.
    return anthropic.Anthropic(api_key=key, max_retries=6)


def structured(stage: Literal["extraction", "decision"] | str, system: str, user: str,
               model: type[T], model_id: str = DEFAULT_MODEL) -> T:
    """One Claude call whose answer is a validated `model` instance.

    The schema rides as a tool's input_schema. Opus 5.5 rejects a forced tool_choice (400),
    so the tool is offered with `auto` and the prompt says to call it; one re-ask if it doesn't.
    """
    tool = {"name": model.__name__, "description": f"Return the {model.__name__}.",
            "input_schema": model.model_json_schema()}
    system = f"{system}\n\nAnswer only by calling the {model.__name__} tool, exactly once."
    trace = TRACE.get()
    error = None
    for attempt in (1, 2):
        resp = _client(stage).messages.create(
            model=model_id, max_tokens=16000, system=system, tools=[tool],
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=[{"role": "user", "content": user}],
        )
        block = next((b for b in resp.content if b.type == "tool_use"), None)
        try:
            if block is None:
                raise ValueError(f"no {model.__name__} tool call (stop_reason={resp.stop_reason})")
            out = model.model_validate(block.input)
            error = None
        except (ValidationError, ValueError) as e:
            error = e
        if trace is not None:
            trace.append({"step": "model_call", "stage": stage, "model": model_id,
                          "prompt_version": hashlib.sha1(system.encode()).hexdigest()[:8],
                          "run": attempt, "user": user,
                          "output": json.dumps(block.input, default=str) if block else None,
                          "error": str(error) if error else None})
        if error is None:
            return out
    raise RuntimeError(f"{stage}: {error}")
