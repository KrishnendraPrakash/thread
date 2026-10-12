"""Default-local plan; upload exact source VSIX bytes only from protected main."""

import argparse
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from marketplace_upload import process
from source_package import ROOT, verify


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
    for release in versions(record["publisher"], "thread-agent"):
        if release.get("version") != record["version"] or release.get("targetPlatform") not in {
            None,
            "universal",
        }:
            continue
        properties = {item["key"]: item["value"] for item in release.get("properties", [])}
        if properties.get("Microsoft.VisualStudio.Code.PreRelease", "false") != "false":
            raise ValueError("Published source package is not in the approved stable channel.")
        expected = record["targets"][0]["vsix"]["sha256"]
        if properties.get("Microsoft.VisualStudio.Services.VsixSha256") != expected:
            raise ValueError("Marketplace source package digest differs from reviewed bytes.")
        return True
    return False


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

    return process(record, package.parent, ledger, publish, lambda _: visible(record), True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--ledger", type=Path, default=Path("source-upload-ledger.json"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.root, args.package, args.commit, args.sha256, args.ledger, args.execute)
        ),
        flush=True,
    )
