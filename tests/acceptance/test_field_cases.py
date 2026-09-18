"""Development fixtures for exact source reports; not a model quality benchmark."""

import json
import tempfile
import unittest
from pathlib import Path

from thread_agent.domain.records import canonical
from thread_agent.runtime.lookup import replay, start
from thread_agent.storage.sqlite.store import Store

CASES = Path(__file__).resolve().parents[2] / "evals/cases/development/field_lookup.json"


class FieldCases(unittest.TestCase):
    def test_development_reference_outcomes(self):
        for case in json.loads(CASES.read_text()):
            with self.subTest(case=case["id"]), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                workspace = root / "workspace"
                workspace.mkdir()
                # Only the source fixture enters the allowed workspace, never its reference answer.
                (workspace / case["file"]).write_text(case["source"], encoding="utf-8")
                store = Store(root / "state")
                try:
                    session = start(store, str(workspace), case["file"], field=case["field"])
                    actual = json.loads(session["answer"])
                    self.assertEqual(canonical(case["expected"]), canonical(actual["value"]))
                    self.assertEqual(case["field"], actual["field"])
                    self.assertEqual(case["file"], actual["source"])
                    self.assertEqual(session["answer"], replay(store, session["id"]))
                finally:
                    store.close()
