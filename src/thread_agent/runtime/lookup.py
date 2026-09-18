"""Experimental T1 field lookup with explicit scope and persisted clarification."""

import json
from pathlib import Path
from uuid import uuid4

from thread_agent.domain.records import AgentError, canonical, digest
from thread_agent.evidence.structured import fields
from thread_agent.providers.ollama.client import Ollama
from thread_agent.storage.sqlite.store import Store
from thread_agent.tools.filesystem.read import read_source

SCOPE = "Captured file contents only; running configuration was not checked."


def result_events(evidence: dict, pointer: str) -> tuple[str, list[dict]]:
    if digest(evidence["text"].encode()) != evidence["sha256"]:
        raise AgentError("Stored source hash mismatch; cannot verify this session.")
    values = fields(evidence["text"], evidence["path"])
    if pointer not in values:
        raise AgentError("Selected field is absent from the captured source.")
    answer = {
        "source": evidence["path"],
        "field": pointer,
        "value": values[pointer],
        "source_sha256": evidence["sha256"],
        "scope": SCOPE,
    }
    claim = {
        "id": "claim:field",
        "predicate": "source_field_equals",
        "field": pointer,
        "value": values[pointer],
        "evidence_sha256": evidence["sha256"],
        "scope": SCOPE,
    }
    rendered = json.dumps(answer, ensure_ascii=True, indent=2, allow_nan=False)
    # Inspect the actual bytes after rendering against independently parsed source bindings.
    decoded = json.loads(rendered)
    independently_parsed = fields(evidence["text"], evidence["path"])[pointer]
    if (
        set(decoded) != {"source", "field", "value", "source_sha256", "scope"}
        or canonical(decoded["value"]) != canonical(independently_parsed)
        or decoded["source"] != evidence["path"]
        or decoded["source_sha256"] != digest(evidence["text"].encode())
        or decoded["field"] != pointer
        or decoded["scope"] != SCOPE
    ):
        raise AgentError("Rendered source report failed fidelity validation.")
    output_hash = digest(rendered.encode())
    return rendered, [
        {"type": "claim", "claim": claim},
        {
            "type": "check",
            "id": "check:field",
            "claim_id": claim["id"],
            "method": "parse-snapshot-field-v1",
            "result": "supported",
            "evidence_sha256": evidence["sha256"],
        },
        {
            "type": "claim_status",
            "claim_id": claim["id"],
            "from": "unchecked",
            "to": "supported",
            "check_ids": ["check:field"],
        },
        {"type": "coverage", "required_field": pointer, "result": "pass"},
        {"type": "render", "text": rendered, "sha256": output_hash},
        {
            "type": "fidelity",
            "method": "json-slots-from-parsed-source-v1",
            "render_sha256": output_hash,
            "result": "pass",
        },
        {"type": "delivery", "render_sha256": output_hash},
    ]


def finalize(store: Store, session: dict, pointer: str, events: list[dict]) -> dict:
    rendered, final_events = result_events(session["evidence"], pointer)
    session = {**session, "status": "completed", "field": pointer, "answer": rendered}
    return store.save(session, [*events, *final_events])


def start(
    store: Store,
    workspace: str,
    file: str,
    question: str = "",
    field: str | None = None,
    model: str | None = None,
) -> dict:
    if len(question.encode()) > 1024:
        raise AgentError("Question exceeds the 1024-byte limit.")
    if field is not None and (question or model):
        raise AgentError("Use either an explicit --field or a question with optional --model.")
    if model and not question:
        raise AgentError("Provide a question when selecting --model.")
    evidence = read_source(workspace, file)
    values = fields(evidence.text, evidence.path)
    if field is not None and field not in values:
        raise AgentError("Field is absent. Omit --field to choose an available field.")
    pointers = sorted(values)
    session = store.create(
        {
            "schema_version": "field-lookup-v1",
            "status": "pending",
            "workspace": str(Path(workspace).resolve()),
            "question": question,
            "evidence": evidence.record(),
            "options": pointers,
            "recommendation": pointers[0],
            "recommendation_reason": "First available field; confirm relevance.",
            "decision_id": uuid4().hex,
            "field": field,
        },
        [
            {
                "type": "contract",
                "tier": "T1",
                "scope": SCOPE,
                "required_field": field,
                "question": question,
                "model": model,
            },
            {
                "type": "policy",
                "result": "allow",
                "rule": "explicit-file-read-v1",
                "source": evidence.path,
                "effects": "read-source-and-write-local-session-only",
            },
            {"type": "evidence", "evidence": evidence.record()},
        ],
    )
    if field is not None:
        return finalize(store, session, field, [])
    if model:

        def record(event: dict) -> None:
            nonlocal session
            session = store.save(session, [event])

        try:
            selected = Ollama(model).suggest(question, pointers, record)
            if selected is not None:
                session["recommendation"] = selected
                session["recommendation_reason"] = (
                    "Local model suggested this field; confirm that source-field scope fits your request."
                )
                session["options"] = [selected, *(p for p in pointers if p != selected)]
            else:
                session["notice"] = (
                    "Model found no single suitable field. Choose a source-only scope or cancel."
                )
        except (AgentError, KeyboardInterrupt) as exc:
            session["notice"] = str(exc) or "Model call interrupted; field choice remains pending."
            session = store.save(
                session, [{"type": "provider_unavailable", "message": session["notice"]}]
            )
    return store.save(
        session,
        [
            {
                "type": "decision",
                "decision_id": session["decision_id"],
                "reason": "Select the exact source-field scope; this is not permission for file edits.",
                "options": session["options"],
                "source_sha256": evidence.sha256,
                "recommendation": session["recommendation"],
                "status": "pending",
            }
        ],
    )


