"""One-request JSON subprocess protocol. It never writes repository files or executes commands."""

import json
import sys

from thread_agent.domain.records import AgentError, canonical
from thread_agent.editor.engine import run
from thread_agent.editor.proposals import validate
from thread_agent.providers.ollama.client import Ollama


def main() -> None:
    try:
        line = sys.stdin.buffer.readline(2 * 1024 * 1024 + 1)
        if len(line) > 2 * 1024 * 1024:
            raise AgentError("Editor request exceeded 2 MiB.")
        request = json.loads(line)
        if not isinstance(request, dict):
            raise AgentError("Expected a JSON request object.")
        operation = request.get("operation")
        if operation == "python":
            if sys.version_info < (3, 11):  # noqa: UP036 - probe may use an older interpreter
                raise AgentError("Thread requires Python 3.11 or later.")
            result = {"executable": sys.executable, "version": sys.version.split()[0]}
        elif operation == "models":
            result = {
                "models": [
                    item["name"]
                    for item in Ollama("").inventory()
                    if isinstance(item.get("name"), str)
                    and "cloud" not in item["name"].lower()
                    and not item.get("remote_host")
                    and not item.get("remote_model")
                ]
            }
        elif operation == "validate":
            result = validate(request["root"], request["proposal"])
        elif operation == "run":
            result = run(request)
        else:
            raise AgentError("Unknown editor operation.")
        print(canonical({"ok": True, "result": result}), flush=True)
    except (AgentError, ValueError, KeyError, TypeError, OSError, RecursionError) as exc:
        print(canonical({"ok": False, "error": str(exc)}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
