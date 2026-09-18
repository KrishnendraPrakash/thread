"""Versioned records for the experimental direct-field workflow."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime


class AgentError(Exception):
    """A bounded failure that can be explained without a traceback."""


def canonical(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class Evidence:
    path: str
    text: str
    sha256: str
    observed_at: str

    def record(self) -> dict:
        return asdict(self)
