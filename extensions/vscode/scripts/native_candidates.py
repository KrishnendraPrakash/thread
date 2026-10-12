"""Build host-native release candidates from reviewed local inputs; never publish.

Requires completed release policy and exact-commit validation evidence. The BYO release contains native VSIXs only. User-provided offline imports are separate.
Six host results are assembled separately.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from freeze import host_target
from marketplace_preflight import BYO_SCOPE, TARGETS, inventory, readiness

ROOT = Path(__file__).resolve().parents[3]
CHECKS = ("native_package", "security", "editor", "clean_machine", "offline_inference")


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"file": path.name, "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def evidence(record, target, commit):
    if record.get("target") != target or record.get("commit") != commit:
        raise ValueError("Evidence target/commit mismatch.")
    for name in CHECKS:
        item = record.get("checks", {}).get(name, {})
        if (
            item.get("result") != "passed"
            or item.get("commit") != commit
            or not isinstance(item.get("url"), str)
            or not item["url"].startswith("https://")
        ):
            raise ValueError(f"Missing reviewed {name} evidence.")
    return record["checks"]


def build(root, target, recipe, validation, output):
    manifest = readiness(root)
    if target != host_target():
        raise ValueError("Candidate must be built on its native host.")
    if recipe:
        raise ValueError("Companion/model recipes are outside the BYO release scope.")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        raise ValueError("Candidate source checkout must be clean.")
    checks = evidence(validation, target, commit)
    if output.exists():
        raise ValueError("Candidate output must not already exist.")
    extension = root / "extensions/vscode"
    scripts = extension / "scripts"
    subprocess.run([sys.executable, str(scripts / "freeze.py"), "--target", target], check=True)
    subprocess.run(
        [shutil.which("npm") or "npm", "run", "compile", "--prefix", str(extension)], check=True
    )
    with tempfile.TemporaryDirectory(prefix="thread-candidate-") as temporary:
        temp = Path(temporary)
        package = package_native(root, target, manifest, temp)
        result = {
            "schema": 1,
            "commit": commit,
            "version": manifest["version"],
            "publisher": manifest["publisher"],
            "channel": "pre-release",
            "target": target,
            "checks": checks,
            "vsix": fingerprint(package),
            "distribution_scope": BYO_SCOPE,
        }
        output.mkdir(parents=True)
        try:
            shutil.copy2(package, output / package.name)
            (output / f"{target}.candidate.json").write_text(json.dumps(result, indent=2) + "\n")
        except BaseException:
            shutil.rmtree(output)
            raise
    return result


def package_native(root, target, manifest, temp):
    """Stage/probe a private host package; this alone establishes no release readiness."""
    extension = root / "extensions/vscode"
    scripts = extension / "scripts"
    stage = temp / "extension"
    shutil.copytree(
        extension,
        stage,
        ignore=shutil.ignore_patterns(
            "node_modules",
            "src",
            "scripts",
            "python",
            "native",
            "*.map",
            "tsconfig.json",
            "package-lock.json",
            "test",
            "__pycache__",
        ),
    )
    shutil.copytree(extension / "native" / target, stage / "native" / target)
    shutil.copy2(root / "LICENSE", stage / "LICENSE")
    staged = json.loads((stage / "package.json").read_text(encoding="utf-8"))
    staged.get("scripts", {}).pop("vscode:prepublish", None)
    (stage / "package.json").write_text(json.dumps(staged, indent=2))
    name = f"thread-agent-{manifest['version']}-{target}"
    package = temp / f"{name}.vsix"
    subprocess.run(
        [
            shutil.which("node") or "node",
            str(extension / "node_modules/@vscode/vsce/vsce"),
            "package",
            "--pre-release",
            "--no-dependencies",
            "--target",
            target,
            "--out",
            str(package),
        ],
        cwd=stage,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(scripts / "check_native_package.py"), str(package)], check=True
    )
    return package


def aggregate(root, folder, commit, version):
    records = [
        json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.candidate.json"))
    ]
    if len(records) != 6 or {r.get("target") for r in records} != TARGETS:
        raise ValueError("Aggregation requires exactly six native candidate records.")
    if any(r.get("commit") != commit or r.get("version") != version for r in records):
        raise ValueError("Candidate source/version mismatch.")
    manifest = readiness(root)
    record = {
        "schema": 1,
        "commit": commit,
        "version": version,
        "publisher": manifest["publisher"],
        "channel": "pre-release",
        "targets": records,
        "distribution_scope": BYO_SCOPE,
    }
    destination = folder / "release.json"
    if destination.exists():
        raise ValueError("Release inventory already exists.")
    destination.write_text(json.dumps(record, indent=2) + "\n")
    try:
        inventory(root, folder, commit, version)
    except BaseException:
        destination.unlink()
        raise
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("build", "aggregate"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--target", choices=sorted(TARGETS))
    parser.add_argument(
        "--recipe",
        type=Path,
        help="Rejected for BYO 0.2.1; retained only for explicit failure on old invocations",
    )
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--commit")
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.operation == "build":
        if not all((args.target, args.evidence)):
            parser.error("Build requires --target and --evidence.")
        if args.recipe:
            parser.error("Companion recipes are outside the BYO release scope.")
        build(
            args.root,
            args.target,
            None,
            json.loads(args.evidence.read_text(encoding="utf-8")),
            args.output,
        )
    else:
        if not args.commit or not args.version:
            parser.error("Aggregate requires --commit and --version.")
        aggregate(args.root, args.output, args.commit, args.version)


if __name__ == "__main__":
    main()
