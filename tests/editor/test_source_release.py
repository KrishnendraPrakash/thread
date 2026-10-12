"""Exact source-package identity/content and nonpublishing/uncertain-upload boundaries."""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "extensions/vscode/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


PACKAGE = load("source_package")
UPLOAD = load("source_upload")


class SourceReleaseTests(unittest.TestCase):
    def fixture(self, root):
        (root / "release").mkdir()
        (root / "extensions/vscode").mkdir(parents=True)
        (root / "release/source-vsix-policy.json").write_bytes(
            (ROOT / "release/source-vsix-policy.json").read_bytes()
        )
        manifest = {
            "publisher": "Krishnendra",
            "name": "thread-agent",
            "version": "0.2.1",
            "license": "MIT",
            "preview": True,
            "threadModelProvisioning": "user-supplied",
        }
        (root / "extensions/vscode/package.json").write_text(json.dumps(manifest))
        (root / "LICENSE").write_bytes((ROOT / "LICENSE").read_bytes())
        self.commit = "a" * 40
        files = {
            "extension/package.json": json.dumps(
                {
                    **manifest,
                    "threadDistribution": "source-vsix",
                    "threadPythonRequirement": ">=3.9",
                }
            ),
            "extension.vsixmanifest": '<PackageManifest xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"><Metadata><Identity Id="thread-agent" Publisher="Krishnendra" Version="0.2.1"/><GalleryFlags>Public Preview</GalleryFlags><Properties/></Metadata></PackageManifest>',
            "extension/LICENSE.txt": (root / "LICENSE").read_bytes(),
            "extension/readme.md": "Python 3.9+ required; experimental",
            "extension/changelog.md": "0.2.1",
            "extension/PRIVACY.md": "local",
            "extension/out/extension.js": "// synthetic source fixture",
            "extension/python/bridge.py": "# fixture",
            "extension/python/thread_agent/editor/service.py": "# fixture",
            "extension/python/pathspec/__init__.py": "# fixture",
            "extension/python/pypdf/__init__.py": "# fixture",
            "extension/source-build.json": json.dumps(
                {
                    "commit": self.commit,
                    "distribution": "source-vsix",
                    "working_tree_dirty": False,
                    "dependencies": {"pathspec": "0.12.1", "pypdf": "6.19.0"},
                }
            ),
        }
        for name, version in [("pathspec", "0.12.1"), ("pypdf", "6.19.0")]:
            prefix = f"extension/python/{name}-{version}.dist-info/"
            files[prefix + "LICENSE"] = "retained synthetic third party terms"
            files[prefix + "METADATA"] = f"Name: {name}\nVersion: {version}\n"
        path = root / "source.vsix"
        self.write(path, files)
        return path, files

    def write(self, path, files):
        with zipfile.ZipFile(path, "w") as archive:
            for name, value in files.items():
                archive.writestr(name, value)

    def test_exact_source_scope_does_not_require_native_release_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package, _ = self.fixture(root)
            result = PACKAGE.verify(root, package, self.commit)
            self.assertEqual(result["channel"], "stable")
            self.assertEqual(result["targets"][0]["target"], "universal")
            self.assertEqual(result["python_requirement"], ">=3.9")
            self.assertFalse((root / "release/marketplace-policy.json").exists())

    def test_native_disguise_models_traversal_and_private_paths_stop_validation(self):
        additions = [
            ("extension/native/backend.exe", b"binary"),
            ("extension/out/a.js", b"MZimage"),
            ("extension/python/weights.gguf", b"model"),
            ("../escape", b"text"),
            ("extension/python/.env", b"secret"),
            ("extension/secret.txt", b"private"),
        ]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package, files = self.fixture(root)
            for name, content in additions:
                self.write(package, {**files, name: content})
                with self.assertRaises(ValueError):
                    PACKAGE.verify(root, package, self.commit)

    def test_wrong_hash_identity_channel_and_missing_notices_stop(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package, files = self.fixture(root)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                PACKAGE.verify(root, package, self.commit, "f" * 64)
            changed = json.loads(files["extension/package.json"])
            changed["publisher"] = "other"
            self.write(package, {**files, "extension/package.json": json.dumps(changed)})
            with self.assertRaisesRegex(ValueError, "identity"):
                PACKAGE.verify(root, package, self.commit)
            altered = files["extension.vsixmanifest"].replace(
                "<Properties/>",
                '<Properties><Property Id="Microsoft.VisualStudio.Code.PreRelease" Value="true"/></Properties>',
            )
            self.write(package, {**files, "extension.vsixmanifest": altered})
            with self.assertRaisesRegex(ValueError, "channel"):
                PACKAGE.verify(root, package, self.commit)
            self.write(
                package,
                {
                    k: v
                    for k, v in files.items()
                    if k != "extension/python/pathspec-0.12.1.dist-info/LICENSE"
                },
            )
            with self.assertRaisesRegex(ValueError, "dependency notice"):
                PACKAGE.verify(root, package, self.commit)

    def test_dirty_provenance_and_ambiguous_zip_stop(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package, files = self.fixture(root)
            provenance = json.loads(files["extension/source-build.json"])
            provenance["working_tree_dirty"] = True
            self.write(package, {**files, "extension/source-build.json": json.dumps(provenance)})
            with self.assertRaisesRegex(ValueError, "provenance"):
                PACKAGE.verify(root, package, self.commit)
            self.write(package, files)
            with warnings.catch_warnings(), zipfile.ZipFile(package, "a") as archive:
                warnings.simplefilter("ignore")
                archive.writestr("extension/package.json", "{}")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                PACKAGE.verify(root, package, self.commit)

    def test_default_plan_never_authenticates_queries_uploads_or_writes_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package, _ = self.fixture(root)
            ledger = root / "ledger.json"
            with (
                patch.object(UPLOAD, "versions") as query,
                patch.object(UPLOAD.subprocess, "run") as execute,
            ):
                result = UPLOAD.run(
                    root, package, self.commit, PACKAGE.fingerprint(package)["sha256"], ledger
                )
                self.assertEqual(result["operation"], "plan")
                query.assert_not_called()
                execute.assert_not_called()
                self.assertFalse(ledger.exists())

    def test_execution_fails_before_network_outside_protected_main(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            package, _ = self.fixture(root)
            with patch.dict(os.environ, {}, clear=True), patch.object(UPLOAD, "versions") as query:
                with self.assertRaisesRegex(ValueError, "protected-main"):
                    UPLOAD.run(
                        root,
                        package,
                        self.commit,
                        PACKAGE.fingerprint(package)["sha256"],
                        root / "ledger.json",
                        True,
                    )
                query.assert_not_called()

    def test_source_listing_requires_exact_universal_stable_hash(self):
        record = {
            "publisher": "Krishnendra",
            "version": "0.2.1",
            "targets": [{"vsix": {"sha256": "a" * 64}}],
        }
        listing = {
            "version": "0.2.1",
            "properties": [
                {"key": "Microsoft.VisualStudio.Services.VsixSha256", "value": "a" * 64}
            ],
        }
        with patch.object(UPLOAD, "versions", return_value=[listing]):
            self.assertTrue(UPLOAD.visible(record))
            listing["properties"][0]["value"] = "b" * 64
            with self.assertRaisesRegex(ValueError, "digest"):
                UPLOAD.visible(record)

    def test_source_workflow_oidc_is_only_in_explicit_protected_publish_job(self):
        source = (ROOT / ".github/workflows/source-vsix-release.yml").read_text()
        build, publish = source.split("\njobs:\n", 1)[1].split("\n  publish:\n", 1)
        self.assertNotIn("id-token:", build)
        self.assertNotIn("azure/login", build)
        self.assertIn("default: false", source)
        self.assertIn(
            "(inputs.publish || inputs.check_access) && github.ref == 'refs/heads/main'", publish
        )
        self.assertIn("if: inputs.publish", publish)
        self.assertIn("environment: marketplace-publish", publish)
        self.assertIn("github.repository == 'KrishnendraPrakash/thread'", publish)
        self.assertIn("verify-pat --azure-credential Krishnendra", publish)
        self.assertNotIn("native-release-candidates", source)

    def test_staging_allowlist_ignores_existing_generated_native_and_model_folders(self):
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, files = self.fixture(root)
            extension = root / "extensions/vscode"
            for name, content in [
                ("README.md", "source"),
                ("CHANGELOG.md", "0.2.1"),
                ("PRIVACY.md", "local"),
            ]:
                (extension / name).write_text(content)
            for name in ["out", "media", "native", "models"]:
                (extension / name).mkdir()
            (extension / "out/extension.js").write_text("compiled fixture")
            (extension / "native/backend.exe").write_bytes(b"MZoriginal preserved")
            (extension / "models/model.gguf").write_bytes(b"original preserved")
            source = root / "src/thread_agent"
            source.mkdir(parents=True)
            (source / "__init__.py").write_text("# fixture")
            (extension / "scripts").mkdir()
            for name in ["bridge.py", "install_runtime.py", "runtime_assets.py"]:
                (extension / "scripts" / name).write_text("# fixture")

            def dependency(name):
                return SimpleNamespace(
                    version={"pathspec": "0.12.1", "pypdf": "6.19.0"}[name],
                    read_text=lambda _: "Root-Is-Purelib: true",
                    files=[],
                )

            with patch.object(PACKAGE, "distribution", side_effect=dependency):
                PACKAGE.stage(root, root / "stage", self.commit)
            self.assertFalse((root / "stage/native").exists())
            self.assertFalse((root / "stage/models").exists())
            self.assertEqual(
                (extension / "native/backend.exe").read_bytes(), b"MZoriginal preserved"
            )
            self.assertEqual(
                json.loads((root / "stage/package.json").read_text())["threadDistribution"],
                "source-vsix",
            )
