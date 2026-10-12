"""Lightweight policy/acquisition boundaries; no real software/model downloads."""

import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "extensions/vscode/scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "runtime_ci_tests", SCRIPTS / "ci_runtime_integration.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RuntimeCIPolicyTests(unittest.TestCase):
    def test_local_or_wrong_runner_stops_before_network_and_writes(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(MODULE.urllib.request, "urlopen") as network,
        ):
            work = Path(folder) / "new"
            with patch.dict(MODULE.os.environ, {}, clear=True):
                with self.assertRaisesRegex(ValueError, "hosted x64"):
                    MODULE.preflight(work, "linux-x64")
            self.assertFalse(work.exists())
            network.assert_not_called()

    def test_insufficient_disk_stops_before_creating_runtime_storage(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(MODULE, "require_runner"),
            patch.object(MODULE.shutil, "disk_usage") as disk,
        ):
            disk.return_value.free = MODULE.required_disk("linux-x64") - 1
            work = Path(folder) / "new"
            with self.assertRaisesRegex(ValueError, "RESOURCE_STOP"):
                MODULE.preflight(work, "linux-x64")
            self.assertFalse(work.exists())

    def test_additional_vendor_agreements_block_without_automatic_acceptance(self):
        blocks = MODULE.vendor_blocks(
            [{"path": "lib/cudnn64_9.dll"}, {"path": "lib/rocm_v7/runner.dll"}]
        )
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["url"], MODULE.CUDNN_TERMS)
        self.assertEqual(MODULE.vendor_blocks([{"path": "lib/cuda_v12/cublas64.dll"}]), [])

    def test_model_tag_drift_stops_before_blob_acquisition(self):
        with self.assertRaisesRegex(ValueError, "tag drift"):
            MODULE.verify_manifest(b'{"changed":"tag"}')

    def test_exact_blob_hash_and_size_required_no_overwrite(self):
        class Response(io.BytesIO):
            url = "https://approved.example/blob"

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "blob"
            with patch.object(MODULE.urllib.request, "urlopen", return_value=Response(b"fixture")):
                MODULE.download_blob(
                    Response.url, output, 7, hashlib.sha256(b"fixture").hexdigest()
                )
            self.assertEqual(output.read_bytes(), b"fixture")
            with self.assertRaisesRegex(ValueError, "overwrite"):
                MODULE.download_blob(Response.url, output, 7, "a" * 64)
            for name, size, sha in (("wrong-hash", 7, "a" * 64), ("oversize", 6, "a" * 64)):
                with patch.object(
                    MODULE.urllib.request, "urlopen", return_value=Response(b"fixture")
                ):
                    with self.assertRaises(ValueError):
                        MODULE.download_blob(Response.url, Path(folder) / name, size, sha)
                self.assertFalse((Path(folder) / name).exists())
                self.assertFalse((Path(folder) / name).with_suffix(".partial").exists())

    def test_approved_descriptor_set_is_exact(self):
        document = {
            "config": {"digest": "sha256:" + list(MODULE.BLOBS)[0], "size": 490},
            "layers": [
                {"digest": "sha256:" + sha, "size": size}
                for sha, size in list(MODULE.BLOBS.items())[1:]
            ],
        }
        data = json.dumps(document).encode()
        with patch.object(MODULE, "MANIFEST_SHA", hashlib.sha256(data).hexdigest()):
            self.assertEqual(MODULE.verify_manifest(data), document)
        document["layers"].append(document["layers"][0])
        data = json.dumps(document).encode()
        with patch.object(MODULE, "MANIFEST_SHA", hashlib.sha256(data).hexdigest()):
            with self.assertRaisesRegex(ValueError, "differ"):
                MODULE.verify_manifest(data)
