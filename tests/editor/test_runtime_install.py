"""Managed runtime installer boundaries using synthetic local archives only."""

import hashlib
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "extensions/vscode/scripts/install_runtime.py"
SPEC = importlib.util.spec_from_file_location("thread_runtime_install", SCRIPT)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class RuntimeInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def archive(self, name="ollama", kind=tarfile.REGTYPE, link=""):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            item = tarfile.TarInfo(name)
            item.type = kind
            item.linkname = link
            item.mode = 0o755
            data = b"synthetic executable"
            item.size = len(data) if kind == tarfile.REGTYPE else 0
            archive.addfile(item, io.BytesIO(data) if item.size else None)
        return buffer.getvalue()

    def test_archive_traversal_special_files_and_external_links_rejected(self):
        for index, args in enumerate(
            [
                ("../escape",),
                ("/escape",),
                ("device", tarfile.CHRTYPE),
                ("ollama", tarfile.SYMTYPE, "../../escape"),
            ]
        ):
            with self.subTest(args=args):
                archive = self.root / f"bad{index}.tgz"
                archive.write_bytes(self.archive(*args))
                out = self.root / f"out{index}"
                out.mkdir()
                with self.assertRaises(ValueError):
                    installer.unpack(archive, out)
        self.assertFalse((self.root / "escape").exists())

    def test_checksum_failure_never_installs_and_releases_lock(self):
        content = self.archive()

        class Response(io.BytesIO):
            url = "https://official.example/test"

        with (
            patch.object(installer.urllib.request, "urlopen", return_value=Response(content)),
            patch.object(installer, "SIZE", len(content)),
        ):
            with self.assertRaisesRegex(ValueError, "checksum"):
                installer.install(self.root)
        self.assertFalse((self.root / f"ollama-{installer.VERSION}").exists())
        self.assertFalse((self.root / "install.lock").exists())

    def test_verified_archive_is_atomically_installed_with_no_redownload(self):
        content = self.archive()

        class Response(io.BytesIO):
            url = "https://official.example/test"

        with (
            patch.object(
                installer.urllib.request, "urlopen", return_value=Response(content)
            ) as download,
            patch.object(installer, "SIZE", len(content)),
            patch.object(installer, "SHA256", hashlib.sha256(content).hexdigest()),
        ):
            installer.install(self.root)
            installer.install(self.root)
            self.assertEqual(download.call_count, 1)
        final = self.root / f"ollama-{installer.VERSION}"
        self.assertEqual((final / "ollama").read_bytes(), b"synthetic executable")
        self.assertEqual(
            json.loads((final / "installed.json").read_text())["version"], installer.VERSION
        )
        self.assertFalse((self.root / "install.lock").exists())