def respond(store: Store, session_id: str, decision_id: str, raw: str) -> dict:
    session = store.get(session_id)
    if session["status"] != "pending":
        raise AgentError("Decision is no longer pending; duplicate replies cannot rerun it.")
    if decision_id != session["decision_id"]:
        raise AgentError("Stale decision ID. Display the current session before replying.")
    if len(raw.encode()) > 2048:
        raise AgentError("Reply exceeds 2048 bytes; decision remains pending.")
    reply = raw.strip()
    event = {"type": "human_reply", "producer": "human", "raw": raw, "decision_id": decision_id}
    if reply.lower() == "cancel":
        return store.save({**session, "status": "cancelled"}, [event, {"type": "cancelled"}])
    if reply.lower() in {"pause", "more"} or not reply:
        return store.save(session, [event, {"type": "pending", "reason": reply or "empty reply"}])
    if reply.isascii() and reply.isdigit() and len(reply) < 4:
        index = int(reply) - 1
        pointer = session["options"][index] if 0 <= index < len(session["options"]) else None
    elif reply.startswith("field "):
        pointer = reply.removeprefix("field ")
    else:
        pointer = None
    if pointer not in session["options"]:
        session["notice"] = (
            "Reply is ambiguous or invalid. Choose a number or write: field /exact/pointer"
        )
        return store.save(session, [event, {"type": "interpretation", "result": "ambiguous"}])
    current = read_source(session["workspace"], session["evidence"]["path"])
    if current.sha256 != session["evidence"]["sha256"]:
        options = sorted(fields(current.text, current.path))
        session.update(
            {
                "evidence": current.record(),
                "options": options,
                "recommendation": options[0],
                "recommendation_reason": "Source changed; choose a field from the refreshed snapshot.",
                "decision_id": uuid4().hex,
                "notice": "Source changed. Your old reply was not applied. Review the new decision.",
            }
        )
        return store.save(
            session,
            [
                event,
                {"type": "stale_source", "result": "reply_rejected"},
                {"type": "evidence", "evidence": current.record()},
                {
                    "type": "decision",
                    "decision_id": session["decision_id"],
                    "source_sha256": current.sha256,
                    "options": options,
                },
            ],
        )
    echo = (
        f"Selected source-field scope: {canonical(pointer)} in {canonical(current.path)}. {SCOPE}"
    )
    session["echo"] = echo
    session.pop("notice", None)
    return finalize(
        store,
        session,
        pointer,
        [
            event,
            {
                "type": "interpretation",
                "result": "valid",
                "rule": "exact-field-choice-v1",
                "field": pointer,
                "echo": echo,
            },
            {
                "type": "contract_revision",
                "cause": "explicit_human_field_choice",
                "required_field": pointer,
                "scope": SCOPE,
            },
            {
                "type": "freshness",
                "method": "compare-fresh-read-to-saved-snapshot",
                "source_sha256": current.sha256,
                "result": "unchanged",
            },
        ],
    )


def replay(store: Store, session_id: str) -> str:
    """Recheck a completed field report using stored bytes, with no tool/model calls."""
    session = store.get(session_id)
    if session["status"] != "completed":
        raise AgentError("Only a completed field report can be replayed.")
    trace = store.trace(session_id)
    if any(event["seq"] != i for i, event in enumerate(trace, 1)):
        raise AgentError("Trace sequence mismatch; replay stopped.")
    rendered, expected = result_events(session["evidence"], session["field"])
    tail = trace[-len(expected) :]
    if (
        len(tail) != len(expected)
        or any(
            canonical({key: event.get(key) for key in reference}) != canonical(reference)
            for event, reference in zip(tail, expected, strict=True)
        )
        or session.get("answer") != rendered
    ):
        raise AgentError("Replay mismatch: recorded claims, checks, or delivered answer changed.")
    return rendered
