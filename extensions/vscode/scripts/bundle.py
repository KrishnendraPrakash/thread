"""Bundle the core and pure-Python dependencies, retaining distribution notices."""

import shutil
from importlib.metadata import distribution
from pathlib import Path

root = Path(__file__).resolve().parents[3]
output = root / "extensions/vscode/python"
# This is a generated directory, never a user-selected destination.
if output.exists():
    shutil.rmtree(output)
output.mkdir()
shutil.copytree(
    root / "src/thread_agent",
    output / "thread_agent",
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
)
for name in ("pathspec", "pypdf"):
    package = distribution(name)
    for file in package.files or []:
        if ".." in file.parts or "__pycache__" in file.parts or file.suffix == ".pyc":
            continue
        destination = output / file
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package.locate_file(file), destination)
shutil.copy2(Path(__file__).with_name("bridge.py"), output / "bridge.py")
print(f"Bundled backend and dependency notices in {output}")
