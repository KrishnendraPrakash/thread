"""Fail-closed boundaries for the inactive Marketplace automation preparation."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "marketplace_preflight", ROOT / "extensions/vscode/scripts/marketplace_preflight.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MarketplacePreflightTests(unittest.TestCase):
    def test_normalized_vsix_license_retains_exact_bytes_and_rejects_ambiguity(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "license.vsix"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("extension/LICENSE.txt", "approved MIT fixture")
            with zipfile.ZipFile(path) as archive:
                MODULE.verify_packaged_license(archive, b"approved MIT fixture")
                with self.assertRaisesRegex(ValueError, "license mismatch"):
                    MODULE.verify_packaged_license(archive, b"different license")
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("extension/LICENSE", "approved MIT fixture")
            with zipfile.ZipFile(path) as archive:
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    MODULE.verify_packaged_license(archive, b"approved MIT fixture")

    def release_fixture(self, root):
        (root / "release").mkdir()
        extension = root / "extensions/vscode"
        (extension / "src").mkdir(parents=True)
        policy = json.loads((ROOT / "release/marketplace-policy.json").read_text())
        policy["gates"] = dict.fromkeys(MODULE.GATES, "passed")
        policy["gates"]["offline_companion_distribution_review"] = "not_applicable"
        (root / "release/marketplace-policy.json").write_text(json.dumps(policy))
        (root / "LICENSE").write_text("Synthetic test license")
        manifest = {
            "publisher": "Krishnendra",
            "name": "thread-agent",
            "version": "0.2.1",
            "license": "TEST",
            "preview": True,
            "threadModelProvisioning": "user-supplied",
        }
        (extension / "package.json").write_text(json.dumps(manifest))
        (extension / "src/extension.ts").write_text("// synthetic enabled fixture")
        record = {
            "schema": 1,
            "commit": "a" * 40,
            "version": "0.2.1",
            "publisher": "Krishnendra",
            "channel": "pre-release",
            "targets": [],
            "distribution_scope": MODULE.BYO_SCOPE,
        }

        def fingerprint(path):
            return {
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }

        for target in sorted(MODULE.TARGETS):
            package = root / f"{target}.vsix"
            executable = "thread-backend.exe" if target.startswith("win32-") else "thread-backend"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("extension/package.json", json.dumps(manifest))
                archive.writestr("extension/LICENSE", (root / "LICENSE").read_bytes())
                archive.writestr(
                    f"extension/native/{target}/thread-backend/{executable}", b"fixture"
                )
                archive.writestr(
                    "extension.vsixmanifest",
                    f'''<PackageManifest
                    xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
                    <Metadata><Identity Id="thread-agent" Publisher="Krishnendra"
                    Version="0.2.1" TargetPlatform="{target}"/><Properties>
                    <Property Id="Microsoft.VisualStudio.Code.PreRelease" Value="true"/>
                    </Properties></Metadata></PackageManifest>''',
                )
            record["targets"].append(
                {
                    "target": target,
                    "vsix": fingerprint(package),
                    "distribution_scope": MODULE.BYO_SCOPE,
                    "checks": {
                        name: {
                            "result": "passed",
                            "commit": "a" * 40,
                            "url": "https://example.test/check",
                        }
                        for name in (
                            "native_package",
                            "security",
                            "editor",
                            "clean_machine",
                            "offline_inference",
                        )
                    },
                }
            )
        (root / "release.json").write_text(json.dumps(record))
        return record

    def test_complete_synthetic_six_target_inventory_is_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.release_fixture(root)
            self.assertEqual(MODULE.inventory(root, root, "a" * 40, "0.2.1"), record)

    def test_duplicate_archive_entries_cannot_override_reviewed_metadata(self):
        for kind, entry, message in (("vsix", "extension/package.json", "Duplicate VSIX"),):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                record = self.release_fixture(root)
                artifact = record["targets"][0][kind]
                path = root / artifact["file"]
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    with zipfile.ZipFile(path, "a") as archive:
                        archive.writestr(entry, "{}")
                artifact["bytes"] = path.stat().st_size
                artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                (root / "release.json").write_text(json.dumps(record))
                with self.assertRaisesRegex(ValueError, message):
                    MODULE.inventory(root, root, "a" * 40, "0.2.1")

    def test_stale_evidence_and_unexpected_companions_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.release_fixture(root)
            record["targets"][0]["checks"]["editor"]["commit"] = "b" * 40
            (root / "release.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "same-commit editor"):
                MODULE.inventory(root, root, "a" * 40, "0.2.1")
            record["targets"][0]["checks"]["editor"]["commit"] = "a" * 40
            record["targets"][0]["companion"] = {"file": "unapproved.zip"}
            (root / "release.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "BYO distribution scope"):
                MODULE.inventory(root, root, "a" * 40, "0.2.1")

    def test_xml_identity_cannot_disagree_with_package_json(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.release_fixture(root)
            item = record["targets"][0]
            path = root / item["vsix"]["file"]
            with zipfile.ZipFile(path) as archive:
                files = {name: archive.read(name) for name in archive.namelist()}
            files["extension.vsixmanifest"] = files["extension.vsixmanifest"].replace(
                b'Publisher="Krishnendra"', b'Publisher="wrong"'
            )
            with zipfile.ZipFile(path, "w") as archive:
                for name, value in files.items():
                    archive.writestr(name, value)
            item["vsix"]["bytes"] = path.stat().st_size
            item["vsix"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            (root / "release.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "XML identity"):
                MODULE.inventory(root, root, "a" * 40, "0.2.1")

    def test_missing_or_duplicate_targets_cannot_publish_after_policy_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "release").mkdir()
            extension = root / "extensions/vscode"
            (extension / "src").mkdir(parents=True)
            policy = json.loads((ROOT / "release/marketplace-policy.json").read_text())
            policy["gates"] = dict.fromkeys(MODULE.GATES, "passed")
            policy["gates"]["offline_companion_distribution_review"] = "not_applicable"
            (root / "release/marketplace-policy.json").write_text(json.dumps(policy))
            (root / "LICENSE").write_text("Synthetic test license")
            manifest = {
                "publisher": "Krishnendra",
                "name": "thread-agent",
                "version": "0.2.1",
                "license": "TEST",
                "preview": True,
                "threadModelProvisioning": "user-supplied",
            }
            (extension / "package.json").write_text(json.dumps(manifest))
            (extension / "src/extension.ts").write_text("// synthetic enabled fixture")
            record = {
                "schema": 1,
                "commit": "a" * 40,
                "version": "0.2.1",
                "publisher": "Krishnendra",
                "channel": "pre-release",
                "distribution_scope": MODULE.BYO_SCOPE,
                "targets": [],
            }
            for targets in ([], [{"target": "linux-x64"}] * 6):
                record["targets"] = targets
                (root / "release.json").write_text(json.dumps(record))
                with self.assertRaisesRegex(ValueError, "Exactly one entry"):
                    MODULE.inventory(root, root, "a" * 40, "0.2.1")

    def test_packaged_publisher_is_checked_against_inventory(self):
        # Verify a real ZIP transport mismatch rather than trusting its inventory claim.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "release").mkdir()
            extension = root / "extensions/vscode"
            (extension / "src").mkdir(parents=True)
            policy = json.loads((ROOT / "release/marketplace-policy.json").read_text())
            policy["gates"] = dict.fromkeys(MODULE.GATES, "passed")
            policy["gates"]["offline_companion_distribution_review"] = "not_applicable"
            (root / "release/marketplace-policy.json").write_text(json.dumps(policy))
            (root / "LICENSE").write_text("Synthetic test license")
            manifest = {
                "publisher": "Krishnendra",
                "name": "thread-agent",
                "version": "0.2.1",
                "license": "TEST",
                "preview": True,
                "threadModelProvisioning": "user-supplied",
            }
            (extension / "package.json").write_text(json.dumps(manifest))
            (extension / "src/extension.ts").write_text("// synthetic enabled fixture")
            package = root / "candidate.vsix"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr(
                    "extension/package.json", json.dumps({**manifest, "publisher": "wrong"})
                )
            entry = {
                "file": package.name,
                "bytes": package.stat().st_size,
                "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
            }
            checks = {
                name: {"result": "passed", "commit": "a" * 40, "url": "https://example.test/check"}
                for name in (
                    "native_package",
                    "security",
                    "editor",
                    "clean_machine",
                    "offline_inference",
                )
            }
            record = {
                "schema": 1,
                "commit": "a" * 40,
                "version": "0.2.1",
                "publisher": "Krishnendra",
                "channel": "pre-release",
                "distribution_scope": MODULE.BYO_SCOPE,
                "targets": [
                    {
                        "target": target,
                        "vsix": entry,
                        "checks": checks,
                        "distribution_scope": MODULE.BYO_SCOPE,
                    }
                    for target in sorted(MODULE.TARGETS)
                ],
            }
            (root / "release.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "Packaged publisher mismatch"):
                MODULE.inventory(root, root, "a" * 40, "0.2.1")

    def test_utf8_source_is_valid_on_all_native_hosts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.release_fixture(root)
            (root / "extensions/vscode/src/extension.ts").write_text(
                "// enabled synthetic fixture — “Unicode” λ\n", encoding="utf-8"
            )
            self.assertEqual(MODULE.readiness(root)["version"], "0.2.1")

    def test_companion_waiver_is_bound_to_exact_scope_and_other_gates_stay_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.release_fixture(root)
            path = root / "release/marketplace-policy.json"
            policy = json.loads(path.read_text())
            policy["distribution_scope"]["official_companions"] = True
            path.write_text(json.dumps(policy))
            with self.assertRaisesRegex(ValueError, "BYO 0.2.1"):
                MODULE.readiness(root)
            policy["distribution_scope"]["official_companions"] = False
            policy["gates"]["complete_third_party_notices"] = "not_applicable"
            path.write_text(json.dumps(policy))
            with self.assertRaisesRegex(ValueError, "complete_third_party_notices"):
                MODULE.readiness(root)

    def test_byo_weights_and_unreferenced_companion_transport_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.release_fixture(root)
            artifact = record["targets"][0]["vsix"]
            path = root / artifact["file"]
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("extension/native/hidden.gguf", b"fake weight")
            artifact["bytes"] = path.stat().st_size
            artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            (root / "release.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "Model weights"):
                MODULE.inventory(root, root, "a" * 40, "0.2.1")
            (root / "unexpected.zip").write_bytes(b"not accepted")
            with self.assertRaisesRegex(ValueError, "outside this release scope"):
                MODULE.inventory(root, root, "a" * 40, "0.2.1")

    def test_byo_keeps_same_commit_offline_user_inference_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = self.release_fixture(root)
            record["targets"][0]["checks"].pop("offline_inference")
            (root / "release.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "offline_inference"):
                MODULE.inventory(root, root, "a" * 40, "0.2.1")

    def test_current_release_is_blocked_before_artifact_access(self):
        with self.assertRaisesRegex(ValueError, "Release gates pending"):
            MODULE.inventory(ROOT, Path("/nonexistent/thread-candidates"), "a" * 40, "0.2.1")

    def test_removing_release_gate_is_not_a_bypass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "release").mkdir()
            (root / "extensions/vscode").mkdir(parents=True)
            policy = json.loads((ROOT / "release/marketplace-policy.json").read_text())
            policy["gates"].pop("windows_editor_activation")
            (root / "release/marketplace-policy.json").write_text(json.dumps(policy))
            (root / "extensions/vscode/package.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "must not be removed"):
                MODULE.readiness(root)

    def test_artifact_tampering_and_size_mismatch_stop_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "candidate.vsix").write_bytes(b"approved")
            record = {
                "file": "candidate.vsix",
                "bytes": 8,
                "sha256": hashlib.sha256(b"approved").hexdigest(),
            }
            self.assertEqual(MODULE.checked_file(root, record), root / "candidate.vsix")
            (root / "candidate.vsix").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "digest differs"):
                MODULE.checked_file(root, record)
            record["bytes"] = 9
            with self.assertRaisesRegex(ValueError, "size differs"):
                MODULE.checked_file(root, record)

    def test_escaping_and_linked_artifacts_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("../candidate.vsix", "/tmp/candidate.vsix", "dir\\candidate.vsix"):
                with self.assertRaisesRegex(ValueError, "basenames"):
                    MODULE.checked_file(root, {"file": name})
            (root / "candidate.vsix").symlink_to(root / "missing")
            with self.assertRaisesRegex(ValueError, "Missing regular artifact"):
                MODULE.checked_file(root, {"file": "candidate.vsix"})


if __name__ == "__main__":
    unittest.main()
