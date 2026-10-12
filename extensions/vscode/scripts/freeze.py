"""Build a native one-folder backend using an already installed PyInstaller.

This builds only the host target. It does not install tools, publish, download AI,
or establish platform support. Native runtime artifacts are generated files.
"""

import argparse
import ast
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path
from sysconfig import get_path

from native_notices import collect_static_notices

ROOT = Path(__file__).resolve().parents[3]
TARGETS = ("darwin-arm64", "darwin-x64", "linux-x64", "linux-arm64", "win32-x64", "win32-arm64")


def host_target():
    machine = platform.machine().lower()
    arch = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(machine)
    target = f"{sys.platform}-{arch}"
    if target not in TARGETS:
        raise ValueError(f"No native build target for {sys.platform}/{machine}.")
    return target


def materialize_links(directory):
    """VSIX scanners require regular files, not framework directory aliases.

    Only internal, non-cyclic aliases in this generated backend are copied.
    Native code bytes/signatures are unchanged; the extracted package is probed.
    """
    root = directory.resolve(strict=True)
    for _ in range(10000):
        link = next((item for item in root.rglob("*") if item.is_symlink()), None)
        if link is None:
            return
        target = link.resolve(strict=True)
        if root not in target.parents or (target.is_dir() and target in link.parents):
            raise ValueError("Native backend contains an external or cyclic link.")
        link.unlink()
        if target.is_dir():
            shutil.copytree(target, link, symlinks=True)
        elif target.is_file():
            shutil.copy2(target, link)
        else:
            raise ValueError("Native backend link is not a regular file/directory.")
        if sum(item.stat().st_size for item in root.rglob("*") if item.is_file()) > 512 * 1024**2:
            raise ValueError("Materialized backend exceeds 512 MiB.")
    raise ValueError("Native backend exceeds the alias expansion limit.")


def collect_notices(directory, work):
    """Retain native dependency notices found in the installed build distributions.

    This records available notice provenance; it does not select the project license
    or certify all target distributions. Missing notices stay explicit in the record.
    """
    output = directory / "notices"
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError("Generated notice output must be a regular directory.")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    record = {
        "python": sys.version.split()[0],
        "pyinstaller": version("PyInstaller"),
        "zstandard": version("zstandard"),
        "notices": [],
        "missing": [],
    }
    import zstandard

    zstd_version = ".".join(str(part) for part in zstandard.ZSTD_VERSION)
    zstd_notice = ROOT / "extensions/vscode/notices" / f"zstd-{zstd_version}-LICENSE"
    if zstd_notice.is_file():
        content = zstd_notice.read_bytes()
        name = zstd_notice.name
        (output / name).write_bytes(content)
        record["notices"].append(
            {
                "component": f"Zstandard native library {zstd_version}",
                "file": name,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    else:
        record["missing"].append(f"Zstandard native library {zstd_version}")
    sources = [("CPython", Path(get_path("stdlib")))]
    python_library = None
    analysis = ast.literal_eval((work / "work/thread-backend/Analysis-00.toc").read_text())
    for group in analysis:
        if isinstance(group, list):
            for item in group:
                if (
                    isinstance(item, tuple)
                    and len(item) == 3
                    and item[2] == "BINARY"
                    and Path(item[1]).is_file()
                ):
                    sources.append((Path(item[0]).name, Path(item[1]).resolve().parent))
                    name = Path(item[0]).name
                    if name.startswith("libpython") or re.match(r"python\d+\.dll$", name):
                        python_library = Path(item[1]).resolve()
    seen = set()
    for component, source in sources:
        found = []
        for parent in [source, *list(source.parents)[:6]]:
            found = [
                item
                for item in parent.iterdir()
                if item.is_file()
                and item.name.upper().startswith(("LICENSE", "COPYING", "COPYRIGHT"))
                and item.stat().st_size <= 1024 * 1024
            ]
            if found:
                break
        if not found:
            record["missing"].append(component)
        for item in found:
            content = item.read_bytes()
            sha = hashlib.sha256(content).hexdigest()
            if sha in seen:
                continue
            seen.add(sha)
            name = f"{len(seen):02d}-{item.name}"
            (output / name).write_bytes(content)
            record["notices"].append({"component": component, "file": name, "sha256": sha})
    package = distribution("PyInstaller")
    for item in package.files or []:
        if "licenses/" in str(item) and str(item).endswith(".txt"):
            source = package.locate_file(item)
            content = source.read_bytes()
            name = "PyInstaller-" + item.name
            (output / name).write_bytes(content)
            record["notices"].append(
                {
                    "component": "PyInstaller bootloader",
                    "file": name,
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    if python_library:
        profile = collect_static_notices(
            python_library,
            output,
            ROOT / "extensions/vscode/notices",
            host_target(),
            sys.version.split()[0],
        )
        if profile:
            record["static_profile"] = {
                key: value for key, value in profile.items() if key != "notices"
            }
            record["notices"].extend(profile["notices"])
            if any(item["component"] == "CPython" for item in profile["notices"]):
                record["missing"] = [
                    item for item in record["missing"] if item != python_library.name
                ]
        else:
            record["missing"].append("Distribution-specific static dependency notice profile")
    (output / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")
    if sys.platform == "darwin":
        minima = []
        hashes = set()
        for item in directory.rglob("*"):
            if not item.is_file() or not (
                item.suffix in {".so", ".dylib"}
                or item.name in {"Python", "Python3", "thread-backend"}
            ):
                continue
            sha = hashlib.sha256(item.read_bytes()).hexdigest()
            if sha in hashes:
                continue
            hashes.add(sha)
            result = subprocess.run(
                ["otool", "-l", str(item)], capture_output=True, text=True, check=True
            )
            for command in result.stdout.split("Load command"):
                if "LC_BUILD_VERSION" in command:
                    match = re.search(r"\bminos\s+(\d+(?:\.\d+){1,2})", command)
                elif "LC_VERSION_MIN_MACOSX" in command:
                    match = re.search(r"\bversion\s+(\d+(?:\.\d+){1,2})", command)
                else:
                    continue
                if match:
                    minima.append(tuple(int(part) for part in match[1].split(".")))
        record["minimum_macos"] = (
            ".".join(str(part) for part in max(minima)) if minima else "unknown"
        )
        record["build_macos"] = platform.mac_ver()[0]
        (output / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=TARGETS)
    args = parser.parse_args()
    if args.target != host_target():
        parser.error(
            "Build on the requested native OS/architecture; cross-compilation is not supported."
        )
    output = ROOT / "extensions/vscode/native" / args.target
    work = ROOT / "build/frozen-backend" / args.target
    work.mkdir(parents=True, exist_ok=True)
    metadata = []
    try:
        distribution("typing_extensions")
    except PackageNotFoundError:
        pass
    else:
        metadata = ["--copy-metadata", "typing_extensions"]
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--onedir",
            "--name",
            "thread-backend",
            "--paths",
            str(ROOT / "src"),
            "--copy-metadata",
            "pathspec",
            "--copy-metadata",
            "pypdf",
            "--copy-metadata",
            "zstandard",
            *metadata,
            "--distpath",
            str(output),
            "--workpath",
            str(work / "work"),
            "--specpath",
            str(work),
            str(Path(__file__).with_name("frozen_bridge.py")),
        ],
        cwd=ROOT,
        env={**os.environ, "PYINSTALLER_CONFIG_DIR": str(work / "cache")},
        check=True,
    )
    materialize_links(output / "thread-backend")
    collect_notices(output / "thread-backend", work)
    print(f"Built {args.target} backend; native validation and release signing remain required.")


if __name__ == "__main__":
    main()
