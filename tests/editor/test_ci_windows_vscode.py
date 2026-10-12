"""Pinned test acquisition rejects altered bytes and unsafe extraction."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "ci_windows_vscode_tests", ROOT / "extensions/vscode/scripts/ci_windows_vscode.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WindowsVSCodeAcquisitionTests(unittest.TestCase):
    def test_pinned_side_by_side_runtime_layout_is_preserved(self):
        import io

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "wrapped.zip"
            prefix = "a" * 10
            with zipfile.ZipFile(archive, "w") as source:
                source.writestr("Code.exe", b"fixture never executed")
                source.writestr(prefix + "/icudtl.dat", b"fixture ICU data")
                source.writestr(
                    prefix + "/resources/app/package.json", json.dumps({"version": "fixture"})
                )
                source.writestr(
                    prefix + "/resources/app/product.json", json.dumps({"commit": "a" * 40})
                )
            pin = {
                "platform": "win32-x64-archive",
                "commit": "a" * 40,
                "version": "fixture",
                "runtime_directory": prefix,
                "url": "https://vscode.download.prss.microsoft.com/" + "a" * 40 + "/code.zip",
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            }
            with patch.object(
                MODULE.urllib.request, "urlopen", return_value=io.BytesIO(archive.read_bytes())
            ):
                result = MODULE.download(root / "code", pin)
            self.assertEqual(result, root / "code/Code.exe")
            self.assertEqual(
                (root / "code" / prefix / "icudtl.dat").read_bytes(), b"fixture ICU data"
            )

    def test_traversal_duplicate_and_existing_output_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "unsafe.zip"
            for name in ["../escape", "C:/escape", "dir\\escape"]:
                with zipfile.ZipFile(archive, "w") as source:
                    source.writestr(name, b"unsafe")
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    MODULE.verified_extract(archive, root / "output")
                self.assertFalse((root / "output").exists())
            with zipfile.ZipFile(archive, "w") as source:
                source.writestr("Code.exe", b"a")
                source.writestr("CODE.EXE", b"b")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                MODULE.verified_extract(archive, root / "output")
            (root / "output").mkdir()
            with self.assertRaisesRegex(ValueError, "fresh directory"):
                MODULE.verified_extract(archive, root / "output")

    def test_changed_download_is_rejected_before_extraction(self):
        import io

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "code"
            pin = {
                "platform": "win32-x64-archive",
                "commit": "a" * 40,
                "url": "https://vscode.download.prss.microsoft.com/" + "a" * 40 + "/code.zip",
                "sha256": hashlib.sha256(b"approved").hexdigest(),
            }
            with patch.object(
                MODULE.urllib.request, "urlopen", return_value=io.BytesIO(b"changed")
            ):
                with self.assertRaisesRegex(ValueError, "digest mismatch"):
                    MODULE.download(output, pin)
            self.assertFalse(output.exists())

    def test_pinned_verified_archive_extracts_and_metadata_must_match(self):
        import io

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "code.zip"
            with zipfile.ZipFile(archive, "w") as source:
                source.writestr("Code.exe", b"fixture never executed")
                source.writestr("resources/app/package.json", json.dumps({"version": "fixture"}))
                source.writestr("resources/app/product.json", json.dumps({"commit": "a" * 40}))
            pin = {
                "platform": "win32-x64-archive",
                "commit": "a" * 40,
                "version": "fixture",
                "url": "https://vscode.download.prss.microsoft.com/" + "a" * 40 + "/code.zip",
                "sha256": MODULE.hashlib.sha256(archive.read_bytes()).hexdigest(),
            }
            with patch.object(
                MODULE.urllib.request, "urlopen", return_value=io.BytesIO(archive.read_bytes())
            ):
                result = MODULE.download(root / "code", pin)
            self.assertEqual(result.read_bytes(), b"fixture never executed")
            pin["version"] = "wrong"
            with patch.object(
                MODULE.urllib.request, "urlopen", return_value=io.BytesIO(archive.read_bytes())
            ):
                with self.assertRaisesRegex(ValueError, "version/commit mismatch"):
                    MODULE.download(root / "wrong", pin)

    def test_ci_package_requires_native_payload_without_running_tools(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(MODULE.subprocess, "run") as command,
        ):
            with self.assertRaisesRegex(ValueError, "Build the Windows x64 backend"):
                MODULE.package(Path(directory), Path(directory) / "ci.vsix")
            command.assert_not_called()
