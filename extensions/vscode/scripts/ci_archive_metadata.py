"""Read exact approved archive manifests/notices on hosted CI; never extract or execute."""

import argparse
import hashlib
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from ci_runtime_integration import preflight, require_runner, write_report
from runtime_assets import ASSETS

NOTICE_WORDS = ("license", "licence", "notice", "copying")


def inspect(work, target):
    require_runner(target)
    preflight(work, target)
    name, size, sha, _ = ASSETS[target]
    archive = work / name
    digest = hashlib.sha256()
    count = 0
    try:
        with (
            urllib.request.urlopen(
                f"https://github.com/ollama/ollama/releases/download/v0.34.4/{name}", timeout=60
            ) as source,
            archive.open("xb") as output,
        ):
            while block := source.read(1024 * 1024):
                count += len(block)
                if count > size:
                    raise ValueError("Archive exceeds approved size")
                digest.update(block)
                output.write(block)
        if count != size or digest.hexdigest() != sha:
            raise ValueError("Archive identity changed")
        entries = []
        notices = []
        if target == "win32-x64":
            with zipfile.ZipFile(archive) as source:
                members = source.infolist()
                if len(members) > 10000 or sum(x.file_size for x in members) > 8 * 1024**3:
                    raise ValueError("Archive metadata bounds")
                for item in members:
                    entries.append({"path": item.filename, "size": item.file_size})
                    if any(word in item.filename.lower() for word in NOTICE_WORDS):
                        if item.file_size > 256 * 1024:
                            raise ValueError("Notice exceeds inspection bound")
                        data = source.read(item)
                        notices.append(
                            {
                                "path": item.filename,
                                "sha256": hashlib.sha256(data).hexdigest(),
                                "text": data.decode("utf-8", errors="replace"),
                            }
                        )
        else:
            import zstandard

            with (
                archive.open("rb") as raw,
                zstandard.ZstdDecompressor().stream_reader(raw) as stream,
            ):
                with tarfile.open(fileobj=stream, mode="r|") as source:
                    expanded = 0
                    for item in source:
                        expanded += item.size
                        if len(entries) >= 10000 or expanded > 8 * 1024**3:
                            raise ValueError("Archive metadata bounds")
                        entries.append(
                            {
                                "path": item.name,
                                "size": item.size,
                                "type": item.type.decode("ascii"),
                                "link": item.linkname,
                            }
                        )
                        if item.isfile() and any(
                            word in item.name.lower() for word in NOTICE_WORDS
                        ):
                            if item.size > 256 * 1024:
                                raise ValueError("Notice exceeds inspection bound")
                            data = source.extractfile(item).read(256 * 1024 + 1)
                            notices.append(
                                {
                                    "path": item.name,
                                    "sha256": hashlib.sha256(data).hexdigest(),
                                    "text": data.decode("utf-8", errors="replace"),
                                }
                            )
        write_report(
            work,
            "archive-metadata.json",
            {
                "target": target,
                "archive_sha256": sha,
                "entries": entries,
                "notices": notices,
                "extracted": False,
                "executed": False,
                "model_downloaded": False,
            },
        )
    finally:
        archive.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    inspect(args.work, args.target)
