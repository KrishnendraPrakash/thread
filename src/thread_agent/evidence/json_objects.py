"""Strict JSON objects shared by the editor and field CLI."""

from thread_agent.domain.records import AgentError


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise AgentError("Duplicate JSON keys are ambiguous; correct the source first.")
        result[key] = value
    return result
