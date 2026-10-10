"""The one door to Claude: agent.core.llm.structured (#12)."""

from __future__ import annotations

import importlib
import inspect
from typing import Literal, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)

_SCHEMA_PARAMS = ("schema", "response_model", "output_model", "output_type", "model_cls")


def call(stage: Literal["extraction", "decision"], system: str, user: str, schema: type[M]) -> M:
    structured = importlib.import_module("agent.core.llm").structured
    try:
        params = inspect.signature(structured).parameters
    except (TypeError, ValueError):
        params = {}
    for name in _SCHEMA_PARAMS:
        if name in params:
            result = structured(stage, system, user, **{name: schema})
            break
    else:
        result = structured(stage, system, user, schema)
    if isinstance(result, schema):
        return result
    if isinstance(result, BaseModel):
        return schema.model_validate(result.model_dump())
    return schema.model_validate(result)
