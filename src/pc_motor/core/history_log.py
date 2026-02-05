from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def make_envelope(kind: str, snapshot: dict[str, Any], meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a history envelope for JSONL persistence."""
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "meta": meta or {},
        "snapshot": snapshot,
    }


def append_jsonl(path: str | Path, envelope: dict[str, Any]) -> None:
    """Append one envelope as a line-delimited JSON record."""
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(envelope, ensure_ascii=False) + "\n")


def _read_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []

    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        # Be compatible with older doctor/report payloads.
        for key in ("snapshots", "history", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return value

    raise ValueError(f"Unsupported JSON history format in {path}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []

    snapshots: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if isinstance(item, dict) and isinstance(item.get("snapshot"), dict):
                snapshots.append(item["snapshot"])
            elif isinstance(item, dict):
                snapshots.append(item)
            else:
                raise ValueError(f"Invalid JSONL record in {path}")
    return snapshots


def read_history_auto(path: str | Path) -> tuple[str, list[dict[str, Any]]]:
    """Read `.json` and `.jsonl` history and normalize to snapshot list."""
    history_path = Path(path)
    suffix = history_path.suffix.lower()

    if suffix == ".jsonl":
        return "jsonl", _read_jsonl(history_path)
    if suffix == ".json":
        return "json", _read_json(history_path)

    raise ValueError(
        f"Unsupported history format for {history_path}. Use .json or .jsonl history files."
    )
