"""Bind PyInstaller native inputs to actual payload bytes without asserting license coverage."""

import hashlib
from pathlib import Path, PurePosixPath


def native_build_environment(target, environment, python_base, executable):
    """Keep Windows binary discovery independent of ambient JDK/Git DLL copies."""
    result = dict(environment)
    if target.startswith("win32-"):
        windows = Path(environment["SystemRoot"])
        paths = [
            Path(executable).parent,
            python_base,
            python_base / "DLLs",
            windows / "System32",
            windows,
        ]
        result["PATH"] = ";".join(dict.fromkeys(str(path) for path in paths))
    return result


def omit_windows_os_images(analysis, payload, windows_root):
    """Omit OS API-set/UCRT copies; supported Windows 10+ supplies these centrally.

    Only matching BINARY entries originating inside Windows system directories are
    eligible. Validate the entire existing TOC/payload before deleting owned output.
    Preserve original hashes for audit; caller must probe the resulting package.
    """
    import re

    before = collected_binaries(analysis, payload)
    by_destination = {
        row["destination"].removeprefix("_internal/"): row for row in before["entries"]
    }
    omitted = []
    filtered = []
    root = windows_root.resolve(strict=True)
    for group in analysis:
        if not isinstance(group, list):
            filtered.append(group)
            continue
        remaining = []
        for item in group:
            eligible = False
            if isinstance(item, tuple) and len(item) == 3 and item[2] == "BINARY":
                source = Path(item[1]).resolve(strict=True)
                family = (
                    re.fullmatch(r"(?:api-ms-win-[a-z0-9-]+|ucrtbase)\.dll", source.name.lower())
                    is not None
                )
                if root in source.parents:
                    relative = source.relative_to(root)
                    system_directory = relative.parts[0].lower() in {"system32", "syswow64"}
                    component_store = (
                        len(relative.parts) == 3
                        and relative.parts[0].lower() == "winsxs"
                        and re.fullmatch(
                            r"(?:amd64|arm64|wow64)_microsoft-windows-[a-z0-9.-]+_31bf3856ad364e35_[a-z0-9._-]+",
                            relative.parts[1].lower(),
                        )
                        is not None
                    )
                    eligible = family and (system_directory or component_store)
                if not eligible and family:
                    # Build search paths can resolve a copied OS image outside
                    # SystemRoot. Only an exact match to the installed OS image
                    # supplies equivalent evidence; names/versions alone do not.
                    for parent in [
                        root / "System32",
                        root / "System32/downlevel",
                        root / "SysWOW64",
                        root / "SysWOW64/downlevel",
                    ]:
                        candidate = parent / source.name
                        if (
                            candidate.is_file()
                            and root in candidate.resolve().parents
                            and digest(candidate) == digest(source)
                        ):
                            eligible = True
                            relative = candidate.resolve().relative_to(root)
                            break
            if eligible:
                row = by_destination[item[0].replace("\\", "/")]
                omitted.append(
                    {
                        **row,
                        "windows_relative_path": relative.as_posix(),
                        "reason": "OS component supplied by Windows 10+; no system image redistribution",
                    }
                )
            else:
                remaining.append(item)
        filtered.append(remaining)
    for row in {item["destination"]: item for item in omitted}.values():
        payload.joinpath(*PurePosixPath(row["destination"]).parts).unlink()
    return filtered, omitted


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
