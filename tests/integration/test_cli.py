"""Subprocess checks of the installed CLI against isolated source and state."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_lookup_pending_resume_and_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings.toml").write_text('[database]\ndefault = "sqlite"\n')
            env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")}

            def cli(*args):
                return subprocess.run(
                    [sys.executable, "-m", "thread_agent", *args],
                    cwd=root,
                    env=env,
                    text=True,
                    input="",
                    capture_output=True,
                    timeout=10,
                )

            self.assertEqual(0, cli("--help").returncode)
            self.assertEqual(0, cli("status").returncode)
            self.assertFalse((root / ".thread-agent").exists())
            pending = cli("ask", "--file", "settings.toml", "--no-input")
            self.assertEqual(2, pending.returncode, pending.stderr)
            session_id = pending.stdout.split("Session: ")[1].split()[0]
            decision_id = pending.stdout.split("Decision: ")[1].split()[0]
            self.assertEqual(2, cli("resume", session_id, "--reply", "1").returncode)
            complete = cli("resume", session_id, "--reply", "1", "--decision", decision_id)
            self.assertEqual(0, complete.returncode, complete.stdout + complete.stderr)
            self.assertIn('"value": "sqlite"', complete.stdout)
            self.assertEqual(0, cli("replay", session_id).returncode)
            self.assertEqual(
                1, cli("resume", session_id, "--reply", "1", "--decision", decision_id).returncode
            )
            trace = cli("trace", session_id)
            self.assertEqual("delivery", json.loads(trace.stdout)[-1]["type"])
            self.assertEqual(
                '[database]\ndefault = "sqlite"\n', (root / "settings.toml").read_text()
            )
