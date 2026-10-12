"""Plan or resume exact reviewed uploads with a durable per-target ledger.

Default is read-only planning. Execution belongs only in the protected publisher
job. Uncertain uploads require owner reconciliation and are never blindly retried.
"""

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from marketplace_preflight import inventory

ROOT = Path(__file__).resolve().parents[3]


def listing(publisher, extension, version, target):
    body = {
        "filters": [{"criteria": [{"filterType": 7, "value": f"{publisher}.{extension}"}]}],
        "flags": 17,
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
    for group in result.get("results", []):
        for item in group.get("extensions", []):
            if (
                item.get("publisher", {}).get("publisherName") != publisher
                or item.get("extensionName") != extension
            ):
                continue
            for release in item.get("versions", []):
                if release.get("version") == version and release.get("targetPlatform") == target:
                    properties = {p["key"]: p["value"] for p in release.get("properties", [])}
                    if properties.get("Microsoft.VisualStudio.Code.PreRelease") != "true":
                        raise ValueError(
                            "Marketplace version is not in the approved preview channel."
                        )
                    return True
    return False


def save(path, ledger):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x") as stream:
        json.dump(ledger, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def process(record, folder, ledger_path, publish, visible, execute=False, *, wait_for_listing=None):
    if not execute:
        return _process(record, folder, ledger_path, publish, visible, False)
    lock = ledger_path.with_name(ledger_path.name + ".lock")
    handle = lock.open("x")
    try:
        with handle:
            return _process(record, folder, ledger_path, publish, visible, True, wait_for_listing)
    finally:
        lock.unlink()


def _process(record, folder, ledger_path, publish, visible, execute=False, wait_for_listing=None):
    identity = {k: record[k] for k in ("commit", "version", "publisher", "channel")}
    expected = {item["target"]: item["vsix"]["sha256"] for item in record["targets"]}
    ledger = (
        json.loads(ledger_path.read_text())
        if ledger_path.exists()
        else {"schema": 1, **identity, "hashes": expected, "targets": {}}
    )
    if (
        ledger.get("schema") != 1
        or any(ledger.get(k) != v for k, v in identity.items())
        or ledger.get("hashes") != expected
    ):
        raise ValueError("Recovery ledger differs from the exact reviewed release.")
    if not execute:
        return {
            "operation": "plan",
            "release": identity,
            "targets": [
                {"target": t, "state": ledger["targets"].get(t, "not_started")}
                for t in sorted(expected)
            ],
        }
    for item in record["targets"]:
        target = item["target"]
        state = ledger["targets"].get(target, "not_started")
        if state == "verified":
            if not visible(target):
                raise ValueError("Previously verified listing is no longer visible.")
            continue
        if state in {"uploading", "uncertain"}:
            raise ValueError(f"Owner reconciliation required for uncertain upload: {target}")
        if state == "uploaded":
            if visible(target):
                ledger["targets"][target] = "verified"
                save(ledger_path, ledger)
                continue
            raise ValueError(f"Listing pending for {target}; resume later without re-uploading.")
        if state != "not_started":
            raise ValueError("Unknown upload state.")
        if visible(target):
            raise ValueError(
                f"Existing version for {target} lacks this ledger's upload provenance."
            )
        ledger["targets"][target] = "uploading"
        save(ledger_path, ledger)
        try:
            publish(folder / item["vsix"]["file"])
        except BaseException:
            ledger["targets"][target] = "uncertain"
            save(ledger_path, ledger)
            raise
        ledger["targets"][target] = "uploaded"
        save(ledger_path, ledger)
        if wait_for_listing is not None:
            wait_for_listing(target)
            ledger["targets"][target] = "verified"
            save(ledger_path, ledger)
            continue
        for attempt in range(6):
            if visible(target):
                ledger["targets"][target] = "verified"
                save(ledger_path, ledger)
                break
            if attempt < 5:
                time.sleep(5)
        else:
            raise ValueError(f"Listing pending for {target}; resume later without re-uploading.")
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    record = inventory(args.root, args.artifacts, args.commit, args.version)
    if args.execute and (
        os.environ.get("THREAD_MARKETPLACE_ENABLED") != "reviewed-and-enabled"
        or os.environ.get("GITHUB_REF") != "refs/heads/main"
        or os.environ.get("GITHUB_SHA") != args.commit
    ):
        parser.error("Execution requires enabled protected main job at exact approved commit.")

    def publish(path):
        subprocess.run(
            [
                shutil.which("node") or "node",
                str(args.root / "extensions/vscode/node_modules/@vscode/vsce/vsce"),
                "publish",
                "--azure-credential",
                "--pre-release",
                "--packagePath",
                str(path.resolve()),
            ],
            check=True,
        )

    result = process(
        record,
        args.artifacts,
        args.ledger,
        publish,
        lambda target: listing(record["publisher"], "thread-agent", args.version, target),
        args.execute,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
