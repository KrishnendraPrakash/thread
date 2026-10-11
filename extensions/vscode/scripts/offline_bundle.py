"""Audit an unpacked offline companion bundle without execution or downloads.

Validation establishes inventory integrity, not publisher authenticity, licensing
approval, native compatibility, model quality, or readiness for production import.
"""

import argparse
import hashlib
import json
import re
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath

from freeze import TARGETS


def safe_path(name):
    if (
        not isinstance(name, str)
        or not name
        or len(name) > 500
        or re.search(r'[\\:\x00-\x1f<>"|?*]', name)
        or any(
            part in {"", ".", ".."}
            or part.endswith((" ", "."))
            or re.match(r"^(con|prn|aux|nul|clock\$|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)", part, re.I)
            for part in name.split("/")
        )
    ):
        raise ValueError("Unsafe asset path.")
    return name


def assemble_bundle(recipe: dict, output: Path) -> dict:
    """Copy explicitly inventoried local files; never download or execute assets.

    Each asset adds an input path to the import manifest. Size/digest are supplied
    expectations, not inferred trust. Existing output is never replaced.
    """
    if output.exists() or output.is_symlink():
        raise ValueError("Output already exists; choose a new directory.")
    manifest = {key: value for key, value in recipe.items() if key != "assets"}
    assets = recipe.get("assets")
    if not isinstance(assets, list) or not 1 <= len(assets) <= 10000:
        raise ValueError("Expected a bounded asset inventory.")
    manifest["assets"] = []
    names = set()
    total = 0
    for asset in assets:
        name = safe_path(asset.get("path", ""))
        if (
            not isinstance(name, str)
            or not name
            or PurePosixPath(name).is_absolute()
            or "\\" in name
            or ":" in name
            or any(part in {"", ".", ".."} for part in name.split("/"))
            or name.casefold() in {"bundle.json", "import.json"}
            or name.casefold() in names
        ):
            raise ValueError("Unsafe or duplicate output asset path.")
        names.add(name.casefold())
        size = asset.get("size")
        if type(size) is not int or size < 0:
            raise ValueError("Invalid asset size.")
        total += size
        if total > 100 * 1024**3:
            raise ValueError("Bundle exceeds 100 GiB.")
        manifest["assets"].append({k: v for k, v in asset.items() if k != "input"})
        executable = asset.get("executable")
        if "executable" in asset and (
            type(executable) is not bool
            or (executable and asset.get("role") not in {"backend", "runtime"})
        ):
            raise ValueError("Executable flags require backend/runtime assets.")
    if any(
        parent.casefold() in names
        for name in names
        for parent in [str(p) for p in PurePosixPath(name).parents if str(p) != "."]
    ):
        raise ValueError("File/directory asset collision.")
    runtime = safe_path(recipe.get("runtimeExecutable"))
    models = safe_path(recipe.get("modelDirectory"))
    if not any(a["path"] == runtime and a.get("role") == "runtime" for a in assets):
        raise ValueError("Runtime executable is not inventoried.")
    if not any(a["path"].startswith(models + "/") and a.get("role") == "model" for a in assets):
        raise ValueError("Model directory is not inventoried.")
    if not all(
        isinstance(recipe.get(k), str) and recipe[k].strip() for k in ("model", "runtimeVersion")
    ):
        raise ValueError("Runtime version and model identity are required.")
    encoded = (json.dumps(manifest, indent=2) + "\n").encode()
    if len(encoded) > 1024 * 1024:
        raise ValueError("Manifest exceeds 1 MiB.")
    output = output.absolute()
    # Caller owns this parent. No source folders or existing artifacts are removed.
    with tempfile.TemporaryDirectory(prefix=".thread-assemble-", dir=output.parent) as temp:
        staging = Path(temp) / "bundle"
        staging.mkdir()
        for asset in assets:
            source = Path(asset["input"])
            if not source.is_absolute() or any(p.is_symlink() for p in (source, *source.parents)):
                raise ValueError("Input must be an absolute path without symlinks.")
            info = source.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("Input must be an unlinked regular file.")
            destination = staging / asset["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            copied = 0
            with source.open("rb") as stream, destination.open("xb") as target:
                while chunk := stream.read(1024 * 1024):
                    copied += len(chunk)
                    if copied > asset["size"]:
                        raise ValueError("Input grew beyond its approved size.")
                    target.write(chunk)
            destination.chmod(0o755 if info.st_mode & 0o111 else 0o644)
        (staging / "bundle.json").write_bytes(encoded)
        validate_bundle(staging, recipe.get("target"))
        # Reserve the destination exclusively so a concurrent assembler cannot replace it.
        output.mkdir()
        try:
            for item in staging.iterdir():
                shutil.move(str(item), output / item.name)
        except BaseException:
            shutil.rmtree(output)
            raise
    return manifest


def validate_bundle(directory: Path, target: str) -> dict:
    if directory.is_symlink():
        raise ValueError("Bundle directory cannot be a symlink.")
    root = directory.resolve(strict=True)
    manifest_path = root / "bundle.json"
    if manifest_path.is_symlink() or manifest_path.stat().st_size > 1024 * 1024:
        raise ValueError("Invalid bundle manifest.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if target not in TARGETS or manifest.get("schema") != 1 or manifest.get("target") != target:
        raise ValueError("Bundle schema or native target mismatch.")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets or len(assets) > 10000:
        raise ValueError("Expected a bounded asset inventory.")
    roles = set()
    names = set()
    for asset in assets:
        name = asset.get("path", "")
        relative = PurePosixPath(name)
        if (
            not name
            or relative.is_absolute()
            or "\\" in name
            or ":" in name
            or any(part in {"", ".", ".."} for part in name.split("/"))
        ):
            raise ValueError("Unsafe asset path.")
        if name.casefold() in names:
            raise ValueError("Duplicate asset path.")
        names.add(name.casefold())
        item = root
        for part in relative.parts:
            item = item / part
            if item.is_symlink():
                raise ValueError("Bundle assets cannot be symlinks.")
        if not item.is_file() or item.stat().st_nlink != 1:
            raise ValueError("Bundle asset must be an unlinked regular file.")
        if not isinstance(asset.get("size"), int) or item.stat().st_size != asset["size"]:
            raise ValueError("Asset size mismatch.")
        digest = hashlib.sha256()
        with item.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        if digest.hexdigest() != asset.get("sha256"):
            raise ValueError("Asset checksum mismatch.")
        if not all(
            isinstance(asset.get(key), str) and asset[key].strip()
            for key in ("source", "license", "version", "role")
        ):
            raise ValueError("Asset provenance and license identity are required.")
        roles.add(asset["role"])
    if not {"backend", "runtime", "model", "notice"}.issubset(roles):
        raise ValueError("Offline bundle needs backend, runtime, model and notice assets.")
    # Reject unlisted content; never accept a partial manifest as a complete offline bundle.
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ValueError("Bundle cannot contain symlinks.")
        if (
            item.is_file()
            and item != manifest_path
            and item.relative_to(root).as_posix().casefold() not in names
        ):
            raise ValueError("Bundle contains unlisted files.")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = assemble_bundle(json.loads(args.recipe.read_text()), args.output)
    print(
        json.dumps(
            {
                "target": result["target"],
                "assets": len(result["assets"]),
                "manifest_sha256": hashlib.sha256(
                    (args.output / "bundle.json").read_bytes()
                ).hexdigest(),
                "inference_verified": False,
            },
            indent=2,
        )
    )
