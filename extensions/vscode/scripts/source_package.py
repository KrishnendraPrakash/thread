"""Build/validate a universal Python-source VSIX, never acquire native assets or publish."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from importlib.metadata import distribution
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[3]
MAX_BYTES = 64 * 1024**2
MAX_FILE_BYTES = 4 * 1024**2
PROFILE = "source-vsix"
NATIVE_SUFFIXES = {".exe", ".dll", ".pyd", ".so", ".dylib", ".gguf", ".safetensors", ".zip", ".whl"}
MAGIC = (
    b"MZ",
    b"\x7fELF",
    b"\xfe\xed\xfa\xce",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
)


def fingerprint(path):
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def policy(root):
    value = json.loads((root / "release/source-vsix-policy.json").read_text(encoding="utf-8"))
    expected = {
        "schema": 1,
        "version": "0.2.1",
        "publisher": "Krishnendra",
        "extension": "thread-agent",
        "distribution": PROFILE,
        "target": "universal",
        "channel": "stable",
        "preview": True,
        "project_license": "MIT",
        "python_requirement": ">=3.9",
        "models": "user-supplied",
        "dependencies": {"pathspec": "0.12.1", "pypdf": "6.19.0"},
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise ValueError("Source-only release scope differs from owner approval.")
    manifest = json.loads((root / "extensions/vscode/package.json").read_text(encoding="utf-8"))
    if (
        manifest.get("version") != value["version"]
        or manifest.get("publisher") != value["publisher"]
        or manifest.get("name") != value["extension"]
        or manifest.get("license") != "MIT"
        or manifest.get("preview") is not True
    ):
        raise ValueError("Source release identity/version/license does not match the manifest.")
    return value, manifest


def archive_entries(archive):
    entries, total, seen = [], 0, set()
    if len(archive.infolist()) > 3000:
        raise ValueError("Source VSIX file limit exceeded.")
    for info in archive.infolist():
        name = info.filename
        parts = name.rstrip("/").split("/")
        if (
            not name
            or "\\" in name
            or ":" in name
            or "\0" in name
            or PurePosixPath(name).is_absolute()
            or any(p in {"", ".", ".."} for p in parts)
            or name.casefold() in seen
        ):
            raise ValueError("Unsafe or duplicate source VSIX entry.")
        seen.add(name.casefold())
        mode = (info.external_attr >> 16) & 0o170000
        if mode not in {0, stat.S_IFREG, stat.S_IFDIR} or info.flag_bits & 1:
            raise ValueError("Source VSIX rejects links, special files and encryption.")
        if info.is_dir():
            continue
        if not (
            name
            in {
                "extension.vsixmanifest",
                "[Content_Types].xml",
                "extension/package.json",
                "extension/readme.md",
                "extension/changelog.md",
                "extension/PRIVACY.md",
                "extension/LICENSE",
                "extension/LICENSE.txt",
                "extension/source-build.json",
            }
            or name.startswith(("extension/python/", "extension/out/", "extension/media/"))
        ):
            raise ValueError("Source VSIX contains an unapproved staging path.")
        total += info.file_size
        if info.file_size > MAX_FILE_BYTES or total > MAX_BYTES:
            raise ValueError("Source VSIX byte limit exceeded.")
        if (
            any(
                p.lower()
                in {
                    "native",
                    "models",
                    "node_modules",
                    "test",
                    "tests",
                    "test-config",
                    "__pycache__",
                    ".git",
                    ".thread-agent",
                }
                for p in parts
            )
            or name.startswith(("extension/src/", "extension/scripts/", "extension/notices/"))
            or any(p.lower().startswith((".env", "sha256-")) for p in parts)
            or PurePosixPath(name).suffix.lower()
            in NATIVE_SUFFIXES | {".pyc", ".map", ".sqlite", ".sqlite3", ".pem", ".key"}
        ):
            raise ValueError("Source VSIX contains native/model/development/private content.")
        content = archive.read(info)
        if content.startswith(MAGIC):
            raise ValueError("Source VSIX contains a native image disguised as text.")
        entries.append((name, content))
    return entries


def verify(root, package, commit, expected_sha=None):
    import re

    scope, configured = policy(root)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected exact source commit.")
    if not package.is_file() or package.is_symlink() or package.stat().st_size > MAX_BYTES:
        raise ValueError("Source package must be a bounded regular file.")
    stamp = fingerprint(package)
    if expected_sha is not None and stamp["sha256"] != expected_sha:
        raise ValueError("Source package SHA-256 differs from reviewed bytes.")
    with zipfile.ZipFile(package) as archive:
        files = dict(archive_entries(archive))
        required = {
            "extension/package.json",
            "extension.vsixmanifest",
            "extension/readme.md",
            "extension/changelog.md",
            "extension/PRIVACY.md",
            "extension/source-build.json",
            "extension/out/extension.js",
            "extension/python/bridge.py",
            "extension/python/thread_agent/editor/service.py",
            "extension/python/pathspec/__init__.py",
            "extension/python/pypdf/__init__.py",
        }
        if not required.issubset(files):
            raise ValueError("Source VSIX is missing required runtime/source/documentation files.")
        licenses = [
            name for name in files if name in {"extension/LICENSE", "extension/LICENSE.txt"}
        ]
        if len(licenses) != 1 or files[licenses[0]] != (root / "LICENSE").read_bytes():
            raise ValueError("Source package project license mismatch or ambiguity.")
        packaged = json.loads(files["extension/package.json"])
        for key in (
            "publisher",
            "name",
            "version",
            "license",
            "preview",
            "threadModelProvisioning",
        ):
            if packaged.get(key) != configured.get(key):
                raise ValueError("Source packaged identity/scope mismatch: " + key)
        if (
            packaged.get("threadDistribution") != PROFILE
            or packaged.get("threadPythonRequirement") != ">=3.9"
        ):
            raise ValueError("Source package must disclose its external Python requirement.")
        receipt = json.loads(files["extension/source-build.json"])
        if (
            receipt.get("commit") != commit
            or receipt.get("distribution") != PROFILE
            or receipt.get("dependencies") != scope["dependencies"]
            or receipt.get("working_tree_dirty") is not False
        ):
            raise ValueError("Source build provenance differs or is dirty.")
        xml_bytes = files["extension.vsixmanifest"]
        if b"<!DOCTYPE" in xml_bytes.upper() or b"<!ENTITY" in xml_bytes.upper():
            raise ValueError("Source VSIX XML declarations are unsafe.")
        xml = ElementTree.fromstring(xml_bytes)
        ns = {"v": "http://schemas.microsoft.com/developer/vsx-schema/2011"}
        identity = xml.find("v:Metadata/v:Identity", ns)
        if identity is None or (
            identity.get("Id"),
            identity.get("Publisher"),
            identity.get("Version"),
            identity.get("TargetPlatform"),
        ) != (scope["extension"], scope["publisher"], scope["version"], None):
            raise ValueError("Expected the approved universal source VSIX identity.")
        props = {
            p.get("Id"): p.get("Value")
            for p in xml.findall("v:Metadata/v:Properties/v:Property", ns)
        }
        if props.get("Microsoft.VisualStudio.Code.PreRelease", "false") != "false":
            raise ValueError("Source package channel must remain stable.")
        gallery = xml.findtext("v:Metadata/v:GalleryFlags", default="", namespaces=ns)
        if "Preview" not in gallery.split():
            raise ValueError("Source package must retain the experimental preview label.")
        for name, version in scope["dependencies"].items():
            prefix = f"extension/python/{name}-{version}.dist-info/"
            candidates = [n for n in files if n.startswith(prefix) and "license" in n.lower()]
            if not candidates or not any(files[n].strip() for n in candidates):
                raise ValueError("Missing exact bundled dependency notice: " + name)
            from email.parser import BytesParser

            metadata = BytesParser().parsebytes(files.get(prefix + "METADATA", b""))
            if metadata.get("Name") != name or metadata.get("Version") != version:
                raise ValueError("Bundled dependency metadata differs: " + name)
    return {
        "schema": 1,
        "commit": commit,
        "version": scope["version"],
        "publisher": scope["publisher"],
        "channel": "stable",
        "distribution": PROFILE,
        "python_requirement": ">=3.9",
        "dependencies": scope["dependencies"],
        "file_count": len(files),
        "targets": [{"target": "universal", "vsix": stamp}],
    }


def copy_tree(source, output, excluded=()):
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if any(part in excluded for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError("Source staging rejects source links.")
        if path.is_file():
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def stage(root, output, commit):
    scope, manifest = policy(root)
    output.mkdir(exist_ok=False)
    extension = root / "extensions/vscode"
    # Explicit allowlist: ambient native/model/notices folders never enter staging.
    for name in ("README.md", "CHANGELOG.md", "PRIVACY.md"):
        shutil.copy2(extension / name, output / name)
    shutil.copy2(root / "LICENSE", output / "LICENSE")
    for name in ("media", "out"):
        copy_tree(extension / name, output / name, {"test", "tests", "__pycache__"})
    for path in (output / "out").rglob("*.map"):
        path.unlink()
    copy_tree(root / "src/thread_agent", output / "python/thread_agent", {"__pycache__"})
    for name, version in scope["dependencies"].items():
        package = distribution(name)
        if package.version != version or "Root-Is-Purelib: true" not in (
            package.read_text("WHEEL") or ""
        ):
            raise ValueError("Source build requires the exact pure-Python dependency: " + name)
        for file in package.files or []:
            if (
                ".." in file.parts
                or "__pycache__" in file.parts
                or file.suffix == ".pyc"
                or file.name in {"INSTALLER", "REQUESTED", "RECORD", "direct_url.json"}
            ):
                continue
            source = Path(package.locate_file(file))
            if source.is_symlink():
                raise ValueError("Source dependency links are not permitted.")
            destination = output / "python" / file
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    for name in ("bridge.py", "install_runtime.py", "runtime_assets.py"):
        shutil.copy2(extension / "scripts" / name, output / "python" / name)
    manifest.update(threadDistribution=PROFILE, threadPythonRequirement=">=3.9", scripts={})
    manifest.pop("devDependencies", None)
    (output / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "source-build.json").write_text(
        json.dumps(
            {
                "commit": commit,
                "distribution": PROFILE,
                "working_tree_dirty": False,
                "dependencies": scope["dependencies"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def probe(root, package, commit):
    verify(root, package, commit)
    with (
        tempfile.TemporaryDirectory(prefix="thread-source-probe-") as folder,
        zipfile.ZipFile(package) as archive,
    ):
        stage_root = Path(folder)
        for name, content in archive_entries(archive):
            path = stage_root.joinpath(*PurePosixPath(name).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        for operation, expected in (("python", True), ("shell", False)):
            result = subprocess.run(
                [sys.executable, "-I", "-u", str(stage_root / "extension/python/bridge.py")],
                input=json.dumps({"operation": operation}) + "\n",
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=stage_root,
                timeout=30,
                env={
                    **os.environ,
                    "PYTHONPATH": "/nonexistent/thread-source-probe",
                    "PYTHONSTARTUP": "",
                },
            )
            envelope = json.loads(result.stdout)
            if envelope.get("ok") is not expected or (result.returncode == 0) is not expected:
                raise ValueError("Actual source package protocol failed: " + result.stderr)


def build(root, output):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        raise ValueError("Build the exact committed source; working tree must be clean.")
    scope, _ = policy(root)
    output.mkdir(parents=True, exist_ok=True)
    package = output / f"thread-agent-{scope['version']}-source.vsix"
    if package.exists():
        raise ValueError("Refusing to overwrite an existing reviewed source candidate.")
    subprocess.run(
        ["npm", "run", "compile", "--prefix", str(root / "extensions/vscode")], check=True
    )
    with tempfile.TemporaryDirectory(prefix="thread-source-build-") as folder:
        staging = Path(folder) / "extension"
        stage(root, staging, commit)
        subprocess.run(
            [
                shutil.which("node") or "node",
                str(root / "extensions/vscode/node_modules/@vscode/vsce/vsce"),
                "package",
                "--allow-missing-repository",
                "--out",
                str(package.resolve()),
            ],
            cwd=staging,
            check=True,
        )
    # Make repeated builds at the same source commit comparable without relying
    # on wall-clock ZIP timestamps or local filesystem permissions/order.
    import datetime

    epoch = int(
        subprocess.check_output(["git", "show", "-s", "--format=%ct", commit], cwd=root, text=True)
    )
    timestamp = datetime.datetime.fromtimestamp(epoch, datetime.UTC).timetuple()[:6]
    normalized = package.with_suffix(".normalized")
    with (
        zipfile.ZipFile(package) as archive,
        zipfile.ZipFile(
            normalized, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as target,
    ):
        for name, content in sorted(archive_entries(archive)):
            info = zipfile.ZipInfo(name, timestamp)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    normalized.replace(package)
    receipt = verify(root, package, commit)
    probe(root, package, commit)
    receipt["actual_source_protocol_checked"] = True
    package.with_suffix(".receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("build", "verify", "probe"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--commit")
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if args.operation == "build":
        if args.output is None:
            parser.error("build requires --output")
        print(json.dumps(build(args.root, args.output)), flush=True)
    else:
        if args.package is None or args.commit is None:
            parser.error("verify/probe requires --package and --commit")
        record = verify(args.root, args.package, args.commit, args.sha256)
        if args.operation == "probe":
            probe(args.root, args.package, args.commit)
        print(json.dumps(record), flush=True)
