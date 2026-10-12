"""Read-only gates for an exact six-target Marketplace/offline release inventory.

This preparation does not package, authenticate, download or publish anything.
"""

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

TARGETS = {"darwin-arm64", "darwin-x64", "linux-x64", "linux-arm64", "win32-x64", "win32-arm64"}
GATES = {
    "project_license",
    "complete_third_party_notices",
    "all_target_editor_and_inference_checks",
    "windows_editor_activation",
    "clean_machine_setup",
    "signing_decision_and_validation",
    "offline_companion_distribution_review",
}

BYO_SCOPE = {
    "version": "0.2.1",
    "models": "user-supplied",
    "artifacts": "native-vsix",
    "official_companions": False,
}


def checked_file(root: Path, record: dict) -> Path:
    name = record.get("file", "")
    if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name:
        raise ValueError("Inventory filenames must be plain basenames.")
    path = root / name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing regular artifact: {name}")
    if path.stat().st_size != record.get("bytes"):
        raise ValueError(f"Artifact size differs: {name}")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != record.get("sha256"):
        raise ValueError(f"Artifact digest differs: {name}")
    return path


def verify_packaged_license(archive, license_text):
    names = [
        name
        for name in archive.namelist()
        if name in {"extension/LICENSE", "extension/LICENSE.txt"}
    ]
    if len(names) != 1 or archive.read(names[0]) != license_text:
        raise ValueError("Packaged project license mismatch or ambiguous license files.")


def readiness(root: Path) -> dict:
    policy = json.loads((root / "release/marketplace-policy.json").read_text())
    manifest = json.loads((root / "extensions/vscode/package.json").read_text())
    if (
        policy.get("schema") != 1
        or policy.get("publisher") != "Krishnendra"
        or policy.get("extension") != "thread-agent"
        or policy.get("environment") != "marketplace-publish"
        or len(policy.get("targets", [])) != len(TARGETS)
        or set(policy.get("targets", [])) != TARGETS
    ):
        raise ValueError("Unexpected release policy identity/targets.")
    if set(policy.get("gates", {})) != GATES:
        raise ValueError("Required release gates must not be removed.")
    if policy.get("distribution_scope") != BYO_SCOPE or manifest.get("version") != "0.2.1":
        raise ValueError("Owner-approved BYO 0.2.1 distribution scope is required.")
    if policy["gates"]["offline_companion_distribution_review"] != "not_applicable":
        raise ValueError("Official-companion gate must match the exact BYO scope.")
    pending = [
        name
        for name, value in policy["gates"].items()
        if name != "offline_companion_distribution_review" and value != "passed"
    ]
    if pending:
        raise ValueError("Release gates pending: " + ", ".join(sorted(pending)))
    if (
        manifest.get("publisher") != policy["publisher"]
        or manifest.get("name") != policy["extension"]
    ):
        raise ValueError("Manifest identity differs from approved publisher.")
    if manifest.get("license") in (None, "", "UNLICENSED") or not (root / "LICENSE").is_file():
        raise ValueError("Owner-selected project license is required.")
    if manifest.get("threadModelProvisioning") != "user-supplied":
        raise ValueError("Packaged model provisioning must be user-supplied.")
    if manifest.get("preview") is not True:
        raise ValueError("Prepared automation supports the preview channel only.")
    source = (root / "extensions/vscode/src/extension.ts").read_text()
    if "if (process.platform === 'win32')" in source:
        raise ValueError("Windows editor activation remains gated; six-target publication blocked.")
    return manifest


