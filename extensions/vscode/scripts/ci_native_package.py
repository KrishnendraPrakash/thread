"""Private hosted package proof, with no models/exports/product gate promotion."""

import argparse
import json
import os
import tempfile
from pathlib import Path

from freeze import host_target
from marketplace_preflight import BYO_SCOPE, TARGETS, verify_byo_vsix
from native_candidates import fingerprint, package_native
from runtime_notice_inventory import inventory

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=sorted(TARGETS))
    args = parser.parse_args()
    if (
        args.target != host_target()
        or os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("GITHUB_REPOSITORY") != "KrishnendraPrakash/thread"
        or os.environ.get("THREAD_PRIVATE_PACKAGE_CI") != "github-hosted"
    ):
        raise ValueError("Private package proof requires the approved host-native GitHub runner.")
    policy = json.loads((ROOT / "release/marketplace-policy.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "extensions/vscode/package.json").read_text(encoding="utf-8"))
    if (
        policy["distribution_scope"] != BYO_SCOPE
        or manifest.get("threadModelProvisioning") != "user-supplied"
    ):
        raise ValueError("Private proof must match the approved BYO scope.")
    if "if (process.platform === 'win32')" not in (
        ROOT / "extensions/vscode/src/extension.ts"
    ).read_text(encoding="utf-8"):
        raise ValueError("This approved private check preserves the production Windows guard.")
    native = ROOT / "extensions/vscode/native" / args.target / "thread-backend"
    metadata = inventory(native)
    provenance = json.loads((native / "notices/provenance.json").read_text(encoding="utf-8"))
    for row in metadata["files"]:
        print(json.dumps({"native_file": row}), flush=True)
    print(json.dumps({"native_notice_provenance": provenance}), flush=True)
    distribution_report = json.loads(
        (native / "notices/distribution-provenance.json").read_text(encoding="utf-8")
    )
    for row in distribution_report.pop("images"):
        print(json.dumps({"native_distribution_image": row}), flush=True)
    for row in distribution_report.pop("texts"):
        print(json.dumps({"native_distribution_text": row}), flush=True)
    print(json.dumps({"native_distribution_summary": distribution_report}), flush=True)
    with tempfile.TemporaryDirectory(prefix="thread-byo-ci-package-") as directory:
        package = package_native(ROOT, args.target, manifest, Path(directory))
        verify_byo_vsix(ROOT, manifest, package, args.target)
        print(
            json.dumps(
                {
                    "target": args.target,
                    "vsix": fingerprint(package),
                    "model_free_package_checked": True,
                    "actual_native_protocol_checked": True,
                    "native_files": metadata["file_count"],
                    "native_bytes": metadata["total_bytes"],
                    "complete_distribution_review": False,
                    "ordinary_user_trust_checked": False,
                    "real_inference_checked": False,
                    "public_release_ready": False,
                }
            ),
            flush=True,
        )
    print("THREAD_BYO_PRIVATE_PACKAGE_REMOVED: " + args.target, flush=True)


if __name__ == "__main__":
    main()
