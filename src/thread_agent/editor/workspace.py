"""Repository discovery and bounded text retrieval without executing repository code."""

from __future__ import annotations

import math
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from thread_agent.domain.records import AgentError, digest

MAX_FILE = 96 * 1024
MAX_FILES = 3000
MAX_TOTAL = 16 * 1024 * 1024
EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    "build",
    "dist",
    "coverage",
    "__pycache__",
    "venv",
    "target",
    "artifacts",
}
TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".rst",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".sh",
    ".bash",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".kts",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".swift",
    ".dart",
    ".rb",
    ".php",
    ".vue",
    ".svelte",
    ".xml",
    ".ini",
    ".cfg",
    ".conf",
    ".graphql",
    ".proto",
    ".ipynb",
    ".mmd",
}
TEXT_NAMES = {"Dockerfile", "Makefile", "Justfile", "LICENSE", "Gemfile", "Rakefile"}
SECRET_NAMES = {
    "credentials.json",
    "secrets.json",
    "secrets.yaml",
    "secrets.yml",
    "secrets.toml",
    "id_rsa",
    "id_ed25519",
    "package-lock.json",
    "uv.lock",
    "yarn.lock",
    "pnpm-lock.yaml",
}


def safe_relative(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or "\\" in name
        or "\x00" in name
        or any(part in {".", ".."} for part in name.split("/"))
        or any(part.startswith(".") and part != ".github" for part in path.parts)
        or any(part in EXCLUDED_DIRS for part in path.parts)
        or path.name.lower() in SECRET_NAMES
        or any(word in path.stem.lower() for word in ("credential", "secret", "private_key"))
        or (path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in TEXT_NAMES)
    ):
        raise AgentError("Path is outside the permitted source-file policy.")
    return path


def read_bytes(root: Path, name: str, limit: int = MAX_FILE, *, internal: bool = False) -> bytes:
    path = PurePosixPath(name) if internal else safe_relative(name)
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise AgentError("Secure repository access currently requires macOS or Linux.")
    descriptors = []
    try:
        descriptors.append(os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW))
        for part in path.parts[:-1]:
            descriptors.append(
                os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptors[-1])
            )
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptors[-1])
        descriptors.append(fd)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
            raise AgentError("Source is linked, non-regular, or exceeds the byte limit.")
        chunks = []
        total = 0
        while total <= limit:
            chunk = os.read(fd, min(8192, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        after = os.fstat(fd)
        if total > limit or (before.st_size, before.st_mtime_ns) != (
            after.st_size,
            after.st_mtime_ns,
        ):
            raise AgentError("Source changed while reading or exceeded the byte limit.")
        return b"".join(chunks)
    except OSError as exc:
        raise AgentError("Cannot securely read the selected source.") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def decode(data: bytes) -> str:
    if b"\x00" in data:
        raise AgentError("Binary files are not repository text sources.")
    try:
        return data.decode("utf-8")
    except UnicodeError as exc:
        raise AgentError("Source must be UTF-8 text.") from exc


def entries(root: Path, directory: Path) -> list[tuple[str, bool, bool]]:
    """Enumerate through descriptors so a swapped directory cannot escape the root."""
    descriptors = []
    try:
        descriptors.append(os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW))
        for part in directory.relative_to(root).parts:
            descriptors.append(
                os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptors[-1])
            )
        with os.scandir(descriptors[-1]) as iterator:
            result = []
            for entry in iterator:
                if len(result) >= 20000:
                    raise AgentError("A directory exceeds the 20,000-entry scan limit.")
                result.append((entry.name, entry.is_dir(follow_symlinks=False), entry.is_symlink()))
            return sorted(result)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


@dataclass(frozen=True)
class Source:
    path: str
    text: str
    sha256: str

    def record(self) -> dict:
        return {"path": self.path, "text": self.text, "sha256": self.sha256}