def inventory(root: Path, folder: Path, commit: str, version: str) -> dict:
    manifest = readiness(root)
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or version != manifest["version"]:
        raise ValueError("Exact source commit and matching version are required.")
    record = json.loads((folder / "release.json").read_text())
    if (
        record.get("schema") != 1
        or record.get("commit") != commit
        or record.get("version") != version
        or record.get("channel") != "pre-release"
        or record.get("publisher") != manifest["publisher"]
        or record.get("distribution_scope") != BYO_SCOPE
    ):
        raise ValueError("Release inventory identity/commit/channel mismatch.")
    targets = record.get("targets", [])
    if len(targets) != 6 or {item.get("target") for item in targets} != TARGETS:
        raise ValueError("Exactly one entry per required target is required.")
    if any(
        p.suffix.lower() in {".zip", ".gguf", ".safetensors"} or p.name.startswith("sha256-")
        for p in folder.iterdir()
        if p.is_file()
    ):
        raise ValueError("Official companions/model assets are outside this release scope.")
    for item in targets:
        target = item["target"]
        if "companion" in item or item.get("distribution_scope") != BYO_SCOPE:
            raise ValueError("Candidate must match model-free BYO distribution scope.")
        for check in ("native_package", "security", "editor", "clean_machine", "offline_inference"):
            evidence = item.get("checks", {}).get(check, {})
            if (
                evidence.get("result") != "passed"
                or evidence.get("commit") != commit
                or not isinstance(evidence.get("url"), str)
                or not evidence["url"].startswith("https://")
            ):
                raise ValueError(f"Missing same-commit {check} evidence for {target}")
        package = checked_file(folder, item["vsix"])
        if package.suffix != ".vsix":
            raise ValueError("Expected a VSIX file.")
        verify_byo_vsix(root, manifest, package, target)
    return record


def verify_byo_vsix(root, manifest, package, target):
    """Inspect model-free package contents; never advance product/release gates."""
    ns = {"v": "http://schemas.microsoft.com/developer/vsx-schema/2011"}
    with zipfile.ZipFile(package) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("Duplicate VSIX archive entries are ambiguous.")
        if any(
            name.lower().startswith("extension/models/")
            or name.lower().endswith((".gguf", ".safetensors"))
            or "/models/blobs/sha256-" in name.lower()
            for name in archive.namelist()
        ):
            raise ValueError("Model weights must not be bundled in a BYO VSIX.")
        packaged = json.loads(archive.read("extension/package.json"))
        for key in (
            "name",
            "publisher",
            "version",
            "license",
            "preview",
            "threadModelProvisioning",
        ):
            if packaged.get(key) != manifest.get(key):
                raise ValueError(f"Packaged {key} mismatch for {target}")
        xml = ElementTree.fromstring(archive.read("extension.vsixmanifest"))
        identity = xml.find("v:Metadata/v:Identity", ns)
        if identity is None or identity.get("TargetPlatform") != target:
            raise ValueError("Native VSIX target mismatch.")
        if any(
            identity.get(attribute) != manifest[key]
            for attribute, key in (
                ("Id", "name"),
                ("Publisher", "publisher"),
                ("Version", "version"),
            )
        ):
            raise ValueError("VSIX XML identity differs from the approved manifest.")
        properties = {
            p.get("Id"): p.get("Value")
            for p in xml.findall("v:Metadata/v:Properties/v:Property", ns)
        }
        if properties.get("Microsoft.VisualStudio.Code.PreRelease") != "true":
            raise ValueError("Expected a pre-release VSIX.")
        executable = "thread-backend.exe" if target.startswith("win32-") else "thread-backend"
        if f"extension/native/{target}/thread-backend/{executable}" not in archive.namelist():
            raise ValueError("Matching bundled native backend missing.")
        verify_packaged_license(archive, (root / "LICENSE").read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--commit")
    parser.add_argument("--version")
    args = parser.parse_args()
    try:
        if args.artifacts:
            if not args.commit or not args.version:
                raise ValueError("Artifact verification requires --commit and --version.")
            inventory(args.root, args.artifacts, args.commit, args.version)
        else:
            readiness(args.root)
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
        ElementTree.ParseError,
    ) as exc:
        print(f"Release blocked: {exc}")
        return 1
    print("Local release gates passed; publisher authorization and approvals remain separate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
