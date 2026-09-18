"""Bounded, explicitly selected source reads; no model-selected paths or writes."""

import os
import stat
from pathlib import Path, PurePosixPath

from thread_agent.domain.records import AgentError, Evidence, digest, now

MAX_BYTES = 32_768


def read_source(workspace: str, name: str) -> Evidence:
    path = PurePosixPath(name)
    if (
        path.is_absolute()
        or not path.parts
        or any(part.startswith(".") or "\\" in part for part in path.parts)
        or path.suffix.lower() not in {".json", ".toml"}
    ):
        raise AgentError("Select a relative, non-hidden .toml or .json file inside the workspace.")
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise AgentError("Secure source reads currently require macOS or Linux.")
    descriptors = []
    try:
        root = Path(workspace).resolve(strict=True)
        descriptors.append(os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW))
        for part in path.parts[:-1]:
            descriptors.append(
                os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptors[-1])
            )
        fd = os.open(
            path.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptors[-1]
        )
        descriptors.append(fd)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise AgentError("Source must be a regular file with no hard links or symlinks.")
        if before.st_size > MAX_BYTES:
            raise AgentError(f"Source exceeds the {MAX_BYTES}-byte limit; select a smaller file.")
        chunks = []
        remaining = MAX_BYTES + 1
        while remaining:
            chunk = os.read(fd, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(fd)
        if len(data) > MAX_BYTES or (before.st_size, before.st_mtime_ns) != (
            after.st_size,
            after.st_mtime_ns,
        ):
            raise AgentError("Source changed during reading or exceeded its size limit. Try again.")
        return Evidence(path.as_posix(), data.decode("utf-8"), digest(data), now())
    except (OSError, UnicodeError) as exc:
        raise AgentError(
            "Cannot read source: check its path, permissions, UTF-8, and symlinks."
        ) from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)