def tokens(text: str) -> set[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return {word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9]{2,}", text)}


class Repository:
    def __init__(self, root: str):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise AgentError("Select a local workspace folder.")
        self.sources: dict[str, Source] = {}
        self.coverage = {"files": 0, "bytes": 0, "excluded": 0, "skipped": 0, "limited": False}

    def scan(self) -> None:
        try:
            from pathspec import GitIgnoreSpec
        except ImportError as exc:
            raise AgentError(
                "Install the editor dependencies: pip install -e '.[editor]'."
            ) from exc
        visited = 0

        def walk(directory: Path, inherited: list) -> None:
            nonlocal visited
            if self.coverage["limited"]:
                return
            rules = list(inherited)
            ignore_path = directory / ".gitignore"
            if ignore_path.exists():
                try:
                    name = ignore_path.relative_to(self.root).as_posix()
                    rules.append(
                        (
                            directory,
                            GitIgnoreSpec.from_lines(
                                decode(
                                    read_bytes(self.root, name, 32768, internal=True)
                                ).splitlines()
                            ),
                        )
                    )
                except (AgentError, ValueError) as exc:
                    raise AgentError(
                        "Cannot safely parse .gitignore; repository scan stopped."
                    ) from exc
            try:
                children = entries(self.root, directory)
            except OSError:
                self.coverage["skipped"] += 1
                return
            for child_name, is_dir, is_link in children:
                item = directory / child_name
                visited += 1
                if (
                    visited > 20000
                    or self.coverage["files"] >= MAX_FILES
                    or self.coverage["bytes"] >= MAX_TOTAL
                ):
                    self.coverage["limited"] = True
                    return
                if is_link:
                    self.coverage["excluded"] += 1
                    continue
                ignored = False
                for base, spec in rules:
                    relative = item.relative_to(base).as_posix() + ("/" if is_dir else "")
                    match = spec.check_file(relative)
                    if match.include is not None:
                        ignored = match.include
                if (
                    ignored
                    or item.name in EXCLUDED_DIRS
                    or (item.name.startswith(".") and item.name != ".github")
                ):
                    self.coverage["excluded"] += 1
                    continue
                if is_dir:
                    walk(item, rules)
                    continue
                name = item.relative_to(self.root).as_posix()
                try:
                    data = read_bytes(self.root, name)
                    text = decode(data)
                    if self.coverage["bytes"] + len(data) > MAX_TOTAL:
                        self.coverage["limited"] = True
                        return
                except AgentError:
                    self.coverage["skipped"] += 1
                    continue
                self.sources[name] = Source(name, text, digest(data))
                self.coverage["files"] += 1
                self.coverage["bytes"] += len(data)

        walk(self.root, [])
        if not self.sources:
            raise AgentError("No eligible readable text files were found in this workspace.")

    def retrieve(self, query: str, active: str | None = None, limit: int = 6) -> list[dict]:
        query_terms = tokens(query)
        chunks = []
        for source in self.sources.values():
            lines = source.text.splitlines()
            for offset in range(0, len(lines), 35):
                excerpt_lines = lines[offset : offset + 45]
                # Cut only at line boundaries, and reject extremely long individual lines.
                while excerpt_lines and len("\n".join(excerpt_lines).encode()) > 1500:
                    excerpt_lines.pop()
                if not excerpt_lines:
                    continue
                excerpt = "\n".join(excerpt_lines)
                words = tokens(excerpt)
                score = len(query_terms & words) * 3 + len(query_terms & tokens(source.path)) * 6
                score += 8 if source.path == active else 0
                if source.path.lower().endswith(("readme.md", "pyproject.toml", "package.json")):
                    score += 2
                score /= 1 + math.log1p(len(words)) / 10
                chunks.append((score, source.path, offset, excerpt_lines))
        chunks.sort(key=lambda c: (-c[0], c[1], c[2]))
        selected = []
        per_file: dict[str, int] = {}
        total = 0
        for _, name, offset, lines in chunks:
            if per_file.get(name, 0) >= 2:
                continue
            excerpt = "\n".join(lines)
            if total + len(excerpt.encode()) > 6500:
                continue
            selected.append(
                {
                    "id": f"S{len(selected) + 1}",
                    "path": name,
                    "start_line": offset + 1,
                    "end_line": offset + len(lines),
                    "text": excerpt,
                    "sha256": self.sources[name].sha256,
                }
            )
            total += len(excerpt.encode())
            per_file[name] = per_file.get(name, 0) + 1
            if len(selected) >= limit:
                break
        if not selected:
            raise AgentError("No bounded text excerpts are available for this request.")
        return selected
