"""Native candidate aggregation and irreversible upload recovery boundaries."""

import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tests.editor import test_marketplace_preflight as fixtures

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "extensions/vscode/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


BUILDER = load("native_candidates")
UPLOAD = load("marketplace_upload")


class MarketplaceAutomationTests(unittest.TestCase):
    def fixture(self, root):
        return fixtures.MarketplacePreflightTests().release_fixture(root)

    def test_inactive_workflows_use_only_verified_immutable_action_pins(self):
        pins = json.loads((ROOT / "release/action-pins.json").read_text())["actions"]
        for name in ("native-release-candidates", "marketplace-publish"):
            source = (ROOT / "release" / f"{name}.yml.disabled").read_text()
            uses = re.findall(r"^\s+uses: (\S+)|^\s+- uses: (\S+)", source, re.M)
            self.assertTrue(uses)
            for first, second in uses:
                action, revision = (first or second).split("@")
                self.assertRegex(revision, r"^[0-9a-f]{40}$")
                self.assertEqual(revision, pins[action]["commit"])
            self.assertNotIn("contents: write", source)
            self.assertIn("persist-credentials: false", source)
        builder = (ROOT / "release/native-release-candidates.yml.disabled").read_text()
        self.assertNotIn("id-token:", builder)
        self.assertNotIn("azure/login", builder)
        self.assertFalse((ROOT / ".github/workflows/native-release-candidates.yml").exists())
        self.assertFalse((ROOT / ".github/workflows/marketplace-publish.yml").exists())

    def test_builder_stops_before_commands_when_release_policy_is_pending(self):
        with patch.object(BUILDER.subprocess, "run") as command:
            with self.assertRaisesRegex(ValueError, "Release gates pending"):
                BUILDER.build(ROOT, "darwin-arm64", {}, {}, Path("unused"))
            command.assert_not_called()

    def test_builder_rejects_cross_host_and_wrong_companion_before_commands(self):
        with (
            patch.object(BUILDER, "readiness", return_value={}),
            patch.object(BUILDER, "host_target", return_value="linux-x64"),
            patch.object(BUILDER.subprocess, "run") as command,
        ):
            with self.assertRaisesRegex(ValueError, "native host"):
                BUILDER.build(ROOT, "win32-x64", {}, {}, Path("unused"))
            with self.assertRaisesRegex(ValueError, "outside the BYO"):
                BUILDER.build(ROOT, "linux-x64", {"target": "darwin-arm64"}, {}, Path("unused"))
            command.assert_not_called()

    def test_builder_stages_only_native_payload_without_legacy_prepublish(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            extension = root / "extensions/vscode"
            source = json.loads((extension / "package.json").read_text())
            source["scripts"] = {"vscode:prepublish": "legacy hook must not execute"}
            (extension / "package.json").write_text(json.dumps(source))
            backend = extension / "native/linux-x64/thread-backend/thread-backend"
            backend.parent.mkdir(parents=True)
            backend.write_bytes(b"synthetic native backend")
            (extension / "python").mkdir()
            (extension / "python/legacy.py").write_text("legacy backend")

            def command(args, **kwargs):
                if "package" in args:
                    staged = Path(kwargs["cwd"])
                    self.assertFalse((staged / "python").exists())
                    self.assertFalse((staged / "scripts").exists())
                    self.assertNotIn(
                        "vscode:prepublish",
                        json.loads((staged / "package.json").read_text())["scripts"],
                    )
                    Path(args[args.index("--out") + 1]).write_bytes(b"synthetic test transport")

            with (
                patch.object(BUILDER, "host_target", return_value="linux-x64"),
                patch.object(BUILDER.subprocess, "check_output", side_effect=["a" * 40, ""]),
                patch.object(BUILDER.subprocess, "run", side_effect=command),
            ):
                result = BUILDER.build(
                    root,
                    "linux-x64",
                    None,
                    {
                        "target": "linux-x64",
                        "commit": "a" * 40,
                        "checks": record["targets"][0]["checks"],
                    },
                    root / "output",
                )
            self.assertEqual(result["target"], "linux-x64")
            self.assertNotIn("companion", result)
            self.assertFalse(list((root / "output").glob("*.zip")))
            self.assertTrue((root / "output/linux-x64.candidate.json").is_file())
            self.assertEqual(json.loads((extension / "package.json").read_text()), source)

    def test_concurrent_upload_cannot_reuse_same_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            ledger = root / "ledger.json"
            (root / "ledger.json.lock").write_text("another publisher owns this ledger")
            publisher = Mock()
            with self.assertRaises(FileExistsError):
                UPLOAD.process(record, root, ledger, publisher, lambda _: False, True)
            publisher.assert_not_called()

    def test_lock_handle_is_closed_before_removing_lock_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            ledger = root / "ledger.json"
            lock = root / "ledger.json.lock"
            original_open, original_unlink = Path.open, Path.unlink
            handles = []

            def opened(path, *args, **kwargs):
                handle = original_open(path, *args, **kwargs)
                if path == lock:
                    handles.append(handle)
                return handle

            def removed(path, *args, **kwargs):
                if path == lock:
                    self.assertTrue(handles[0].closed)
                return original_unlink(path, *args, **kwargs)

            with patch.object(Path, "open", opened), patch.object(Path, "unlink", removed):
                with self.assertRaisesRegex(RuntimeError, "connection lost"):
                    UPLOAD.process(
                        record,
                        root,
                        ledger,
                        Mock(side_effect=RuntimeError("connection lost")),
                        lambda _: False,
                        True,
                    )
            self.assertFalse(lock.exists())

    def test_public_listing_requires_exact_platform_and_preview_channel(self):
        result = {
            "results": [
                {
                    "extensions": [
                        {
                            "publisher": {"publisherName": "Krishnendra"},
                            "extensionName": "thread-agent",
                            "versions": [
                                {
                                    "version": "0.2.1",
                                    "targetPlatform": "linux-x64",
                                    "properties": [
                                        {
                                            "key": "Microsoft.VisualStudio.Code.PreRelease",
                                            "value": "true",
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        def response(*args, **kwargs):
            return io.BytesIO(json.dumps(result).encode())

        with patch.object(UPLOAD.urllib.request, "urlopen", side_effect=response):
            self.assertTrue(UPLOAD.listing("Krishnendra", "thread-agent", "0.2.1", "linux-x64"))
            self.assertFalse(UPLOAD.listing("Krishnendra", "thread-agent", "0.2.1", "win32-x64"))
            result["results"][0]["extensions"][0]["versions"][0]["properties"] = []
            with self.assertRaisesRegex(ValueError, "preview channel"):
                UPLOAD.listing("Krishnendra", "thread-agent", "0.2.1", "linux-x64")

    def test_aggregation_accepts_exact_six_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            (root / "release.json").unlink()
            for item in record["targets"]:
                candidate = {
                    **item,
                    **{
                        k: record[k]
                        for k in ("schema", "commit", "version", "publisher", "channel")
                    },
                }
                (root / f"{item['target']}.candidate.json").write_text(json.dumps(candidate))
            result = BUILDER.aggregate(root, root, "a" * 40, "0.2.1")
            self.assertEqual(len(result["targets"]), 6)
            with self.assertRaisesRegex(ValueError, "already exists"):
                BUILDER.aggregate(root, root, "a" * 40, "0.2.1")

    def test_failed_aggregation_removes_incomplete_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            (root / "release.json").unlink()
            for item in record["targets"]:
                item["checks"]["editor"]["commit"] = "b" * 40
                candidate = {**item, "commit": "a" * 40, "version": "0.2.1"}
                (root / f"{item['target']}.candidate.json").write_text(json.dumps(candidate))
            with self.assertRaisesRegex(ValueError, "same-commit"):
                BUILDER.aggregate(root, root, "a" * 40, "0.2.1")
            self.assertFalse((root / "release.json").exists())

    def test_default_plan_never_uploads_or_queries_listing_or_writes_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            publisher, listing = Mock(), Mock()
            result = UPLOAD.process(record, root, root / "ledger.json", publisher, listing)
            self.assertEqual(result["operation"], "plan")
            publisher.assert_not_called()
            listing.assert_not_called()
            self.assertFalse((root / "ledger.json").exists())

    def test_uncertain_upload_cannot_be_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            ledger = root / "ledger.json"
            publisher = Mock(side_effect=RuntimeError("connection lost"))
            with self.assertRaisesRegex(RuntimeError, "connection lost"):
                UPLOAD.process(record, root, ledger, publisher, lambda _: False, True)
            publisher.reset_mock()
            with self.assertRaisesRegex(ValueError, "Owner reconciliation"):
                UPLOAD.process(record, root, ledger, publisher, lambda _: False, True)
            publisher.assert_not_called()

    def test_listing_resume_does_not_reupload_and_exact_digest_is_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            ledger = root / "ledger.json"
            publisher = Mock()
            visibility = {item["target"]: False for item in record["targets"]}

            def publish(path):
                publisher(path)
                for item in record["targets"]:
                    if item["vsix"]["file"] == path.name:
                        visibility[item["target"]] = True

            first = UPLOAD.process(record, root, ledger, publish, visibility.get, True)
            self.assertEqual(set(first["targets"].values()), {"verified"})
            self.assertEqual(publisher.call_count, 6)
            publisher.reset_mock()
            UPLOAD.process(record, root, ledger, publisher, visibility.get, True)
            publisher.assert_not_called()
            record["targets"][0]["vsix"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "exact reviewed release"):
                UPLOAD.process(record, root, ledger, publisher, visibility.get, True)

    def test_crash_after_upload_receipt_resumes_only_listing_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.fixture(root)
            ledger = root / "ledger.json"
            publisher = Mock()
            with patch.object(UPLOAD.time, "sleep"):
                with self.assertRaisesRegex(ValueError, "Listing pending"):
                    UPLOAD.process(record, root, ledger, publisher, lambda _: False, True)
            self.assertEqual(publisher.call_count, 1)
            publisher.reset_mock()
            with self.assertRaisesRegex(ValueError, "lacks this ledger"):
                UPLOAD.process(record, root, ledger, publisher, lambda _: True, True)
            publisher.assert_not_called()
            self.assertEqual(
                json.loads(ledger.read_text())["targets"][record["targets"][0]["target"]],
                "verified",
            )


if __name__ == "__main__":
    unittest.main()
