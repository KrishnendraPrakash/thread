"""Default-local plan; upload exact source VSIX bytes only from protected main."""

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from marketplace_upload import process
from source_package import ROOT, verify

LISTING_WAIT_SECONDS = 15 * 60


class ListingPending(ValueError):
    """Upload is recorded, but the public listing is not yet validated."""


class ListingRejected(ValueError):
    """Marketplace explicitly reports rejection; uploading again is forbidden."""


class ListingMismatch(ValueError):
    """A visible version differs from the reviewed target, channel or bytes."""


def versions(publisher, extension):
    body = {
        "filters": [{"criteria": [{"filterType": 7, "value": f"{publisher}.{extension}"}]}],
        "flags": 147,
    }
    request = urllib.request.Request(
        "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json;api-version=7.2-preview.1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    matches = [
        item
        for group in result.get("results", [])
        for item in group.get("extensions", [])
        if item.get("publisher", {}).get("publisherName") == publisher
        and item.get("extensionName") == extension
    ]
    if len(matches) != 1:
        raise ValueError("Expected the existing exact Marketplace extension identity.")
    return matches[0].get("versions", [])


def available(record):
    import re

    selected = tuple(int(n) for n in record["version"].split("."))
    for release in versions(record["publisher"], "thread-agent"):
        if re.fullmatch(r"\d+\.\d+\.\d+", release.get("version", "")):
            if tuple(int(n) for n in release["version"].split(".")) >= selected:
                raise ValueError(
                    "Source version must be newer than the existing Marketplace release."
                )


def visible(record):
    matches = [
        v
        for v in versions(record["publisher"], "thread-agent")
        if v.get("version") == record["version"]
    ]
    universal = [v for v in matches if v.get("targetPlatform") in {None, "universal"}]
    if matches and (len(universal) != 1 or len(matches) != 1):
        raise ListingMismatch("Marketplace version differs from the single universal target.")
    for release in universal:
        flags = release.get("flags")
        message = str(release.get("validationResultMessage") or "")
        # Do not infer rejection from absence, an unvalidated flag, or generic
        # free text. Preserve explicit rejection evidence if the service supplies it.
        if str(flags).lower() in {"rejected", "validationfailed"} or message.lower().startswith(
            ("validation failed", "rejected:")
        ):
            raise ListingRejected(f"Marketplace rejected this version: {message or flags}")
        if flags is not None and flags not in {1, "validated"}:
            return False
        properties = {item["key"]: item["value"] for item in release.get("properties", [])}
        if properties.get("Microsoft.VisualStudio.Code.PreRelease", "false") != "false":
            raise ListingMismatch("Published source package is not in the approved stable channel.")
        expected = record["targets"][0]["vsix"]["sha256"]
        if properties.get("Microsoft.VisualStudio.Services.VsixSha256") != expected:
            raise ListingMismatch("Marketplace source package digest differs from reviewed bytes.")
        return True
    return False


def wait_visible(record, *, timeout=LISTING_WAIT_SECONDS, clock=time.monotonic, sleep=time.sleep):
    """Bound total polling time; mismatches/rejections stop without an upload retry."""
    deadline = clock() + timeout
    delay = 5
    while True:
        if visible(record):
            return
        remaining = deadline - clock()
        if remaining <= 0:
            raise ListingPending(
                "Listing pending; preserve the uploaded ledger and use --verify-only. "
                "Do not rerun publication."
            )
        sleep(min(delay, remaining))
        delay = min(delay * 2, 45)


def recover(root, package, commit, sha256, ledger_path, receipt_path=None):
    """Verify a recorded upload without any publishing or authentication operation."""
    record = verify(root, package, commit, sha256)
    ledger = json.loads(ledger_path.read_text())
    identity = {key: record[key] for key in ("commit", "version", "publisher", "channel")}
    if (
        ledger.get("schema") != 1
        or any(ledger.get(key) != value for key, value in identity.items())
        or ledger.get("hashes") != {"universal": sha256}
        or ledger.get("targets") not in ({"universal": "uploaded"}, {"universal": "verified"})
    ):
        raise ValueError("Verification requires the exact uploaded/verified source ledger.")
    if receipt_path is not None and (
        receipt_path.resolve() in {ledger_path.resolve(), package.resolve()}
        or receipt_path.exists()
    ):
        raise ValueError("Verification receipt must be a new file separate from original evidence.")
    wait_visible(record)
    receipt = {
        "schema": 1,
        "operation": "verification-only",
        **identity,
        "verified_at": datetime.now(UTC).isoformat(),
        "targets": {"universal": "verified"},
        "hashes": ledger["hashes"],
        "upload_invoked": False,
    }
    if receipt_path is not None:
        with receipt_path.open("x") as stream:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
    return receipt


def run(root, package, commit, sha256, ledger, execute=False):
    record = verify(root, package, commit, sha256)
    if not execute:
        return process(record, package.parent, ledger, lambda _: None, lambda _: False)
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("GITHUB_REPOSITORY") != "KrishnendraPrakash/thread"
        or os.environ.get("GITHUB_REF") != "refs/heads/main"
        or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
        or os.environ.get("GITHUB_SHA") != commit
        or os.environ.get("THREAD_SOURCE_PUBLISH_APPROVED") != "github-protected-main"
    ):
        raise ValueError("Source upload requires explicit protected-main dispatch approval.")
    # Recovery states are checked by the durable existing ledger. Never blindly
    # retry an uncertain upload or infer ownership from an existing listing.
    if not ledger.exists():
        available(record)

    def publish(path):
        verify(root, path, commit, sha256)
        subprocess.run(
            [
                shutil.which("node") or "node",
                str(root / "extensions/vscode/node_modules/@vscode/vsce/vsce"),
                "publish",
                "--azure-credential",
                "--packagePath",
                str(path.resolve()),
            ],
            check=True,
        )

    return process(
        record,
        package.parent,
        ledger,
        publish,
        lambda _: visible(record),
        True,
        wait_for_listing=lambda _: wait_visible(record),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--ledger", type=Path, default=Path("source-upload-ledger.json"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify-only", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.receipt is not None and not args.verify_only:
        parser.error("--receipt belongs only to --verify-only")
    print(
        json.dumps(
            recover(args.root, args.package, args.commit, args.sha256, args.ledger, args.receipt)
            if args.verify_only
            else run(args.root, args.package, args.commit, args.sha256, args.ledger, args.execute)
        ),
        flush=True,
    )
