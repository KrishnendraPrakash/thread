"""Probe a built backend using no external Python search path or live model."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from freeze import host_target

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--extension-root", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[3]
extension = args.extension_root or root / "extensions/vscode"
target = host_target()
executable = (
    extension
    / "native"
    / target
    / "thread-backend"
    / ("thread-backend.exe" if target.startswith("win32-") else "thread-backend")
)
environment = {
    **os.environ,
    "PYTHONPATH": "/nonexistent/thread-untrusted",
    "PYTHONHOME": "/nonexistent/thread-untrusted",
    "PATH": "/nonexistent/thread-no-system-python",
}
for operation, expected in (("python", True), ("shell", False)):
    result = subprocess.run(
        [str(executable)],
        input=json.dumps({"operation": operation}) + "\n",
        text=True,
        capture_output=True,
        cwd=root,
        env=environment,
        timeout=30,
    )
    envelope = json.loads(result.stdout)
    if envelope["ok"] is not expected or (result.returncode == 0) is not expected:
        raise RuntimeError(f"Native protocol probe failed: {result.stderr} {envelope}")
print(f"Native {target} protocol passed; no model inference was exercised.")
dependencies = subprocess.run(
    [str(executable), "check-dependencies"],
    env=environment,
    text=True,
    capture_output=True,
    timeout=30,
    check=True,
)
if not json.loads(dependencies.stdout).get("frozen"):
    raise RuntimeError("Expected a frozen backend with its embedded interpreter.")
print(f"Bundled dependency imports and decoder round-trip passed: {dependencies.stdout.strip()}")
