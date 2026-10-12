"""Install a pinned native Ollama runtime in extension-owned storage after UI consent."""

import hashlib
import json
import os
import platform
import re
import shutil
import signal
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from runtime_assets import ASSETS

VERSION = "0.34.4"
URL = f"https://github.com/ollama/ollama/releases/download/v{VERSION}/ollama-darwin.tgz"
SHA256 = "e9c8fddaab5f48f47f2c4ae3d23d0732f5182417125353faeed2188e34a22799"
SIZE = 160042307
MAX_EXPANDED = 2 * 1024**3


def target():
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "amd64": "x64"}.get(
        platform.machine().lower()
    )
    value = f"{sys.platform}-{arch}"
    if value not in ASSETS:
        raise ValueError("No pinned runtime for this OS/architecture.")
    return value


def unpack_zip(archive, destination):
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        if len(members) > 10000 or sum(item.file_size for item in members) > 8 * 1024**3:
            raise ValueError("Runtime archive exceeds extraction limits.")
        names = set()
        for member in members:
            name = member.filename.rstrip("/")
            relative = PurePosixPath(name)
            if (
                not name
                or relative.is_absolute()
                or "\\" in name
                or ":" in name
                or any(part in {"", ".", ".."} for part in name.split("/"))
                or any(part.endswith((".", " ")) for part in relative.parts)
                or any(
                    re.match(
                        r"^(con|prn|aux|nul|clock\$|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)", part, re.I
                    )
                    for part in relative.parts
                )
                or ((member.external_attr >> 16) & 0o170000) == 0o120000
                or name.casefold() in names
            ):
                raise ValueError("Unsafe runtime archive path or link.")
            names.add(name.casefold())
            output = destination.joinpath(*relative.parts)
            if member.is_dir():
                output.mkdir(parents=True, exist_ok=True)
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                with source.open(member) as content, output.open("xb") as stream:
                    shutil.copyfileobj(content, stream)


def unpack_zstd(archive, destination):
    try:
        import zstandard
    except ImportError as exc:
        raise ValueError("The native Linux backend must bundle the zstandard decoder.") from exc
    # Decode into bounded temporary storage, then use the existing safe tar extractor.
    decoded = destination.parent / "decoded.tar"
    expanded = 0
    with (
        archive.open("rb") as raw,
        zstandard.ZstdDecompressor().stream_reader(raw) as source,
        decoded.open("xb") as output,
    ):
        while chunk := source.read(1024 * 1024):
            expanded += len(chunk)
            if expanded > 8 * 1024**3:
                raise ValueError("Runtime decompression exceeds limit.")
            output.write(chunk)
    unpack(decoded, destination, limit=8 * 1024**3)


def unpack(archive, destination, limit=MAX_EXPANDED):
    """Extract regular files/directories only; materialize safe internal links as copies."""
    with tarfile.open(archive, "r:*") as source:
        names = set()
        links = []
        expanded = 0
        count = 0
        for member in source:
            count += 1
            expanded += member.size
            if count > 10000 or expanded > limit:
                raise ValueError("Runtime archive exceeds extraction limits.")
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts or "\\" in member.name:
                raise ValueError("Unsafe runtime archive path.")
            if str(relative) == "." and member.isdir():
                continue
            if str(relative) in names:
                raise ValueError("Duplicate runtime archive path.")
            names.add(str(relative))
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as content, target.open("xb") as output:
                    shutil.copyfileobj(content, output)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
            elif member.issym() or member.islnk():
                links.append((member, target))
            else:
                raise ValueError("Unsupported runtime archive entry.")
        # Only materialize declared internal file links. Revisit unresolved targets
        # after their own links have been copied; never create filesystem links.
        pending = links
        for _ in range(64):
            if not pending:
                break
            deferred = []
            for member, target in pending:
                link = PurePosixPath(member.linkname)
                if link.is_absolute() or "\\" in member.linkname:
                    raise ValueError("Unsafe runtime archive link.")
                base = target.parent if member.issym() else destination
                resolved = (base / member.linkname).resolve()
                if destination.resolve() not in resolved.parents:
                    raise ValueError("Runtime link must reference an extracted internal file.")
                if not resolved.is_file():
                    deferred.append((member, target))
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise ValueError("Duplicate runtime archive link.")
                expanded += resolved.stat().st_size
                if expanded > limit:
                    raise ValueError("Runtime link copies exceed extraction limits.")
                shutil.copy2(resolved, target)
            if len(deferred) == len(pending):
                raise ValueError("Runtime link must reference an extracted internal file.")
            pending = deferred
        if pending:
            raise ValueError("Runtime link chain exceeds the bounded resolution limit.")


