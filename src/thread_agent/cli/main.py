"""Terminal interface for the experimental local source-field workflow."""

import argparse
import json
import shlex
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path

from thread_agent import __version__
from thread_agent.domain.records import AgentError, canonical
from thread_agent.providers.ollama.client import Ollama
from thread_agent.runtime.lookup import replay, respond, start
from thread_agent.storage.sqlite.store import Store


def display(text: str) -> None:
    """Do not let source paths, questions, or exceptions inject terminal controls."""
    print("".join(c if c.isprintable() or c == "\n" else f"\\u{ord(c):04x}" for c in text))


def resume_command(session: dict, directory: Path) -> str:
    return f"thread-agent --state-dir {shlex.quote(str(directory))} resume {session['id']}"


def show(session: dict, more: bool = False, directory: Path = Path(".thread-agent")) -> None:
    display(f"Session: {session['id']} | {session['status']}")
    if session.get("echo"):
        display(session["echo"])
    if session["status"] == "completed":
        display(session["answer"])
    elif session["status"] == "pending":
        display(f"Decision: {session['decision_id']}")
        display(f"Source: {canonical(session['evidence']['path'])}")
        display(f"Snapshot: {session['evidence']['sha256']}")
        if session["question"]:
            display(f"Question: {canonical(session['question'])}")
        display("Choose an exact field to report. This reports file contents, not running state.")
        if session.get("notice"):
            display(session["notice"])
        for i, option in enumerate(session["options"], 1):
            if i > 3 and not more:
                break
            note = ""
            if option == session["recommendation"]:
                note = f" — Recommended: {session['recommendation_reason']}"
            display(f"{i}. {canonical(option)}{note}")
        display("more — Show all fields | field /exact/pointer — Custom field | pause | cancel")
        display("No default is submitted. Other free text stays pending for clarification.")
        display(f"Resume later: {resume_command(session, directory)}")


def interact(store: Store, session: dict, no_input: bool) -> int:
    more = False
    while True:
        show(session, more, store.directory)
        if session["status"] != "pending":
            return 0
        if no_input or not sys.stdin.isatty():
            return 2
        try:
            raw = input("Your choice: ")
        except (EOFError, KeyboardInterrupt):
            raw = "pause"
        session = respond(store, session["id"], session["decision_id"], raw)
        more = raw.strip().lower() == "more"
        if raw.strip().lower() == "pause":
            display(f"Paused. Resume with: {resume_command(session, store.directory)}")
            return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="thread-agent",
        description="Experimental local TOML/JSON field reports with evidence and human choices.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path(".thread-agent"),
        help="Local session database directory (default: .thread-agent)",
    )
    commands = parser.add_subparsers(dest="command")
    status = commands.add_parser("status", help="Show implementation status, not model health")
    status.add_argument("--json", action="store_true")
    commands.add_parser("doctor", help="List installed models from local Ollama; no generation")
    ask = commands.add_parser(
        "ask", help="Report a scalar field from an explicitly selected TOML/JSON file"
    )
    ask.add_argument(
        "question", nargs="?", default="", help="Optional question to guide field selection"
    )
    ask.add_argument("--workspace", default=".", help="Root allowed for source reads")
    ask.add_argument("--file", required=True, help="Source path relative to workspace")
    ask.add_argument("--field", help="Exact JSON pointer, e.g. /database/default; no model needed")
    ask.add_argument(
        "--model", help="Exact installed Ollama model name; suggests a field for confirmation"
    )
    ask.add_argument(
        "--no-input", action="store_true", help="Save any pending decision without prompting"
    )
    resume = commands.add_parser("resume", help="Show or answer a saved field-selection decision")
    resume.add_argument("session_id")
    resume.add_argument("--reply", help="Explicit number, field pointer, more, pause, or cancel")
    resume.add_argument(
        "--decision", help="Decision ID displayed with the menu; required with --reply"
    )
    resume.add_argument("--no-input", action="store_true")
    commands.add_parser("sessions", help="List locally saved session IDs and states")
    trace = commands.add_parser(
        "trace", help="Show a session's local records; includes captured source"
    )
    trace.add_argument("session_id")
    replay_cmd = commands.add_parser(
        "replay", help="Recheck stored field report without tools or models"
    )
    replay_cmd.add_argument("session_id")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "resume" and ((args.reply is None) != (args.decision is None)):
        parser.error("--reply and --decision must be provided together")
    store = None
    try:
        if args.command == "status":
            report = {
                "project": "thread-agent",
                "version": __version__,
                "stage": "experimental-field-cli-and-vscode",
                "implemented": [
                    "toml_json_field_reports",
                    "local_ollama_field_suggestions",
                    "persistent_field_clarifications",
                    "source_report_replay",
                    "vscode_repository_analysis",
                    "vscode_reviewed_edits",
                    "vscode_document_summaries",
                ],
                "not_implemented": [
                    "general_chat",
                    "semantic_verification",
                    "durable_memory",
                    "hosted_private_adapters",
                ],
                "configuration_loading_implemented": False,
                "m1_acceptance_complete": False,
                "next_step": "Try: thread-agent ask --file examples/projects/minimal/settings.toml --field /database/default",
            }
            display(
                json.dumps(report, indent=2)
                if args.json
                else (
                    f"Thread Agent {__version__}: experimental local field lookup.\n"
                    "Available: exact TOML/JSON fields, local model suggestions, saved choices, and replay.\n"
                    "VS Code extension: repository analysis, reviewed edits, and document summaries.\n"
                    "Not yet available: semantic verification, durable memory, or hosted models.\n"
                    "Full M1 acceptance and model accuracy are not established.\n"
                    + report["next_step"]
                )
            )
            return 0
        if args.command == "doctor":
            models = Ollama("").inventory()
            display("Local Ollama is reachable. Installed models (not certified by this project):")
            for model in models:
                display(f"- {canonical(model.get('name'))}")
            if not models:
                display("No models installed. Explicit --field lookups still work without a model.")
            return 0
        store = Store(args.state_dir)
        if args.command == "ask":
            session = start(store, args.workspace, args.file, args.question, args.field, args.model)
            return interact(store, session, args.no_input)
        if args.command == "resume":
            if args.reply is not None:
                session = respond(store, args.session_id, args.decision, args.reply)
                show(session, args.reply.strip().lower() == "more", store.directory)
                return 2 if session["status"] == "pending" else 0
            return interact(store, store.get(args.session_id), args.no_input)
        if args.command == "sessions":
            for session in store.sessions():
                display(
                    f"{session['id']} {session['status']} {canonical(session['evidence']['path'])}"
                )
            return 0
        if args.command == "trace":
            display(json.dumps(store.trace(args.session_id), ensure_ascii=True, indent=2))
            return 0
        if args.command == "replay":
            display(replay(store, args.session_id))
            display("Stored source report verified. No live source or model was accessed.")
            return 0
    except (AgentError, OSError, sqlite3.Error) as exc:
        display(f"Error: {exc}")
        return 1
    finally:
        if store is not None:
            store.close()
    return 0
