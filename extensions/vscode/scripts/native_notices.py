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
