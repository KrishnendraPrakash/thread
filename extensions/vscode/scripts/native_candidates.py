"""Build host-native release candidates from reviewed local inputs; never publish.

Requires completed release policy and exact-commit validation evidence. Model and
runtime inputs must already be present. Six host results are assembled separately.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from freeze import host_target
from marketplace_preflight import TARGETS, inventory, readiness
from offline_bundle import assemble_bundle

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
    if recipe.get("target") != target:
        raise ValueError("Companion recipe must match the build target.")
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
        staged = json.loads((stage / "package.json").read_text())
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
        bundle = temp / "companion"
        assemble_bundle(recipe, bundle)
        executable = "thread-backend.exe" if target.startswith("win32-") else "thread-backend"
        native_hash = fingerprint(extension / "native" / target / "thread-backend" / executable)[
            "sha256"
        ]
        if not any(
            asset.get("role") == "backend"
            and Path(asset["path"]).name == executable
            and asset.get("sha256") == native_hash
            for asset in recipe["assets"]
        ):
            raise ValueError("Companion backend executable must match this candidate build.")
        companion = temp / f"{name}-offline.zip"
        with zipfile.ZipFile(companion, "w", zipfile.ZIP_STORED, allowZip64=True) as archive:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(bundle).as_posix())
        result = {
            "schema": 1,
            "commit": commit,
            "version": manifest["version"],
            "publisher": manifest["publisher"],
            "channel": "pre-release",
            "target": target,
            "checks": checks,
            "vsix": fingerprint(package),
            "companion": {
                **fingerprint(companion),
                "manifest_sha256": hashlib.sha256(
                    (bundle / "bundle.json").read_bytes()
                ).hexdigest(),
            },
        }
        output.mkdir(parents=True)
        try:
            shutil.copy2(package, output / package.name)
            shutil.copy2(companion, output / companion.name)
            (output / f"{target}.candidate.json").write_text(json.dumps(result, indent=2) + "\n")
        except BaseException:
            shutil.rmtree(output)
            raise
    return result


def aggregate(root, folder, commit, version):
    records = [json.loads(p.read_text()) for p in sorted(folder.glob("*.candidate.json"))]
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
    parser.add_argument("--recipe", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--commit")
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.operation == "build":
        if not all((args.target, args.recipe, args.evidence)):
            parser.error("Build requires --target, --recipe and --evidence.")
        recipe = json.loads(args.recipe.read_text())
        for asset in recipe.get("assets", []):
            source = Path(asset["input"])
            if not source.is_absolute():
                asset["input"] = str((args.recipe.parent / source).resolve())
        build(
            args.root,
            args.target,
            recipe,
            json.loads(args.evidence.read_text()),
            args.output,
        )
    else:
        if not args.commit or not args.version:
            parser.error("Aggregate requires --commit and --version.")
        aggregate(args.root, args.output, args.commit, args.version)


if __name__ == "__main__":
    main()
