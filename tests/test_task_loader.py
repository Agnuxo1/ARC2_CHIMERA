import json
from pathlib import Path

import pytest

from arc2_chimera.task_loader import load_task, validate_task

SYNTHETIC_TASK = {
    "train": [
        {"input": [[0, 1], [1, 0]], "output": [[1, 0], [0, 1]]},
    ],
    "test": [
        {"input": [[0, 0], [1, 1]]},
    ],
}


def test_load_synthetic_task(tmp_path: Path):
    p = tmp_path / "task.json"
    p.write_text(json.dumps(SYNTHETIC_TASK), encoding="utf-8")
    loaded = load_task(p)
    assert loaded["train"][0]["output"] == [[1, 0], [0, 1]]


def test_load_challenge_file(tmp_path: Path):
    challenge = {"abc123": SYNTHETIC_TASK}
    p = tmp_path / "ch.json"
    p.write_text(json.dumps(challenge), encoding="utf-8")
    loaded = load_task(p)
    assert "abc123" in loaded


def test_validate_rejects_garbage():
    with pytest.raises(ValueError):
        validate_task({"train": "not-a-list", "test": []})
