"""Native Windows safety tests; portable path-policy tests run everywhere."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from thread_agent.domain.records import AgentError
from thread_agent.tools.filesystem.windows import components, entries, read_bytes


class WindowsPathTests(unittest.TestCase):
    def test_rejects_device_stream_traversal_and_ambiguous_names(self):
        for name in (
            "../a.txt",
            "a.txt:stream",
            "CON.txt",
            "COM¹.txt",
            "CLOCK$.txt",
            "dir/NUL",
            "a./b",
            "a /b",
            "a\\b",
            "/absolute",
            "a//b",
        ):
            with self.subTest(name=name), self.assertRaises(AgentError):
                components(name)
        self.assertEqual(components("nested/source.py"), ["nested", "source.py"])


@unittest.skipUnless(os.name == "nt", "Requires native Windows handles")
class WindowsHandleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "nested").mkdir()
        (self.root / "nested/source.txt").write_bytes(b"hello")

    def test_regular_read_enumeration_and_limits(self):
        self.assertEqual(read_bytes(self.root, "nested/source.txt", 10), b"hello")
        self.assertIn(("nested", True, False), entries(self.root, self.root))
        self.assertIn(("source.txt", False, False), entries(self.root, self.root / "nested"))
        with self.assertRaises(AgentError):
            read_bytes(self.root, "nested/source.txt", 3)

    def test_hardlink_and_junction_rejected(self):
        os.link(self.root / "nested/source.txt", self.root / "linked.txt")
        with self.assertRaises(AgentError):
            read_bytes(self.root, "linked.txt", 10)
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "source.txt").write_bytes(b"outside")
        junction = self.root / "junction"
        subprocess.run(
            ["cmd", "/d", "/c", "mklink", "/J", str(junction), str(outside)],
            check=True,
            capture_output=True,
        )
        try:
            self.assertIn(("junction", True, True), entries(self.root, self.root))
            with self.assertRaises(AgentError):
                read_bytes(self.root, "junction/source.txt", 20)
        finally:
            junction.rmdir()
