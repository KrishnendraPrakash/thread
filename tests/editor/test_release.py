"""Release checks use synthetic metadata, never publisher credentials or a real license grant."""

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "extensions/vscode/scripts/release.py"
spec = importlib.util.spec_from_file_location("thread_release_checks", SCRIPT)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.extension = self.root / "extensions/vscode"
        self.extension.mkdir(parents=True)
        self.manifest = {
            "publisher": "test-fixture",
            "name": "fixture",
            "version": "0.1.0",
            "license": "UNLICENSED",
            "preview": True,
        }
        self.license = b"SYNTHETIC TEST TEXT - NOT A PROJECT LICENSE. " * 5
        for name in ("README.md", "CHANGELOG.md", "PRIVACY.md"):
            (self.extension / name).write_text("Test fixture")
        self.save_manifest()

    def save_manifest(self):
        (self.extension / "package.json").write_text(json.dumps(self.manifest))

    def configure_fixture(self):
        self.manifest["license"] = "LicenseRef-Synthetic-Test"
        self.save_manifest()
        (self.root / "LICENSE").write_bytes(self.license)

    def archive(self, *, target="darwin-arm64", pre_release="true", extra=None):
        package = self.root / "fixture.vsix"
        xml = f'''<PackageManifest xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"><Metadata><Identity TargetPlatform="{target}"/><Properties><Property Id="Microsoft.VisualStudio.Code.PreRelease" Value="{pre_release}"/></Properties></Metadata></PackageManifest>'''
        files = {
            "extension.vsixmanifest": xml,
            "extension/package.json": json.dumps(self.manifest),
            "extension/LICENSE": self.license,
        }
        for name in (
            "readme.md",
            "changelog.md",
            "PRIVACY.md",
            "python/bridge.py",
            "out/extension.js",
            "python/pathspec-0.dist-info/LICENSE",
            "python/pypdf-0.dist-info/licenses/LICENSE",
        ):
            files["extension/" + name] = "fixture"
        files.update(extra or {})
        with zipfile.ZipFile(package, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return package

    def test_unselected_license_and_mismatched_publisher_stop(self):
        with self.assertRaisesRegex(ValueError, "select a license"):
            release.configuration(self.root, "test-fixture")
        self.configure_fixture()
        with self.assertRaisesRegex(ValueError, "exact Marketplace publisher ID"):
            release.configuration(self.root, "another-owner")
        self.assertEqual(release.configuration(self.root, "test-fixture")["preview"], True)

    def test_package_requires_matching_platform_and_pre_release(self):
        self.configure_fixture()
        for options in ({"target": "win32-x64"}, {"pre_release": "false"}):
            with self.assertRaises(ValueError):
                release.inspect_package(
                    self.archive(**options), self.manifest, "darwin-arm64", self.license
                )
        checked = release.inspect_package(
            self.archive(), self.manifest, "darwin-arm64", self.license
        )
        self.assertEqual(len(checked["sha256"]), 64)
        self.assertEqual(checked["channel"], "pre-release")

    def test_license_changes_and_private_files_stop(self):
        self.configure_fixture()
        for extra in (
            {"extension/.env": "synthetic"},
            {"extension/LICENSE": "changed"},
            {"extension/out/test/fixture.js": "fixture"},
        ):
            with self.assertRaises(ValueError):
                release.inspect_package(
                    self.archive(extra=extra), self.manifest, "darwin-arm64", self.license
                )
