"""Isolated entry point: never import modules from the user's repository."""

import sys
from pathlib import Path

if sys.version_info < (3, 11):  # noqa: UP036 - executable may be an older Python
    sys.exit("Thread requires Python 3.11 or later.")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thread_agent.editor.service import main  # noqa: E402

main()
