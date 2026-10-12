"""Native source/payload attribution boundaries using tiny nonexecuted files."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "extensions/vscode/scripts/native_inventory.py"
SPEC = importlib.util.spec_from_file_location("native_inventory_tests", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class NativeInventoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source.so"
        self.source.write_bytes(b"source")
        self.payload = self.root / "payload"
        (self.payload / "_internal/pkg").mkdir(parents=True)
        (self.payload / "_internal/pkg/extension.so").write_bytes(b"rewritten")

    def test_native_extensions_are_included_and_rewritten_payload_is_distinct(self):
        toc = [
            [
                ("pkg/extension.so", str(self.source), "EXTENSION"),
                ("ignore.txt", "not opened", "DATA"),
            ]
        ]
        result = MODULE.collected_binaries(toc, self.payload)
        self.assertEqual(len(result["entries"]), 1)
        row = result["entries"][0]
        self.assertEqual(row["kind"], "EXTENSION")
        self.assertFalse(row["source_bytes_identical"])
        self.assertNotIn(str(self.root), str(result))
        self.assertFalse(result["complete_distribution_review"])

    def test_unsafe_destinations_are_rejected_before_source_access(self):
        for name in ("../escape", "/absolute", "C:\\escape", "pkg//file", "pkg/./file"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Unsafe"):
                MODULE.collected_binaries([[(name, "missing", "BINARY")]], self.payload)

    def test_missing_conflicting_and_ambiguous_payloads_fail(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            MODULE.collected_binaries([[("missing", str(self.source), "BINARY")]], self.payload)
        toc = [
            [
                ("pkg/extension.so", str(self.source), "BINARY"),
                ("pkg/extension.so", str(self.source), "EXTENSION"),
            ]
        ]
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            MODULE.collected_binaries(toc, self.payload)
        (self.payload / "pkg").mkdir()
        (self.payload / "pkg/extension.so").write_bytes(b"duplicate")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            MODULE.collected_binaries([toc[0][:1]], self.payload)

    def test_parent_link_cannot_redirect_inventory_outside_payload(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "binary.so").write_bytes(b"outside")
        (self.payload / "redirect").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "escaped"):
            MODULE.collected_binaries(
                [[("redirect/binary.so", str(self.source), "BINARY")]], self.payload
            )
