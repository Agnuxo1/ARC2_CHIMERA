"""ARC-format task loader (pure Python, no GPU required)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_task(path: str | Path) -> dict[str, Any]:
    """Load a single ARC task JSON from disk.

    Accepts either:
      - {"train": [...], "test": [...]}              (single-task format)
      - {"<task_id>": {"train": [...], "test": [...]}, ...}  (challenge file)
    Returns the dict as-is after validation.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    validate_task(data)
    return data


def validate_task(data: dict[str, Any]) -> None:
    """Raise ValueError if the structure does not look like ARC."""
    if not isinstance(data, dict):
        raise ValueError("ARC task must be a JSON object")

    if "train" in data and "test" in data:
        _validate_single(data)
        return

    # challenge-file form: dict of task_id -> task
    if not data:
        raise ValueError("Empty ARC challenge file")
    for task_id, task in data.items():
        if not isinstance(task, dict) or "train" not in task or "test" not in task:
            raise ValueError(f"Task {task_id!r} missing train/test keys")
        _validate_single(task)


def _validate_single(task: dict[str, Any]) -> None:
    for split in ("train", "test"):
        if not isinstance(task.get(split), list):
            raise ValueError(f"ARC task {split!r} must be a list")
        for i, pair in enumerate(task[split]):
            if "input" not in pair:
                raise ValueError(f"ARC task {split}[{i}] missing 'input'")
