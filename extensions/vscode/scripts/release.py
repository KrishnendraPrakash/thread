"""Package a public preview only after explicit publisher and license configuration."""

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[3]
EXTENSION = ROOT / "extensions/vscode"
TARGETS = ("darwin-arm64", "darwin-x64", "linux-x64", "linux-arm64")


def configuration(root: Path, publisher: str) -> dict:
    manifest = json.loads((root / "extensions/vscode/package.json").read_text())
    if not publisher or publisher != manifest.get("publisher"):
        raise ValueError(
            "Pass --publisher with your exact Marketplace publisher ID; it must match package.json."
        )
    if manifest.get("license") in {None, "", "UNLICENSED"} or not (root / "LICENSE").is_file():
        raise ValueError(
            "The owner must select a license, add root LICENSE and set package.json license before public packaging."
        )
    if len((root / "LICENSE").read_text().strip()) < 100:
        raise ValueError("Root LICENSE must contain the selected license text, not a placeholder.")
    if manifest.get("preview") is not True:
        raise ValueError("This experimental release must remain labeled preview.")
    for name in ("README.md", "CHANGELOG.md", "PRIVACY.md"):
        if not (root / "extensions/vscode" / name).is_file():
            raise ValueError(f"Missing public distribution document: {name}")
    return manifest


def inspect_package(package: Path, manifest: dict, target: str, license_text: bytes) -> dict:
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        required = {
            "extension/package.json",
            "extension/readme.md",
            "extension/changelog.md",
            "extension/PRIVACY.md",
            "extension/LICENSE",
            "extension/python/bridge.py",
            "extension/out/extension.js",
        }
        if not required.issubset(names):
            raise ValueError("VSIX is missing runtime files or public documentation.")
        if any(
            "/node_modules/" in n or "/out/test/" in n or "/.env" in n or n.endswith(".sqlite")
            for n in names
        ):
            raise ValueError("VSIX contains development or private-state files.")
        if archive.read("extension/LICENSE") != license_text:
            raise ValueError("Packaged license differs from the selected project license.")
        packaged = json.loads(archive.read("extension/package.json"))
        for key in ("name", "publisher", "version", "license", "preview"):
            if packaged.get(key) != manifest.get(key):
                raise ValueError(f"Packaged {key} differs from the configured release.")
        xml = ElementTree.fromstring(archive.read("extension.vsixmanifest"))
        ns = {"v": "http://schemas.microsoft.com/developer/vsx-schema/2011"}
        identity = xml.find("v:Metadata/v:Identity", ns)
        if identity is None or identity.get("TargetPlatform") != target:
            raise ValueError("VSIX target platform does not match the requested platform.")
        properties = {
            item.get("Id"): item.get("Value")
            for item in xml.findall("v:Metadata/v:Properties/v:Property", ns)
        }
        if properties.get("Microsoft.VisualStudio.Code.PreRelease") != "true":
            raise ValueError("VSIX is not marked as a Marketplace pre-release.")
        for dependency in ("pathspec-", "pypdf-"):
            if not any(dependency in name and "license" in name.lower() for name in names):
                raise ValueError(f"Missing dependency license notice: {dependency}")
    sha = hashlib.sha256(package.read_bytes()).hexdigest()
    return {
        "file": package.name,
        "sha256": sha,
        "publisher": manifest["publisher"],
        "name": manifest["name"],
        "version": manifest["version"],
        "target": target,
        "channel": "pre-release",
        "license": manifest["license"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("check", "package"))
    parser.add_argument(
        "--publisher", required=True, help="Exact publisher ID from Marketplace management"
    )
    parser.add_argument("--target", choices=TARGETS, default="darwin-arm64")
    args = parser.parse_args()
    try:
        manifest = configuration(ROOT, args.publisher)
        if args.operation == "check":
            print(
                "Local release configuration passes. Publisher ownership/authentication must be verified on Marketplace."
            )
            return 0
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        package = artifacts / f"{manifest['name']}-{manifest['version']}-{args.target}.vsix"
        subprocess.run(
            [
                str(EXTENSION / "node_modules/.bin/vsce"),
                "package",
                "--pre-release",
                "--target",
                args.target,
                "--out",
                str(package),
            ],
            cwd=EXTENSION,
            check=True,
        )
        record = inspect_package(package, manifest, args.target, (ROOT / "LICENSE").read_bytes())
        record["source_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        record["working_tree_dirty"] = bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        )
        package.with_suffix(".vsix.sha256").write_text(f"{record['sha256']}  {package.name}\n")
        package.with_suffix(".release.json").write_text(json.dumps(record, indent=2) + "\n")
        print(f"Validated preview package: {package}\nSHA256: {record['sha256']}")
        print(
            "Upload this exact VSIX in Marketplace management; no network publication was performed."
        )
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Release blocked: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
