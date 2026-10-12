"""Bind PyInstaller native inputs to actual payload bytes without asserting license coverage."""

import hashlib
from pathlib import Path, PurePosixPath


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def collected_binaries(analysis, payload):
    """Inventory both shared binaries and native Python extensions from a trusted build TOC.

    Source paths stay local; the returned record contains filenames/digests only.
    PyInstaller may rewrite a native image, so both source and payload hashes matter.
    Hash correspondence is provenance evidence, not a redistribution approval.
    """
    entries = []
    seen = {}
    for group in analysis:
        if not isinstance(group, list):
            continue
        for item in group:
            if (
                not isinstance(item, tuple)
                or len(item) != 3
                or item[2] not in {"BINARY", "EXTENSION"}
            ):
                continue
            name, source_name, kind = item
            if not isinstance(name, str) or not isinstance(source_name, str):
                raise ValueError("Native TOC paths must be strings.")
            # PyInstaller's Windows destination separators are normalized; drive
            # prefixes, empty components and traversal remain invalid on every host.
            relative = PurePosixPath(name.replace("\\", "/"))
            if (
                relative.is_absolute()
                or ":" in name
                or any(part in {"", ".", ".."} for part in name.replace("\\", "/").split("/"))
            ):
                raise ValueError("Unsafe native TOC destination.")
            source = Path(source_name).resolve(strict=True)
            if not source.is_file():
                raise ValueError("Native source must be a regular file.")
            if str(relative) in seen:
                if seen[str(relative)] != (source, kind):
                    raise ValueError("Conflicting native TOC destinations.")
                continue
            seen[str(relative)] = (source, kind)
            candidates = [
                payload.joinpath(*relative.parts),
                payload.joinpath("_internal", *relative.parts),
            ]
            present = [candidate for candidate in candidates if candidate.exists()]
            if len(present) != 1 or present[0].is_symlink() or not present[0].is_file():
                raise ValueError("Native payload destination missing, linked or ambiguous.")
            destination = present[0]
            if payload.resolve() not in destination.resolve().parents:
                raise ValueError("Native payload destination escaped through a parent link.")
            source_sha, payload_sha = digest(source), digest(destination)
            entries.append(
                {
                    "destination": destination.relative_to(payload).as_posix(),
                    "kind": kind,
                    "source_name": source.name,
                    "source_sha256": source_sha,
                    "payload_sha256": payload_sha,
                    "payload_bytes": destination.stat().st_size,
                    "source_bytes_identical": source_sha == payload_sha,
                }
            )
    return {
        "schema": 1,
        "entries": sorted(entries, key=lambda item: item["destination"]),
        "complete_distribution_review": False,
        "coverage": "PyInstaller BINARY and EXTENSION entries; bootloader/bytecode/data require separate inventory",
    }
