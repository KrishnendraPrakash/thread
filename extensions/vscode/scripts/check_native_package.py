"""Inspect and extract a local native VSIX candidate, then probe its actual backend.

This does not publish, select a license or establish notarization/inference support.
"""

import argparse
import hashlib
import json
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

from freeze import host_target

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("package", type=Path)
args = parser.parse_args()
target = host_target()
prefix = f"extension/native/{target}/thread-backend/"
with (
    zipfile.ZipFile(args.package) as archive,
    tempfile.TemporaryDirectory(prefix="thread-native-vsix-") as folder,
):
    xml = ElementTree.fromstring(archive.read("extension.vsixmanifest"))
    ns = {"v": "http://schemas.microsoft.com/developer/vsx-schema/2011"}
    identity = xml.find("v:Metadata/v:Identity", ns)
    if identity is None or identity.get("TargetPlatform") != target:
        raise ValueError("VSIX target does not match the native host.")
    manifest = json.loads(archive.read("extension/package.json"))
    if manifest.get("preview") is not True:
        raise ValueError("Native candidate must remain a preview.")
    entries = [item for item in archive.infolist() if item.filename.startswith(prefix)]
    if not entries or sum(item.file_size for item in entries) > 512 * 1024**2:
        raise ValueError("Missing or oversized native payload.")
    root = Path(folder)
    for item in entries:
        relative = PurePosixPath(item.filename)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in item.filename
            or stat.S_ISLNK(item.external_attr >> 16)
        ):
            raise ValueError("Unsafe native VSIX entry.")
        destination = root.joinpath(*relative.parts)
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as output:
                output.write(archive.read(item))
            destination.chmod((item.external_attr >> 16) & 0o777 or 0o644)
    names = [item.filename for item in entries]
    for dependency in ("pathspec-", "pypdf-", "zstandard-"):
        if not any(dependency in name and "license" in name.lower() for name in names):
            raise ValueError(f"Missing packaged dependency notice: {dependency}")
    if not any(name.endswith("notices/provenance.json") for name in names):
        raise ValueError("Missing native notice provenance.")
    native_notice = prefix + "notices/zstd-1.5.7-LICENSE"
    if (
        native_notice not in names
        or hashlib.sha256(archive.read(native_notice)).hexdigest()
        != "7055266497633c9025b777c78eb7235af13922117480ed5c674677adc381c9d8"
    ):
        raise ValueError("Missing or changed verified Zstandard native-library notice.")
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("check_native.py")),
            "--extension-root",
            str(root / "extension"),
        ],
        check=True,
    )
print(
    json.dumps(
        {
            "package": args.package.name,
            "bytes": args.package.stat().st_size,
            "sha256": hashlib.sha256(args.package.read_bytes()).hexdigest(),
            "target": target,
            "native_protocol_checked": True,
            "public_release_ready": False,
        },
        indent=2,
    )
)
