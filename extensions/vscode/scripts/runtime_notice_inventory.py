"""Read-only file/notice inventory; never a redistribution approval or binary execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path

MAX_FILES = 50_000
MAX_TOTAL_BYTES = 24 * 1024**3
MAX_FILE_BYTES = 8 * 1024**3
NOTICE_WORDS = ("license", "licence", "notice", "copyright", "copying", "authors")


def _regular_hash(path: Path, expected: os.stat_result) -> str:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        identity = (expected.st_dev, expected.st_ino, expected.st_size, expected.st_mtime_ns)
        if not stat.S_ISREG(before.st_mode) or identity != (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ):
            raise ValueError("Inventory file changed before reading")
        digest = hashlib.sha256()
        consumed = 0
        while block := os.read(descriptor, 1024 * 1024):
            consumed += len(block)
            if consumed > expected.st_size:
                raise ValueError("Inventory file grew while reading")
            digest.update(block)
        after = os.fstat(descriptor)
        if consumed != expected.st_size or identity != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValueError("Inventory file changed while reading")
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def inventory(folder: str | Path) -> dict:
    """Hash bounded regular files, marking notice-name candidates without interpreting terms.

    Supply a quiescent, caller-owned temporary directory. This is a diagnostic inventory,
    not a hostile-directory containment primitive or legal/completeness certificate.
    Absolute machine paths and file contents are excluded from the returned report.
    """
    root = Path(folder)
    root_stat = root.lstat()
    if (
        not stat.S_ISDIR(root_stat.st_mode)
        or root.is_symlink()
        or getattr(root_stat, "st_file_attributes", 0) & 0x400
    ):
        raise ValueError("Inventory root must be a regular directory")
    entries = []
    total = 0
    pending = [root]
    directories = 0
    while pending:
        directory = pending.pop()
        directories += 1
        if directories > MAX_FILES:
            raise ValueError("Inventory directory limit exceeded")
        for path in directory.iterdir():
            metadata = path.lstat()
            # Windows junctions/reparse points must not redirect traversal either.
            reparse = getattr(metadata, "st_file_attributes", 0) & 0x400
            if stat.S_ISLNK(metadata.st_mode) or reparse:
                raise ValueError("Inventory rejects links and reparse points")
            if stat.S_ISDIR(metadata.st_mode):
                if directories + len(pending) >= MAX_FILES:
                    raise ValueError("Inventory directory limit exceeded")
                pending.append(path)
                continue
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError("Inventory rejects special files and hard links")
            total += metadata.st_size
            if len(entries) >= MAX_FILES or metadata.st_size > MAX_FILE_BYTES:
                raise ValueError("Inventory file limit exceeded")
            if total > MAX_TOTAL_BYTES:
                raise ValueError("Inventory total byte limit exceeded")
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size": metadata.st_size,
                    "sha256": _regular_hash(path, metadata),
                    "notice_name_candidate": any(
                        word in path.name.lower() for word in NOTICE_WORDS
                    ),
                }
            )
    entries.sort(key=lambda entry: entry["path"])
    return {
        "schema_version": 1,
        "producer": "read-only file inventory; no binaries executed",
        "complete_legal_review": False,
        "limits": "Names/hashes establish file identity, not terms, dependency closure or approval.",
        "file_count": len(entries),
        "total_bytes": total,
        "files": entries,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(inventory(arguments.folder), indent=2))
