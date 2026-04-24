import json
from pathlib import Path

from arc2_chimera.cli import main


def test_cli_info_prints_disclaimer(capsys):
    rc = main(["info"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "NOT an ARC Prize submission" in out
    assert "research-proof-of-concept" in out


def test_cli_evaluate_identity_fallback(tmp_path: Path, capsys):
    task = {
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [{"input": [[1, 2], [3, 4]]}],
    }
    tf = tmp_path / "t.json"
    tf.write_text(json.dumps(task), encoding="utf-8")
    out = tmp_path / "out.json"
    rc = main(["evaluate", "--task-file", str(tf), "--output", str(out)])
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["engine"] in ("chimera_v10", "identity-baseline")
    assert "NOT an ARC Prize submission" in payload["disclaimer"]
    assert payload["predictions"]  # non-empty


def test_cli_help_runs():
    try:
        main(["--help"])
    except SystemExit as e:
        assert e.code == 0
