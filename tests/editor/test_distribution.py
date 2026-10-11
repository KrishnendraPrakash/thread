"""Distribution integrity checks use tiny fixtures, never real runtimes/models."""

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "extensions/vscode/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("offline_bundle", SCRIPTS / "offline_bundle.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.path.remove(str(SCRIPTS))


class OfflineBundleTests(unittest.TestCase):
    def test_assembly_copies_verified_inputs_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            source = root / "source"
            source.mkdir()
            recipe = self.fixture(source)
            (source / "model").unlink()
            (source / "models").mkdir()
            (source / "models/blob").write_bytes(b"model")
            recipe["assets"][2]["path"] = "models/blob"
            recipe.update(
                runtimeExecutable="runtime",
                runtimeVersion="fixture",
                modelDirectory="models",
                model="fixture:tiny",
            )
            for asset in recipe["assets"]:
                asset["input"] = str(source / asset["path"])
            output = root / "assembled"
            module.assemble_bundle(recipe, output)
            manifest = module.validate_bundle(output, "darwin-arm64")
            self.assertTrue(all("input" not in asset for asset in manifest["assets"]))
            with self.assertRaisesRegex(ValueError, "already exists"):
                module.assemble_bundle(recipe, output)
            self.assertEqual((output / "models/blob").read_bytes(), b"model")
            (source / "models/blob").write_bytes(b"WRONG")
            failed = root / "failed"
            with self.assertRaisesRegex(ValueError, "size mismatch|checksum mismatch"):
                module.assemble_bundle(recipe, failed)
            self.assertFalse(failed.exists())
            self.assertFalse(any(root.glob(".thread-assemble-*")))

    def test_native_alias_materialization_and_external_link_rejection(self):
        freeze = sys.modules["freeze"]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "versions/actual").mkdir(parents=True)
            (root / "versions/actual/binary").write_bytes(b"native fixture")
            (root / "versions/current").symlink_to(
                root / "versions/actual", target_is_directory=True
            )
            (root / "binary").symlink_to(root / "versions/current/binary")
            freeze.materialize_links(root)
            self.assertFalse(any(item.is_symlink() for item in root.rglob("*")))
            self.assertEqual((root / "binary").read_bytes(), b"native fixture")
            (root / "outside").symlink_to(root.parent)
            with self.assertRaisesRegex(ValueError, "external"):
                freeze.materialize_links(root)
            self.assertTrue((root / "outside").is_symlink())

    def fixture(self, root):
        assets = []
        for role in ("backend", "runtime", "model", "notice"):
            content = role.encode()
            (root / role).write_bytes(content)
            assets.append(
                {
                    "path": role,
                    "role": role,
                    "size": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "source": "synthetic",
                    "license": "test-only",
                    "version": "fixture",
                }
            )
        manifest = {"schema": 1, "target": "darwin-arm64", "assets": assets}
        (root / "bundle.json").write_text(json.dumps(manifest))
        return manifest

    def test_inventory_and_target(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            expected = self.fixture(root)
            self.assertEqual(module.validate_bundle(root, "darwin-arm64"), expected)
            with self.assertRaisesRegex(ValueError, "target mismatch"):
                module.validate_bundle(root, "win32-x64")

    def test_tampered_and_unlisted_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            (root / "model").write_bytes(b"wrong")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                module.validate_bundle(root, "darwin-arm64")
            self.fixture(root)
            (root / "extra").write_text("unexpected")
            with self.assertRaisesRegex(ValueError, "unlisted"):
                module.validate_bundle(root, "darwin-arm64")

    def test_paths_and_provenance(self):
        for mutation in (
            lambda asset: asset.update(path="../outside"),
            lambda asset: asset.update(license=""),
        ):
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                manifest = self.fixture(root)
                mutation(manifest["assets"][0])
                (root / "bundle.json").write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    module.validate_bundle(root, "darwin-arm64")
