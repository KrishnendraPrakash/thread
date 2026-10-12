"""Native source/payload attribution boundaries using tiny nonexecuted files."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "extensions/vscode/scripts/native_inventory.py"
SPEC = importlib.util.spec_from_file_location("native_inventory_tests", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class NativeInventoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source.so"
        self.source.write_bytes(b"source")
        self.payload = self.root / "payload"
        (self.payload / "_internal/pkg").mkdir(parents=True)
        (self.payload / "_internal/pkg/extension.so").write_bytes(b"rewritten")

    def test_native_extensions_are_included_and_rewritten_payload_is_distinct(self):
        toc = [
            [
                ("pkg/extension.so", str(self.source), "EXTENSION"),
                ("ignore.txt", "not opened", "DATA"),
            ]
        ]
        result = MODULE.collected_binaries(toc, self.payload)
        self.assertEqual(len(result["entries"]), 1)
        row = result["entries"][0]
        self.assertEqual(row["kind"], "EXTENSION")
        self.assertFalse(row["source_bytes_identical"])
        self.assertNotIn(str(self.root), str(result))
        self.assertFalse(result["complete_distribution_review"])

    def test_unsafe_destinations_are_rejected_before_source_access(self):
        for name in ("../escape", "/absolute", "C:\\escape", "pkg//file", "pkg/./file"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Unsafe"):
                MODULE.collected_binaries([[(name, "missing", "BINARY")]], self.payload)

    def test_missing_conflicting_and_ambiguous_payloads_fail(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            MODULE.collected_binaries([[("missing", str(self.source), "BINARY")]], self.payload)
        toc = [
            [
                ("pkg/extension.so", str(self.source), "BINARY"),
                ("pkg/extension.so", str(self.source), "EXTENSION"),
            ]
        ]
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            MODULE.collected_binaries(toc, self.payload)
        (self.payload / "pkg").mkdir()
        (self.payload / "pkg/extension.so").write_bytes(b"duplicate")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            MODULE.collected_binaries([toc[0][:1]], self.payload)

    def test_parent_link_cannot_redirect_inventory_outside_payload(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "binary.so").write_bytes(b"outside")
        (self.payload / "redirect").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "escaped"):
            MODULE.collected_binaries(
                [[("redirect/binary.so", str(self.source), "BINARY")]], self.payload
            )

    def test_windows_omits_only_os_origin_api_set_and_ucrt_payloads(self):
        windows = self.root / "Windows"
        system = windows / "System32/downlevel"
        system.mkdir(parents=True)
        vendor = self.root / "vendor"
        vendor.mkdir()
        items = []
        for name, parent in [
            ("api-ms-win-crt-fixture.dll", system),
            ("ucrtbase.dll", system),
            ("vcruntime140.dll", system),
            ("api-ms-win-core-vendor.dll", vendor),
        ]:
            source = parent / name
            source.write_bytes(b"synthetic native bytes never executed")
            destination = self.payload / "_internal" / name
            destination.write_bytes(source.read_bytes())
            items.append((name, str(source), "BINARY"))
        filtered, omitted = MODULE.omit_windows_os_images([items], self.payload, windows)
        self.assertEqual(
            {row["source_name"] for row in omitted}, {"api-ms-win-crt-fixture.dll", "ucrtbase.dll"}
        )
        self.assertEqual(len(MODULE.collected_binaries(filtered, self.payload)["entries"]), 2)
        self.assertTrue((self.payload / "_internal/vcruntime140.dll").is_file())
        self.assertTrue((self.payload / "_internal/api-ms-win-core-vendor.dll").is_file())
        self.assertTrue((system / "ucrtbase.dll").is_file())

    def test_windows_omission_validates_entire_payload_before_any_delete(self):
        system = self.root / "Windows/System32"
        system.mkdir(parents=True)
        source = system / "ucrtbase.dll"
        source.write_bytes(b"synthetic bytes")
        destination = self.payload / "_internal/ucrtbase.dll"
        destination.write_bytes(source.read_bytes())
        toc = [[("ucrtbase.dll", str(source), "BINARY"), ("../unsafe.dll", str(source), "BINARY")]]
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            MODULE.omit_windows_os_images(toc, self.payload, system.parent)
        self.assertTrue(destination.is_file())

    def test_copied_os_family_requires_exact_installed_os_bytes(self):
        system = self.root / "Windows/System32/downlevel"
        system.mkdir(parents=True)
        source = self.root / "api-ms-win-crt-copy.dll"
        source.write_bytes(b"copy")
        installed = system / source.name
        installed.write_bytes(b"other")
        destination = self.payload / "_internal" / source.name
        destination.write_bytes(source.read_bytes())
        toc = [[(source.name, str(source), "BINARY")]]
        _, omitted = MODULE.omit_windows_os_images(toc, self.payload, system.parents[1])
        self.assertEqual(omitted, [])
        self.assertTrue(destination.is_file())
        installed.write_bytes(source.read_bytes())
        filtered, omitted = MODULE.omit_windows_os_images(toc, self.payload, system.parents[1])
        self.assertEqual(len(omitted), 1)
        self.assertEqual(filtered, [[]])
        self.assertFalse(destination.exists())

    def test_windows_component_store_requires_microsoft_component_path(self):
        windows = self.root / "Windows"
        component = (
            windows / "WinSxS/amd64_microsoft-windows-ucrt_31bf3856ad364e35_10.0.1.0_none_fixture"
        )
        component.mkdir(parents=True)
        source = component / "ucrtbase.dll"
        source.write_bytes(b"fixture component image")
        destination = self.payload / "_internal/ucrtbase.dll"
        destination.write_bytes(source.read_bytes())
        filtered, omitted = MODULE.omit_windows_os_images(
            [[("ucrtbase.dll", str(source), "BINARY")]], self.payload, windows
        )
        self.assertEqual(len(omitted), 1)
        self.assertEqual(filtered, [[]])
        other = windows / "WinSxS/unrelated"
        other.mkdir()
        source = other / "ucrtbase.dll"
        source.write_bytes(b"unrelated bytes")
        destination.write_bytes(source.read_bytes())
        _, omitted = MODULE.omit_windows_os_images(
            [[("ucrtbase.dll", str(source), "BINARY")]], self.payload, windows
        )
        self.assertEqual(omitted, [])
        self.assertTrue(destination.exists())

    def test_windows_build_discovery_excludes_ambient_jdk_and_preserves_parent(self):
        original = {
            "SystemRoot": "/fixture/Windows",
            "PATH": "/fixture/Java/bin;/fixture/Git/bin",
            "KEEP": "value",
        }
        result = MODULE.native_build_environment(
            "win32-x64", original, Path("/fixture/Python"), "/fixture/Python/python.exe"
        )
        self.assertNotIn("Java", result["PATH"])
        self.assertNotIn("Git", result["PATH"])
        self.assertIn("/fixture/Windows/System32", result["PATH"])
        self.assertIn("/fixture/Python/DLLs", result["PATH"])
        self.assertEqual(result["KEEP"], "value")
        self.assertIn("Java", original["PATH"])
        self.assertEqual(
            MODULE.native_build_environment(
                "linux-x64", original, Path("/fixture/Python"), "/fixture/Python/python"
            ),
            original,
        )
