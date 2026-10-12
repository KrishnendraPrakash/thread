"""Retain reviewed static notices only for an exact source-library profile.

An identified notice snapshot does not certify every distribution term, signing,
compatibility or unrelated Python builds. Unknown libraries stay unreviewed.
"""

import hashlib
import json
import shutil
from pathlib import Path


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def collect_static_notices(source, output, profiles, target, python_version):
    source_hash = digest(source)
    matches = []
    for path in profiles.glob("*/profile.json"):
        profile = json.loads(path.read_text())
        if (
            profile.get("schema") == 1
            and profile.get("target") == target
            and profile.get("python") == python_version
            and profile.get("source_library_sha256") == source_hash
        ):
            matches.append((path, profile))
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError("Ambiguous static dependency notice profile.")
    path, profile = matches[0]
    notices = []
    for item in profile["components"]:
        name = item["file"]
        if Path(name).name != name or "\\" in name:
            raise ValueError("Static notice filenames must be basenames.")
        notice = path.parent / name
        if notice.is_symlink() or not notice.is_file() or digest(notice) != item["sha256"]:
            raise ValueError("Reviewed static dependency notice missing or changed.")
        name = "static-" + name
        shutil.copy2(notice, output / name)
        notices.append({**item, "file": name})
    result = {
        "profile": path.parent.name,
        "source_library_sha256": source_hash,
        "source_archive_sha256": profile["source_archive_sha256"],
        "distribution_source_commit": profile["distribution_source_commit"],
        "complete_distribution_review": False,
        "notices": notices,
    }
    (output / "static-profile.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def notice_text_candidate(path):
    """Accept bounded UTF-8 notice text, never DLL/EXE images named License*."""
    if path.suffix.lower() in {".dll", ".exe", ".so", ".dylib", ".pyd"}:
        return False
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 1024 * 1024:
        return False
    if not path.name.upper().startswith(("LICENSE", "COPYING", "COPYRIGHT")):
        return False
    content = path.read_bytes()
    if not content or b"\0" in content or content.startswith((b"MZ", b"\x7fELF")):
        return False
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def collect_bound_notices(inventory, output, folder, target, python_version):
    """Bind retained terms to recorded exact source hashes; no dependency closure claim."""
    profile = json.loads((folder / "bindings.json").read_text(encoding="utf-8"))
    if profile.get("schema") != 1:
        raise ValueError("Unsupported exact-image notice bindings.")
    notices = []
    for entry in inventory["entries"]:
        matches = [
            binding
            for binding in profile["bindings"]
            if binding["target"] == target
            and binding["python"] == python_version
            and binding["source_name"] == entry["source_name"]
            and binding["source_sha256"] == entry["source_sha256"]
        ]
        if len(matches) > 1:
            raise ValueError("Ambiguous exact-image notice binding.")
        if not matches:
            continue
        binding = matches[0]
        documents = binding.get(
            "notices",
            [
                {
                    "file": binding.get("notice_file"),
                    "sha256": binding.get("notice_sha256"),
                    "source": binding.get("source"),
                }
            ],
        )
        for document in documents:
            name = document["file"]
            if not isinstance(name, str) or Path(name).name != name or "\\" in name:
                raise ValueError("Bound notice filenames must be basenames.")
            notice = folder / name
            if notice.is_symlink() or not notice.is_file() or digest(notice) != document["sha256"]:
                raise ValueError("Bound notice missing or changed.")
            destination = profile.get("prefix", "CPython-core-") + name
            shutil.copy2(notice, output / destination)
            notices.append(
                {
                    **binding,
                    "component": binding.get("component", "CPython core"),
                    "file": destination,
                    "sha256": document["sha256"],
                    "source": document["source"],
                    "payload_sha256": entry["payload_sha256"],
                    "payload_destination": entry["destination"],
                    "scope": profile["scope"],
                    "complete_distribution_review": False,
                }
            )
    if notices and (folder / "PACKAGING-CHANGES.txt").is_file():
        changes = folder / "PACKAGING-CHANGES.txt"
        shutil.copy2(changes, output / "CPython-PACKAGING-CHANGES.txt")
    return notices


collect_cpython_core_notices = collect_bound_notices