def install(root):
    root = Path(root)
    if not root.is_absolute() or root.is_symlink():
        raise ValueError("Expected an absolute extension storage directory.")
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "install.lock"
    try:
        profile = target()
        asset_name, size, sha256, executable = ASSETS[profile]
        # Preserve existing macOS fixture constants and pinned public behavior.
        url = f"https://github.com/ollama/ollama/releases/download/v{VERSION}/{asset_name}"
        if profile.startswith("darwin-"):
            size, sha256, url = SIZE, SHA256, URL
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("Another runtime install is active. Finish it before retrying.") from exc
    try:
        final = root / f"ollama-{VERSION}"
        marker = final / "installed.json"
        if marker.is_file():
            if marker.is_symlink() or marker.stat().st_size > 4096:
                raise ValueError(
                    "Invalid installed runtime marker; do not overwrite existing files."
                )
            installed = json.loads(marker.read_text())
            if not isinstance(installed, dict):
                raise ValueError("Invalid installed runtime marker object.")
            binary = final / executable
            if (
                installed.get("version") != VERSION
                or installed.get("sha256") != sha256
                or installed.get("target", profile if profile.startswith("darwin-") else "")
                != profile
                or binary.is_symlink()
                or not binary.is_file()
            ):
                raise ValueError(
                    "Installed runtime identity or executable is invalid; inspect existing storage."
                )
            return
        if final.exists():
            raise ValueError("Incomplete runtime directory; do not overwrite existing files.")
        if asset_name.endswith(".zst"):
            try:
                import zstandard  # noqa: F401 - fail before any large download if decoder is absent
            except ImportError as exc:
                raise ValueError(
                    "This backend lacks its bundled Linux Zstandard decoder; no runtime was downloaded."
                ) from exc
        with tempfile.TemporaryDirectory(prefix="download-", dir=root) as temporary:
            temporary = Path(temporary)
            archive = temporary / asset_name
            digest = hashlib.sha256()
            received = 0
            request = urllib.request.Request(url, headers={"User-Agent": "Thread-Agent-Setup"})
            # A browser-style HTTPS download, never a remotely supplied shell script.
            with (
                urllib.request.urlopen(request, timeout=30) as response,
                archive.open("xb") as output,
            ):
                if not response.url.startswith("https://"):
                    raise ValueError("Runtime download must stay on HTTPS.")
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > size:
                        raise ValueError("Runtime download exceeded its pinned size.")
                    digest.update(chunk)
                    output.write(chunk)
                    print(
                        f"Runtime download: {received * 100 // size}%", file=sys.stderr, flush=True
                    )
            if received != size or digest.hexdigest() != sha256:
                raise ValueError("Runtime checksum/size mismatch; nothing was installed.")
            extracted = temporary / "extracted"
            extracted.mkdir()
            if asset_name.endswith(".zip"):
                unpack_zip(archive, extracted)
            elif asset_name.endswith(".zst"):
                unpack_zstd(archive, extracted)
            else:
                unpack(archive, extracted)
            if not (extracted / executable).is_file():
                raise ValueError("Official runtime archive has an unexpected layout.")
            (extracted / "installed.json").write_text(
                json.dumps({"version": VERSION, "sha256": sha256, "target": profile})
            )
            os.rename(extracted, final)
    finally:
        lock.rmdir()


if __name__ == "__main__":

    def interrupted(signum, frame):
        raise SystemExit(130)

    signal.signal(signal.SIGTERM, interrupted)
    try:
        install(sys.argv[1])
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
