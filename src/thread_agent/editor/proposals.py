"""Deterministic, snapshot-bound edit proposals; this module never writes source files."""

from pathlib import Path

from thread_agent.domain.records import AgentError, canonical, digest
from thread_agent.editor.workspace import MAX_FILE, Repository, read_bytes, safe_relative


def proposal(repository: Repository, changes: list[dict], sources: list[dict]) -> dict | None:
    if not changes:
        return None
    if len(changes) > 4:
        raise AgentError("A proposal may change at most four files.")
    files = []
    seen = set()
    for change in changes:
        if not isinstance(change, dict) or set(change) != {"path", "old_text", "new_text"}:
            raise AgentError("Invalid edit schema.")
        name, old, new = (change[key] for key in ("path", "old_text", "new_text"))
        if not all(isinstance(value, str) for value in (name, old, new)):
            raise AgentError("Edit fields must be strings.")
        safe_relative(name)
        if name in seen or not new or len(new.encode()) > MAX_FILE:
            raise AgentError("Duplicate, empty or oversized edit.")
        seen.add(name)
        existing = repository.sources.get(name)
        if existing:
            if not old or existing.text.count(old) != 1:
                raise AgentError(
                    f"Edit in {name} does not match exactly one captured source range."
                )
            # Require the match to be visible to the model, not invented from an unread region.
            if not any(source["path"] == name and old in source["text"] for source in sources):
                raise AgentError("Edit target was not present in the supplied source excerpts.")
            after = existing.text.replace(old, new, 1)
            before = existing.text
        else:
            if old:
                raise AgentError("New files must have empty old_text.")
            target = repository.root / name
            parent = target.parent
            if (
                not parent.is_dir()
                or parent.resolve() != parent
                or target.exists()
                or target.is_symlink()
            ):
                raise AgentError("New-file parent must exist without links; target must not exist.")
            # Use the same ignore policy as discovery by checking the parent and new filename.
            check_new_path(repository.root, name)
            before, after = None, new
        if after == before or len(after.encode()) > MAX_FILE:
            raise AgentError("Edit has no effect or produces an oversized file.")
        files.append({"path": name, "before": before, "after": after})
    value = {
        "schema_version": "editor-proposal-v1",
        "root": str(repository.root),
        "files": files,
        "dependencies": {s["path"]: s["sha256"] for s in sources},
    }
    return {**value, "id": digest(canonical(value).encode())}


def check_new_path(root: Path, name: str) -> None:
    from pathspec import GitIgnoreSpec

    directory = root
    parts = safe_relative(name).parts
    rules = []
    for index, part in enumerate(parts):
        ignore = directory / ".gitignore"
        if ignore.exists() or ignore.is_symlink():
            data = read_bytes(root, ignore.relative_to(root).as_posix(), 32768, internal=True)
            rules.append((index, GitIgnoreSpec.from_lines(data.decode("utf-8").splitlines())))
        ignored = False
        is_directory = index < len(parts) - 1
        for base, spec in rules:
            relative = "/".join(parts[base : index + 1]) + ("/" if is_directory else "")
            match = spec.check_file(relative)
            if match.include is not None:
                ignored = match.include
        if ignored:
            raise AgentError(
                "Cannot create an ignored source file or descend into an ignored directory."
            )
        if is_directory:
            directory /= part
            if directory.is_symlink() or not directory.is_dir():
                raise AgentError("New-file parent is unavailable or linked.")


def validate(root: str, value: dict) -> dict:
    expected_id = value.get("id")
    body = {key: val for key, val in value.items() if key != "id"}
    if digest(canonical(body).encode()) != expected_id:
        raise AgentError("Proposal content changed; request a new proposal.")
    repository = Repository(root)
    if str(repository.root) != value.get("root"):
        raise AgentError("Proposal belongs to another workspace.")
    repository.scan()
    for name, sha in value["dependencies"].items():
        source = repository.sources.get(name)
        if source is None or source.sha256 != sha:
            raise AgentError(
                "A source dependency changed or became excluded; regenerate the proposal."
            )
    for file in value["files"]:
        safe_relative(file["path"])
        current = repository.sources.get(file["path"])
        if file["before"] is None:
            target = repository.root / file["path"]
            check_new_path(repository.root, file["path"])
            if target.exists() or target.is_symlink():
                raise AgentError("A proposed new file already exists.")
        elif current is None or current.text != file["before"]:
            raise AgentError("An edit target changed; regenerate the proposal.")
    return {"valid": True, "id": expected_id}
