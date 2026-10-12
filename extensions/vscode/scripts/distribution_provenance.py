"""Collect bounded installed-distribution evidence; never accept terms or fetch images."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MAX_TEXT = 1024 * 1024
MAX_TOTAL_TEXT = 8 * MAX_TEXT


def command(arguments):
    result = subprocess.run(
        arguments,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def retain_text(path, output, texts, origin):
    """Retain original bounded text, not executable names or rewritten terms."""
    if not path.is_file() or path.stat().st_size > MAX_TEXT:
        return None
    content = path.read_bytes()
    if not content or b"\0" in content or content.startswith((b"MZ", b"\x7fELF")):
        return None
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    digest = hashlib.sha256(content).hexdigest()
    if digest not in texts:
        if sum(row["bytes"] for row in texts.values()) + len(content) > MAX_TOTAL_TEXT:
            raise ValueError("Distribution notice text limit exceeded.")
        name = "distribution-" + digest + ".txt"
        (output / name).write_bytes(content)
        texts[digest] = {
            "file": name,
            "sha256": digest,
            "bytes": len(content),
            "origin": origin,
            "text": content.decode("utf-8"),
        }
    return texts[digest]


def linux_evidence(source, output, texts):
    ownership = ""
    for candidate in dict.fromkeys([str(source), str(source).replace("/usr/lib/", "/lib/", 1)]):
        ownership = command(["dpkg-query", "-S", candidate])
        if ownership:
            break
    owners = sorted(
        {
            line.rsplit(": ", 1)[0]
            for line in ownership.splitlines()
            if ": " in line and not line.startswith("diversion ")
        }
    )
    packages = []
    for owner in owners:
        if not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9]+)?", owner):
            continue
        metadata = command(
            [
                "dpkg-query",
                "-W",
                "-f=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}",
                owner,
            ]
        )
        if not metadata:
            continue
        package, version, source_package, source_version = metadata.split("\t")
        document = Path("/usr/share/doc") / owner.split(":")[0] / "copyright"
        notice = retain_text(document, output, texts, "Ubuntu installed package " + package)
        references = []
        if notice:
            for name in sorted(
                set(re.findall(r"/usr/share/common-licenses/([A-Za-z0-9.+-]+)", notice["text"]))
            ):
                common = retain_text(
                    Path("/usr/share/common-licenses") / name.rstrip("."),
                    output,
                    texts,
                    "Ubuntu common license " + name,
                )
                if common:
                    references.append(common["sha256"])
        packages.append(
            {
                "package": package,
                "version": version,
                "source_package": source_package,
                "source_version": source_version,
                "source_access": "https://launchpad.net/ubuntu/+source/"
                + source_package
                + "/"
                + source_version,
                "copyright_sha256": notice["sha256"] if notice else None,
                "referenced_license_sha256": references,
            }
        )
    return {
        "origin": "Ubuntu dpkg ownership" if packages else "unresolved installed origin",
        "packages": packages,
        "terms_reviewed": False,
    }


def windows_sdk_evidence(source, target, output, texts):
    """Only installed SDK redist candidates; System32 is never a redistribution grant."""
    kits = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Windows Kits/10"
    arch = "arm64" if target.endswith("arm64") else "x64"
    matches = []
    candidates = []
    for path in sorted((kits / "Redist").glob("*/ucrt/DLLs/" + arch + "/" + source.name)):
        if path.is_file():
            digest = sha(path)
            record = {"sdk_relative_path": path.relative_to(kits).as_posix(), "sha256": digest}
            candidates.append(record)
            if digest == sha(source):
                matches.append(record)
    licenses = []
    for path in sorted(
        list((kits / "Licenses").rglob("*.txt")) + list((kits / "Licenses").rglob("*.rtf"))
    )[:32]:
        notice = retain_text(
            path, output, texts, "Installed Windows SDK " + path.relative_to(kits).as_posix()
        )
        if notice:
            licenses.append(notice["sha256"])
    return {
        "origin": "installed Windows SDK redist exact match"
        if matches
        else "unresolved Windows redistribution origin",
        "sdk_redist_candidates": candidates,
        "exact_sdk_matches": matches,
        "sdk_license_candidates": licenses,
        "new_sdk_acquired": False,
        "new_terms_accepted": False,
        "terms_reviewed": False,
    }


def windows_file_version(path):
    """Read PE version resources using the installed OS API; never load the image."""
    import ctypes
    from ctypes import wintypes

    api = ctypes.WinDLL("version", use_last_error=True)
    api.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
    api.GetFileVersionInfoSizeW.restype = wintypes.DWORD
    size = api.GetFileVersionInfoSizeW(str(path), None)
    if not size or size > MAX_TEXT:
        return None
    api.GetFileVersionInfoW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    api.GetFileVersionInfoW.restype = wintypes.BOOL
    buffer = ctypes.create_string_buffer(size)
    if not api.GetFileVersionInfoW(str(path), 0, size, buffer):
        return None
    api.VerQueryValueW.argtypes = [
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.UINT),
    ]
    api.VerQueryValueW.restype = wintypes.BOOL
    pointer, length = ctypes.c_void_p(), wintypes.UINT()
    if (
        not api.VerQueryValueW(buffer, "\\", ctypes.byref(pointer), ctypes.byref(length))
        or length.value < 52
    ):
        return None
    words = ctypes.cast(pointer, ctypes.POINTER(wintypes.DWORD))
    if words[0] != 0xFEEF04BD:
        return None
    return ".".join(
        str(part) for part in [words[2] >> 16, words[2] & 0xFFFF, words[3] >> 16, words[3] & 0xFFFF]
    )


def collect_distribution_provenance(analysis, inventory, output, target):
    sources = {}
    for group in analysis:
        if isinstance(group, list):
            for item in group:
                if (
                    isinstance(item, tuple)
                    and len(item) == 3
                    and item[2] in {"BINARY", "EXTENSION"}
                ):
                    sources[item[0].replace("\\", "/")] = Path(item[1]).resolve(strict=True)
    texts, images = {}, []
    base = Path(sys.base_prefix).resolve()
    for row in inventory["entries"]:
        name = row["destination"].removeprefix("_internal/")
        source = sources.get(name)
        if source is None or sha(source) != row["source_sha256"]:
            raise ValueError("Provenance source does not match native inventory.")
        if target.startswith("linux"):
            evidence = linux_evidence(source, output, texts)
        elif target.startswith("win32") and source.name.lower().startswith(("api-ms-", "ucrtbase")):
            evidence = windows_sdk_evidence(source, target, output, texts)
        else:
            evidence = {
                "origin": "Python distribution"
                if base == source or base in source.parents
                else "unresolved installed origin",
                "terms_reviewed": False,
            }
        if base in source.parents:
            evidence["python_relative_path"] = source.relative_to(base).as_posix()
        if sys.platform == "win32":
            evidence["file_version"] = windows_file_version(source)
        images.append({**row, "distribution": evidence})
    # Python installation texts, including the Windows combined dependency license.
    for parent in [base, base / "Resources/English.lproj", base / "lib/python3.12"]:
        for pattern in ("LICENSE*", "License*", "COPYING*", "build-info*.json", "PYTHON.json"):
            for path in sorted(parent.glob(pattern))[:32]:
                retain_text(
                    path, output, texts, "Python distribution " + path.relative_to(base).as_posix()
                )
    snapshots = Path(__file__).resolve().parents[1] / "notices/cpython-incorporated"
    snapshot_sources = json.loads((snapshots / "sources.json").read_text(encoding="utf-8"))
    for item in snapshot_sources["sources"]:
        if item["python"] == sys.version.split()[0]:
            notice = snapshots / item["file"]
            if notice.is_symlink() or sha(notice) != item["sha256"]:
                raise ValueError("Official incorporated notice snapshot changed.")
            retain_text(notice, output, texts, item["source"])
    report = {
        "schema": 1,
        "target": target,
        "python": sys.version.split()[0],
        "images": images,
        "texts": list(texts.values()),
        "python_config_args": str(__import__("sysconfig").get_config_var("CONFIG_ARGS")).replace(
            str(base), "<python-distribution>"
        ),
        "openssl_runtime_version": __import__("ssl").OPENSSL_VERSION,
        "expat_runtime_version": __import__("pyexpat").EXPAT_VERSION,
        "sqlite_runtime_version": __import__("sqlite3").sqlite_version,
        "zlib_runtime_version": __import__("zlib").ZLIB_RUNTIME_VERSION,
        "complete_distribution_review": False,
        "limits": "Installed ownership and retained texts require component-specific redistribution review; absent static build metadata stays unresolved.",
    }
    (output / "distribution-provenance.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report
