"""Installed-origin boundaries without new binaries, SDK acquisition or terms acceptance."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = (
    Path(__file__).resolve().parents[2] / "extensions/vscode/scripts/distribution_provenance.py"
)
SPEC = importlib.util.spec_from_file_location("distribution_provenance_tests", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DistributionProvenanceTests(unittest.TestCase):
    def test_binary_and_oversized_text_never_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "LICENSE.txt"
            for content in [b"MZimage", b"bad\0text", b"\xff", b"x" * (MODULE.MAX_TEXT + 1)]:
                source.write_bytes(content)
                self.assertIsNone(MODULE.retain_text(source, root, {}, "fixture"))
            source.write_bytes(b"original copyright and terms")
            texts = {}
            row = MODULE.retain_text(source, root, texts, "fixture")
            self.assertEqual((root / row["file"]).read_bytes(), source.read_bytes())
            MODULE.retain_text(source, root, texts, "fixture")
            self.assertEqual(len(texts), 1)

    def test_only_exact_installed_sdk_redist_hash_is_origin_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "api-ms-fixture.dll"
            source.write_bytes(b"synthetic image, never executed")
            sdk = root / "Windows Kits/10/Redist/fixture/ucrt/DLLs/arm64"
            sdk.mkdir(parents=True)
            candidate = sdk / source.name
            candidate.write_bytes(b"different")
            with patch.dict(os.environ, {"ProgramFiles(x86)": str(root)}):
                result = MODULE.windows_sdk_evidence(source, "win32-arm64", root, {})
                self.assertEqual(result["exact_sdk_matches"], [])
                self.assertFalse(result["new_sdk_acquired"])
                self.assertFalse(result["new_terms_accepted"])
                candidate.write_bytes(source.read_bytes())
                result = MODULE.windows_sdk_evidence(source, "win32-arm64", root, {})
                self.assertEqual(len(result["exact_sdk_matches"]), 1)
                self.assertFalse(result["terms_reviewed"])
                self.assertEqual(
                    MODULE.windows_sdk_evidence(source, "win32-x64", root, {})["exact_sdk_matches"],
                    [],
                )

    def test_unknown_linux_owner_remains_unresolved(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(MODULE, "command", return_value=""),
        ):
            result = MODULE.linux_evidence(Path("/usr/lib/fixture.so"), Path(directory), {})
            self.assertEqual(result["packages"], [])
            self.assertEqual(result["origin"], "unresolved installed origin")
            self.assertFalse(result["terms_reviewed"])

    def test_notice_link_cannot_escape_declared_source_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            allowed = root / "allowed"
            allowed.mkdir()
            outside = root / "outside"
            outside.write_bytes(b"unrelated text")
            candidate = allowed / "LICENSE.txt"
            candidate.symlink_to(outside)
            self.assertIsNone(MODULE.retain_text(candidate, allowed, {}, "fixture", allowed))
