"""Install a pinned Ollama macOS runtime in extension-owned storage after UI consent."""

import hashlib
import json
import os
import shutil
import signal
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

VERSION = "0.34.4"
URL = f"https://github.com/ollama/ollama/releases/download/v{VERSION}/ollama-darwin.tgz"
SHA256 = "e9c8fddaab5f48f47f2c4ae3d23d0732f5182417125353faeed2188e34a22799"
SIZE = 160042307
MAX_EXPANDED = 2 * 1024**3


def unpack(archive, destination):
    """Extract regular files/directories only; materialize safe internal links as copies."""
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if len(members) > 10000 or sum(m.size for m in members) > MAX_EXPANDED:
            raise ValueError("Runtime archive exceeds extraction limits.")
        names = set()
        links = []
        for member in members:
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
        for member, target in links:
            link = PurePosixPath(member.linkname)
            if link.is_absolute() or "\\" in member.linkname:
                raise ValueError("Unsafe runtime archive link.")
            base = target.parent if member.issym() else destination
            resolved = (base / member.linkname).resolve()
            if destination.resolve() not in resolved.parents or not resolved.is_file():
                raise ValueError("Runtime link must reference an extracted internal file.")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise ValueError("Duplicate runtime archive link.")
            shutil.copy2(resolved, target)


def install(root):
    root = Path(root)
    if not root.is_absolute() or root.is_symlink():
        raise ValueError("Expected an absolute extension storage directory.")
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "install.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("Another runtime install is active. Finish it before retrying.") from exc
    try:
        final = root / f"ollama-{VERSION}"
        if (final / "installed.json").is_file():
            return
        if final.exists():
            raise ValueError("Incomplete runtime directory; do not overwrite existing files.")
        with tempfile.TemporaryDirectory(prefix="download-", dir=root) as temporary:
            temporary = Path(temporary)
            archive = temporary / "runtime.tgz"
            digest = hashlib.sha256()
            received = 0
            request = urllib.request.Request(URL, headers={"User-Agent": "Thread-Agent-Setup"})
            # A browser-style HTTPS download, never a remotely supplied shell script.
            with (
                urllib.request.urlopen(request, timeout=30) as response,
                archive.open("xb") as output,
            ):
                if not response.url.startswith("https://"):
                    raise ValueError("Runtime download must stay on HTTPS.")
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > SIZE:
                        raise ValueError("Runtime download exceeded its pinned size.")
                    digest.update(chunk)
                    output.write(chunk)
                    print(
                        f"Runtime download: {received * 100 // SIZE}%", file=sys.stderr, flush=True
                    )
            if received != SIZE or digest.hexdigest() != SHA256:
                raise ValueError("Runtime checksum/size mismatch; nothing was installed.")
            extracted = temporary / "extracted"
            extracted.mkdir()
            unpack(archive, extracted)
            if not (extracted / "ollama").is_file():
                raise ValueError("Official runtime archive has an unexpected layout.")
            (extracted / "installed.json").write_text(
                json.dumps({"version": VERSION, "sha256": SHA256})
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
