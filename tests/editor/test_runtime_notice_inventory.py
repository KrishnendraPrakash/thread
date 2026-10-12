import hashlib
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = (
    Path(__file__).resolve().parents[2] / "extensions/vscode/scripts/runtime_notice_inventory.py"
)
SPEC = importlib.util.spec_from_file_location("runtime_notice_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RuntimeNoticeInventoryTests(unittest.TestCase):
    def test_identity_notice_and_no_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "lib").mkdir()
            (root / "lib/backend.exe").write_bytes(b"not executed")
            (root / "LICENSE.txt").write_bytes(b"synthetic terms")
            report = MODULE.inventory(root)
            self.assertFalse(report["complete_legal_review"])
            self.assertEqual(report["file_count"], 2)
            notice, binary = report["files"]
            self.assertEqual(notice["sha256"], hashlib.sha256(b"synthetic terms").hexdigest())
            self.assertTrue(notice["notice_name_candidate"])
            self.assertFalse(binary["notice_name_candidate"])
            self.assertNotIn(temporary, str(report))
            self.assertEqual((root / "lib/backend.exe").read_bytes(), b"not executed")

    def test_links_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "original"
            original.write_bytes(b"x")
            os.link(original, root / "hardlink")
            with self.assertRaisesRegex(ValueError, "hard links"):
                MODULE.inventory(root)

    @unittest.skipIf(os.name == "nt", "Windows symlink creation requires privileges")
    def test_directory_symlink_and_special_file_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "redirect").symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "links"):
                MODULE.inventory(root)
            (root / "redirect").unlink()
            os.mkfifo(root / "pipe")
            with self.assertRaisesRegex(ValueError, "special files"):
                MODULE.inventory(root)

    def test_limits_fail_before_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "large").write_bytes(b"abc")
            for name in ("MAX_FILE_BYTES", "MAX_TOTAL_BYTES", "MAX_FILES"):
                with self.subTest(limit=name), patch.object(MODULE, name, 0):
                    with self.assertRaisesRegex(ValueError, "limit"):
                        MODULE.inventory(root)


if __name__ == "__main__":
    unittest.main()
