"""Expose package information without implying that an agent can run yet."""

import argparse
import json
from collections.abc import Sequence

from thread_agent import __version__


def main(argv: Sequence[str] | None = None) -> int:
    """Print help, version, or scaffold status without network or data writes."""
    parser = argparse.ArgumentParser(
        prog="thread-agent",
        description="Project scaffold. Agent execution and model adapters are not implemented yet.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")
    status = commands.add_parser("status", help="Show implementation status, not model health")
    status.add_argument("--json", action="store_true", help="Print machine-readable status")
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "status":
        report = {
            "project": "thread-agent",
            "version": __version__,
            "stage": "scaffold",
            "agent_runtime_implemented": False,
            "model_adapters_implemented": [],
            "configuration_loading_implemented": False,
            "next_step": "Define M0 acceptance fixtures and implement the local M1 workflow.",
        }
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Thread Agent {__version__}: scaffold only.")
            print("Available: package installation, --help, --version, and status.")
            print("Not yet available: agent runs, provider connections, memory, or approvals.")
            print(report["next_step"])
        return 0

    parser.error("Unknown command")
    return 2
