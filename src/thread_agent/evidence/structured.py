"""Exact structured-field extraction; no inference from configuration to runtime."""

import json
import math
import tomllib
from datetime import date, datetime, time

from thread_agent.domain.records import AgentError
from thread_agent.evidence.json_objects import unique_object

MAX_FIELDS = 64


def fields(text: str, path: str) -> dict[str, object]:
    """Return scalar fields addressed by RFC 6901 JSON pointers, also for TOML."""
    try:
        data = (
            tomllib.loads(text)
            if path.lower().endswith(".toml")
            else json.loads(text, object_pairs_hook=unique_object)
        )
        result: dict[str, object] = {}

        def visit(value: object, pointer: str, depth: int) -> None:
            if depth > 16:
                raise AgentError("Source nesting exceeds the supported depth of 16.")
            if isinstance(value, dict):
                for key, item in value.items():
                    escaped = key.replace("~", "~0").replace("/", "~1")
                    visit(item, f"{pointer}/{escaped}", depth + 1)
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    visit(item, f"{pointer}/{index}", depth + 1)
            else:
                if isinstance(value, float) and not math.isfinite(value):
                    raise AgentError("Non-finite numbers are unsupported.")
                if isinstance(value, (date, datetime, time)):
                    value = value.isoformat()
                result[pointer] = value
                if len(result) > MAX_FIELDS:
                    raise AgentError(
                        f"Source exceeds {MAX_FIELDS} scalar fields; use a smaller file."
                    )
                if len(pointer) > 512:
                    raise AgentError("Field pointer exceeds 512 characters.")

        visit(data, "", 0)
        if not result:
            raise AgentError("Source has no scalar fields to report.")
        return result
    except (ValueError, RecursionError) as exc:
        raise AgentError("Source is not valid supported TOML/JSON.") from exc
