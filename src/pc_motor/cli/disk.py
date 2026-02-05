from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pc_motor.core.history_log import append_jsonl, make_envelope, read_history_auto


def _append_json_history(path: str | Path, snapshot: dict[str, Any]) -> None:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    if history_path.exists() and history_path.stat().st_size > 0:
        with history_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if isinstance(payload, list):
            snapshots = payload
        elif isinstance(payload, dict):
            snapshots = payload.get("snapshots", [])
            if not isinstance(snapshots, list):
                snapshots = []
        else:
            snapshots = []
    else:
        snapshots = []

    snapshots.append(snapshot)
    with history_path.open("w", encoding="utf-8") as fh:
        json.dump(snapshots, fh, ensure_ascii=False, indent=2)


def persist_disk_snapshot(history: str | Path, root: str, depth: int, snapshot: dict[str, Any]) -> None:
    """Persist a disk snapshot according to history extension."""
    history_path = Path(history)
    suffix = history_path.suffix.lower()

    if suffix == ".jsonl":
        envelope = make_envelope("disk", snapshot, meta={"root": root, "depth": depth})
        append_jsonl(history_path, envelope)
        return

    if suffix == ".json":
        _append_json_history(history_path, snapshot)
        return

    raise ValueError(f"Unsupported history extension: {history_path}. Use .json or .jsonl")


def load_snapshots_for_analysis(history_path: str | Path) -> list[dict[str, Any]]:
    """Load history for report/diff/advise commands using unified parser."""
    _, snaps = read_history_auto(history_path)
    if len(snaps) < 2:
        raise ValueError(
            "Need at least 2 snapshots in history to run disk report/diff/advise. "
            "Run disk scan multiple times first."
        )
    return snaps


def disk_report(history_path: str | Path) -> dict[str, Any]:
    snaps = load_snapshots_for_analysis(history_path)
    return {"count": len(snaps), "first": snaps[0], "last": snaps[-1]}


def disk_diff(history_path: str | Path) -> dict[str, Any]:
    snaps = load_snapshots_for_analysis(history_path)
    return {"before": snaps[-2], "after": snaps[-1]}


def disk_advise(history_path: str | Path) -> dict[str, Any]:
    snaps = load_snapshots_for_analysis(history_path)
    return {"snapshots": len(snaps), "advice": "review growing paths"}
