"""Exact-library attribution and changed-notice rejection, not legal certification."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "notice_tests", ROOT / "extensions/vscode/scripts/native_notices.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class NativeNoticeTests(unittest.TestCase):
    def fixture(self, root):
        source = root / "library"
        source.write_bytes(b"exact binary fixture")
        output = root / "output"
        output.mkdir()
        profiles = root / "profiles"
        folder = profiles / "matched"
        folder.mkdir(parents=True)
        notice = folder / "LICENSE.txt"
        notice.write_bytes(b"synthetic retained terms")
        record = {
            "schema": 1,
            "target": "fixture-target",
            "python": "fixture-version",
            "source_library_sha256": MODULE.digest(source),
            "source_archive_sha256": "a" * 64,
            "distribution_source_commit": "b" * 40,
            "components": [
                {
                    "component": "fixture",
                    "version": "1",
                    "file": notice.name,
                    "sha256": MODULE.digest(notice),
                    "source": "https://example.test/notice",
                }
            ],
        }
        (folder / "profile.json").write_text(json.dumps(record))
        return source, output, profiles, notice

    def test_exact_source_retains_bytes_but_does_not_certify_distribution(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output, profiles, notice = self.fixture(Path(directory))
            result = MODULE.collect_static_notices(
                source, output, profiles, "fixture-target", "fixture-version"
            )
            self.assertEqual((output / "static-LICENSE.txt").read_bytes(), notice.read_bytes())
            self.assertFalse(result["complete_distribution_review"])

    def test_wrong_source_target_or_version_never_receives_attribution(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output, profiles, _ = self.fixture(Path(directory))
            for target, version in [("other", "fixture-version"), ("fixture-target", "other")]:
                self.assertIsNone(
                    MODULE.collect_static_notices(source, output, profiles, target, version)
                )
            source.write_bytes(b"different binary")
            self.assertIsNone(
                MODULE.collect_static_notices(
                    source, output, profiles, "fixture-target", "fixture-version"
                )
            )
            self.assertEqual(list(output.iterdir()), [])

    def test_notice_tampering_and_path_escape_stop_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output, profiles, notice = self.fixture(Path(directory))
            notice.write_bytes(b"changed terms")
            with self.assertRaisesRegex(ValueError, "missing or changed"):
                MODULE.collect_static_notices(
                    source, output, profiles, "fixture-target", "fixture-version"
                )
            path = profiles / "matched/profile.json"
            record = json.loads(path.read_text())
            record["components"][0]["file"] = "../LICENSE.txt"
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "basenames"):
                MODULE.collect_static_notices(
                    source, output, profiles, "fixture-target", "fixture-version"
                )

    def test_repository_snapshot_notice_hashes_and_openssl_version(self):
        folder = ROOT / "extensions/vscode/notices/portable-darwin-arm64-20261009"
        profile = json.loads((folder / "profile.json").read_text())
        self.assertFalse(profile["complete_distribution_review"])
        for item in profile["components"]:
            self.assertEqual(
                hashlib.sha256((folder / item["file"]).read_bytes()).hexdigest(), item["sha256"]
            )
        openssl = next(x for x in profile["components"] if x["component"] == "OpenSSL")
        self.assertEqual(openssl["version"], "3.5.9")
        self.assertIn(b"Apache License", (folder / openssl["file"]).read_bytes())

    def test_executable_named_license_is_not_notice_text(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name, content in [
                ("LicenseManager.dll", b"MZimage"),
                ("LicenseManager.exe", b"MZimage"),
                ("LICENSE", b"MZimage"),
                ("COPYING.txt", b"bad\0text"),
            ]:
                path = folder / name
                path.write_bytes(content)
                self.assertFalse(MODULE.notice_text_candidate(path))
            text = folder / "LICENSE.txt"
            text.write_text("retained copyright and terms", encoding="utf-8")
            self.assertTrue(MODULE.notice_text_candidate(text))

    def test_core_binding_requires_exact_source_target_version_and_notice(self):
        folder = ROOT / "extensions/vscode/notices/cpython-core-ci"
        bindings = json.loads((folder / "bindings.json").read_text())["bindings"]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for binding in bindings:
                entry = {
                    "source_name": binding["source_name"],
                    "source_sha256": binding["source_sha256"],
                    "payload_sha256": "a" * 64,
                    "destination": "_internal/fixture",
                }
                result = MODULE.collect_cpython_core_notices(
                    {"entries": [entry]}, output, folder, binding["target"], binding["python"]
                )
                self.assertEqual(len(result), 1)
                self.assertFalse(result[0]["complete_distribution_review"])
                self.assertEqual(result[0]["payload_sha256"], "a" * 64)
                for target, version, source_hash in [
                    ("unknown", binding["python"], binding["source_sha256"]),
                    (binding["target"], "unknown", binding["source_sha256"]),
                    (binding["target"], binding["python"], "f" * 64),
                ]:
                    changed = {**entry, "source_sha256": source_hash}
                    self.assertEqual(
                        MODULE.collect_cpython_core_notices(
                            {"entries": [changed]}, output, folder, target, version
                        ),
                        [],
                    )
            copied = output / "CPython-core-LICENSE.txt"
            self.assertEqual(copied.read_bytes(), (folder / "LICENSE.txt").read_bytes())
            altered = output / "altered"
            altered.mkdir()
            (altered / "bindings.json").write_text((folder / "bindings.json").read_text())
            (altered / "LICENSE.txt").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "missing or changed"):
                MODULE.collect_cpython_core_notices(
                    {"entries": [entry]}, output, altered, binding["target"], binding["python"]
                )
