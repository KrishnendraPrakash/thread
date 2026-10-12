"""GitHub-runner-only acquisition/audit for approved private CPU integration.

Never publish/export assets or infer legal/model readiness from these checks.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from runtime_assets import ASSETS
from runtime_notice_inventory import inventory

ROOT = Path(__file__).resolve().parents[3]
MODEL = "qwen2.5-coder:0.5b"
REGISTRY = "https://registry.ollama.ai/v2/library/qwen2.5-coder"
MANIFEST_SHA = "4ff64a7f502a08b7616edb8ca0a79eb1853fc363d842b7df4b46915d11a3fb09"
BLOBS = {
    "abd33a30420b0d013edc16c98fde77e4301f4c0cee721d6fbf203b76e5aee426": 490,
    "20693aeb02c63304e263a72453b6ab89e1c700a87c6948cac523ac1e6f7cade0": 397808000,
    "66b9ea09bd5b7099cbb4fc820f31b575c0366fa439b08245566692c6784e281e": 68,
    "1e65450c30670713aa47fe23e8b9662bdf4065e81cc8e3cbfaa98924fcc0d320": 1615,
    "832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e": 11343,
}
CUDNN_TERMS = "https://docs.nvidia.com/deeplearning/cudnn/backend/v9.18.1/reference/eula.html"

# Exact permissive notice bytes inspected in pinned-archive metadata run 38215230670.
# This permits only these notices, never a cuDNN/MLX binary or a changed license.
PERMISSIVE_NOTICE_HASHES = {
    "lib/ollama/CUDNN_LICENSE.txt": {
        "b6fe452605fe29245f0cbafa724b42df94a5e170bedb9d45bc9cfaa4883ad907",
    },
    "lib/ollama/MLX_LICENSE": {
        "e93675e97d080c4fcfef6dd530448b9a6fd7c1ad43c736d593537079cd669d3d",
        "ccfab7ccb2ea306f71531c8ca77bb55507606cd90768b1e32b8b52ab5b48cf01",
    },
    "lib/ollama/MLX_C_LICENSE": {
        "d8d63c7fa57071d80d30116d014e4189c52ef4cb2d1671f6d848e78d9f6cfad0",
        "44326a4ea062241ae6fc26ee2ec90bdc81af7eb7b9d3966181b733fa69d42057",
    },
}


def require_runner(target):
    actual = f"{sys.platform}-" + {"amd64": "x64", "x86_64": "x64"}.get(
        platform.machine().lower(), "unsupported"
    )
    if (
        target not in {"win32-x64", "linux-x64"}
        or actual != target
        or os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("GITHUB_REPOSITORY") != "KrishnendraPrakash/thread"
        or os.environ.get("THREAD_RUNTIME_CI_ENVIRONMENT") != "github-hosted"
        or os.environ.get("RUNNER_ARCH") != "X64"
    ):
        raise ValueError("Runtime/model operations require the approved hosted x64 GitHub runner.")


def write_report(work, name, value):
    (work / name).write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({"report": name, **value}), flush=True)


def required_disk(target):
    return ASSETS[target][1] + (17_000_000_000 if target == "linux-x64" else 9_000_000_000)


def preflight(work, target):
    require_runner(target)
    if work.exists() or work.is_symlink():
        raise ValueError("Use a new caller-owned CI work directory.")
    work.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(work.parent).free
    required = required_disk(target)
    print(json.dumps({"target": target, "free_bytes": free, "required_bytes": required}))
    if free < required:
        raise ValueError("RESOURCE_STOP: insufficient free disk; no runtime/model downloaded.")
    work.mkdir()
    write_report(
        work,
        "owner-scope.json",
        {
            "target": target,
            "github_runner_only": True,
            "runtime": "0.34.4",
            "model": MODEL,
            "manifest_sha256": MANIFEST_SHA,
            "free_bytes_before_downloads": free,
            "required_bytes": required,
        },
    )


def vendor_blocks(entries):
    """Fail closed for unapproved optional/vendor payloads; no license auto-acceptance."""
    blocks = []
    for entry in entries:
        if entry.get("sha256") in PERMISSIVE_NOTICE_HASHES.get(entry["path"], set()):
            continue
        name = entry["path"].lower()
        if "cudnn" in name:
            blocks.append({"path": entry["path"], "agreement": "cuDNN", "url": CUDNN_TERMS})
        elif any(
            token in name
            for token in ("tensorrt", "nvinfer", "rocm", "mlx_", "vc_redist", "vcredist")
        ) or (
            any(token in name for token in ("eula", "agreement", "terms")) and "cuda" not in name
        ):
            blocks.append(
                {
                    "path": entry["path"],
                    "agreement": "Unapproved optional/vendor component",
                    "url": "https://github.com/ollama/ollama/releases/tag/v0.34.4",
                }
            )
    return blocks


def audit(work, target):
    require_runner(target)
    scope = json.loads((work / "owner-scope.json").read_text())
    if scope["target"] != target:
        raise ValueError("CI target changed.")
    native = inventory(ROOT / f"extensions/vscode/native/{target}/thread-backend")
    runtime = inventory(work / "managed/ollama-0.34.4")
    write_report(work, "native-inventory.json", native)
    write_report(work, "runtime-inventory.json", runtime)
    marker = json.loads((work / "managed/ollama-0.34.4/installed.json").read_text())
    if marker != {"version": "0.34.4", "sha256": ASSETS[target][2], "target": target}:
        raise ValueError("Installed runtime identity differs from the approved pin.")
    blocks = vendor_blocks(runtime["files"])
    for entry in runtime["files"]:
        if entry.get("notice_name_candidate") and entry["size"] <= 2 * 1024 * 1024:
            text = (
                (work / "managed/ollama-0.34.4" / entry["path"]).read_text(errors="replace").lower()
            )
            if "cudnn" in text:
                blocks.append(
                    {"path": entry["path"], "agreement": "cuDNN notice", "url": CUDNN_TERMS}
                )
    result = {
        "target": target,
        "status": "blocked" if blocks else "ready_for_private_test",
        "additional_agreements": blocks,
        "complete_legal_review": False,
        "accepted_vendor_terms": ["CUDA 12.8", "CUDA 13.0"],
        "optional_mlx_rocm_assets_requested": False,
    }
    write_report(work, "vendor-audit.json", result)
    if blocks:
        raise ValueError("TERMS_STOP: additional vendor agreement; no Ollama/model execution.")


def verify_manifest(data):
    if len(data) > 65536 or hashlib.sha256(data).hexdigest() != MANIFEST_SHA:
        raise ValueError("Model tag drift; stop for updated approval before blob downloads.")
    manifest = json.loads(data)
    descriptors = [manifest["config"], *manifest["layers"]]
    observed = {item["digest"].removeprefix("sha256:"): item["size"] for item in descriptors}
    if len(descriptors) != len(BLOBS) or observed != BLOBS:
        raise ValueError("Model config/layers differ from the approved pins.")
    return manifest


def download_blob(url, output, size, sha):
    if output.exists() or output.is_symlink():
        raise ValueError("Never overwrite existing model blobs.")
    temporary = output.with_suffix(".partial")
    digest, count = hashlib.sha256(), 0
    try:
        with urllib.request.urlopen(url, timeout=60) as source, temporary.open("xb") as target:
            if urlsplit(source.url).scheme != "https":
                raise ValueError("Model download must stay on HTTPS.")
            while block := source.read(1024 * 1024):
                count += len(block)
                if count > size:
                    raise ValueError("Model blob exceeds its exact pinned size.")
                digest.update(block)
                target.write(block)
        if count != size or digest.hexdigest() != sha:
            raise ValueError("Model blob size/digest mismatch.")
        temporary.rename(output)
    finally:
        temporary.unlink(missing_ok=True)


def acquire_model(work, target):
    require_runner(target)
    if json.loads((work / "vendor-audit.json").read_text())["status"] != "ready_for_private_test":
        raise ValueError("Vendor audit must pass before model acquisition/execution.")
    with urllib.request.urlopen(REGISTRY + "/manifests/0.5b", timeout=30) as response:
        data = response.read(65537)
    verify_manifest(data)
    models = work / "managed/models"
    if models.exists() or models.is_symlink():
        raise ValueError("Use a fresh test model store; never modify another store.")
    if shutil.disk_usage(work).free < sum(BLOBS.values()) + 1_000_000_000:
        raise ValueError("RESOURCE_STOP: insufficient model headroom.")
    blobs = models / "blobs"
    blobs.mkdir(parents=True)
    for sha, size in BLOBS.items():
        download_blob(REGISTRY + "/blobs/sha256:" + sha, blobs / ("sha256-" + sha), size, sha)
    manifest = models / "manifests/registry.ollama.ai/library/qwen2.5-coder/0.5b"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(data)
    write_report(
        work,
        "model-acquisition.json",
        {
            "model": MODEL,
            "manifest_sha256": MANIFEST_SHA,
            "blob_bytes": sum(BLOBS.values()),
            "blobs": BLOBS,
            "license": "Apache-2.0",
            "user_default": False,
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("preflight", "audit", "model"))
    parser.add_argument("--target", required=True)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    {"preflight": preflight, "audit": audit, "model": acquire_model}[args.operation](
        args.work, args.target
    )


if __name__ == "__main__":
    main()
