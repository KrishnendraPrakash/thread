"""Local session snapshots and append-only events with optimistic concurrency."""

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from thread_agent.domain.records import AgentError, canonical, now


class Store:
    def __init__(self, directory: Path):
        if directory.is_symlink():
            raise AgentError("State directory must not be a symlink.")
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.directory = directory.resolve()
        path = directory / "sessions.sqlite3"
        if path.is_symlink():
            raise AgentError("State database must not be a symlink.")
        self.db = sqlite3.connect(path, timeout=5)
        path.chmod(0o600)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(
            "CREATE TABLE IF NOT EXISTS sessions ("
            "id TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL);"
            "CREATE TABLE IF NOT EXISTS events ("
            "session_id TEXT REFERENCES sessions(id), seq INTEGER, body TEXT NOT NULL,"
            "PRIMARY KEY(session_id, seq));"
        )

    def close(self) -> None:
        self.db.close()

    def create(self, body: dict, events: list[dict]) -> dict:
        session = {**body, "id": uuid4().hex, "revision": 0, "created_at": now()}
        with self.db:
            self.db.execute(
                "INSERT INTO sessions VALUES (?, ?, ?)",
                (session["id"], 0, canonical(session)),
            )
            self._events(session["id"], events)
        return session

    def get(self, session_id: str) -> dict:
        row = self.db.execute("SELECT body FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise AgentError("Unknown session ID. Use 'thread-agent sessions' to list sessions.")
        return json.loads(row[0])

    def save(self, session: dict, events: list[dict]) -> dict:
        updated = {**session, "revision": session["revision"] + 1}
        with self.db:
            cursor = self.db.execute(
                "UPDATE sessions SET revision = ?, body = ? WHERE id = ? AND revision = ?",
                (updated["revision"], canonical(updated), session["id"], session["revision"]),
            )
            if cursor.rowcount != 1:
                raise AgentError("Session changed concurrently. Reload it before replying.")
            self._events(session["id"], events)
        return updated

    def _events(self, session_id: str, events: list[dict]) -> None:
        seq = self.db.execute(
            "SELECT COALESCE(MAX(seq), 0) FROM events WHERE session_id = ?", (session_id,)
        ).fetchone()[0]
        for event in events:
            seq += 1
            body = {"seq": seq, "at": now(), "producer": "deterministic", **event}
            self.db.execute(
                "INSERT INTO events VALUES (?, ?, ?)", (session_id, seq, canonical(body))
            )

    def trace(self, session_id: str) -> list[dict]:
        self.get(session_id)
        return [
            json.loads(row[0])
            for row in self.db.execute(
                "SELECT body FROM events WHERE session_id = ? ORDER BY seq", (session_id,)
            )
        ]

    def sessions(self) -> list[dict]:
        return [
            json.loads(row[0])
            for row in self.db.execute("SELECT body FROM sessions ORDER BY rowid")
        ]
