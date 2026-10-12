"""CI-only Windows package and pinned VS Code acquisition. Never publish.

Private test packaging intentionally remains separate from production release
approval. No model/runtime assets, signing keys or publisher credentials are used.
"""

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[3]
PIN = ROOT / "extensions/vscode/test-config/windows-vscode.json"


def verified_extract(archive, output):
    if output.exists() or output.is_symlink():
        raise ValueError("VS Code output must be a fresh directory.")
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        if len(entries) > 100000 or sum(x.file_size for x in entries) > 2 * 1024**3:
            raise ValueError("VS Code archive exceeds bounds.")
        names = set()
        for entry in entries:
            name = PurePosixPath(entry.filename)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in entry.filename
                or ":" in entry.filename
                or stat.S_ISLNK(entry.external_attr >> 16)
                or entry.filename.casefold() in names
            ):
                raise ValueError("Unsafe or duplicate VS Code archive entry.")
            names.add(entry.filename.casefold())
        output.mkdir(parents=True)
        try:
            source.extractall(output)
        except BaseException:
            shutil.rmtree(output)
            raise


def download(output, pin):
    address = urlsplit(pin["url"])
    if (
        address.scheme != "https"
        or address.hostname != "vscode.download.prss.microsoft.com"
        or pin.get("platform") != "win32-x64-archive"
        or not re.fullmatch(r"[0-9a-f]{64}", pin["sha256"])
        or pin["commit"] not in address.path
    ):
        raise ValueError("Expected pinned official Microsoft Windows archive.")
    if output.exists() or output.is_symlink():
        raise ValueError("VS Code output already exists.")
    with tempfile.TemporaryDirectory(prefix="thread-code-download-") as folder:
        archive = Path(folder) / "code.zip"
        digest = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(pin["url"], timeout=60) as source, archive.open("xb") as target:
            while chunk := source.read(1024 * 1024):
                size += len(chunk)
                if size > 512 * 1024**2:
                    raise ValueError("VS Code download exceeds 512 MiB.")
                digest.update(chunk)
                target.write(chunk)
        if digest.hexdigest() != pin["sha256"]:
            raise ValueError("Pinned VS Code archive digest mismatch; nothing extracted.")
        verified_extract(archive, output)
    runtime_directory = pin.get("runtime_directory", "")
    if runtime_directory and runtime_directory != pin["commit"][:10]:
        raise ValueError("Runtime directory must match the pinned commit prefix.")
    app = output / runtime_directory / "resources/app"
    if (
        json.loads((app / "package.json").read_text())["version"] != pin["version"]
        or json.loads((app / "product.json").read_text())["commit"] != pin["commit"]
    ):
        raise ValueError("Extracted VS Code version/commit mismatch.")
    return output / "Code.exe"


def package(root, output):
    if output.exists() or output.is_symlink():
        raise ValueError("CI-only package output already exists.")
    extension = root / "extensions/vscode"
    native = extension / "native/win32-x64"
    if not (native / "thread-backend/thread-backend.exe").is_file():
        raise ValueError("Build the Windows x64 backend before private test packaging.")
    manifest = json.loads((extension / "package.json").read_text())
    with tempfile.TemporaryDirectory(prefix="thread-private-vsix-") as folder:
        stage = Path(folder) / "extension"
        shutil.copytree(
            extension,
            stage,
            ignore=shutil.ignore_patterns(
                "node_modules",
                "src",
                "scripts",
                "python",
                "native",
                "test",
                "test-config",
                "*.map",
                "package-lock.json",
                "tsconfig.json",
            ),
        )
        shutil.copytree(native, stage / "native/win32-x64")
        shutil.copy2(root / "LICENSE", stage / "LICENSE")
        staged = {
            **manifest,
            "scripts": {
                k: v for k, v in manifest.get("scripts", {}).items() if k != "vscode:prepublish"
            },
        }
        (stage / "package.json").write_text(json.dumps(staged, indent=2) + "\n")
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                shutil.which("node") or "node",
                str(extension / "node_modules/@vscode/vsce/vsce"),
                "package",
                "--pre-release",
                "--no-dependencies",
                "--target",
                "win32-x64",
                "--out",
                str(output.resolve()),
            ],
            cwd=stage,
            check=True,
        )
    with zipfile.ZipFile(output) as archive:
        packaged = json.loads(archive.read("extension/package.json"))
        for key in ("name", "publisher", "version", "license", "preview"):
            if packaged[key] != manifest[key]:
                raise ValueError("CI package metadata mismatch.")
        ns = {"v": "http://schemas.microsoft.com/developer/vsx-schema/2011"}
        xml = ElementTree.fromstring(archive.read("extension.vsixmanifest"))
        if xml.find("v:Metadata/v:Identity", ns).get("TargetPlatform") != "win32-x64":
            raise ValueError("CI package target mismatch.")
        if archive.read("extension/LICENSE.txt") != (root / "LICENSE").read_bytes():
            raise ValueError("CI package license bytes mismatch.")
        if any(name.startswith("extension/python/") for name in archive.namelist()):
            raise ValueError("Native CI package must not include a legacy Python bridge.")
    output.with_suffix(".ci-only.json").write_text(
        json.dumps(
            {
                "file": output.name,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "version": manifest["version"],
                "target": "win32-x64",
                "ci_only": True,
                "public_release_ready": False,
            },
            indent=2,
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("download", "package"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.operation == "download":
        print(download(args.output, json.loads(PIN.read_text())))
    else:
        package(ROOT, args.output)


if __name__ == "__main__":
    main()
