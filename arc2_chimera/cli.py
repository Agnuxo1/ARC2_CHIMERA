"""arc2-chimera command-line interface.

The CLI is intentionally minimal. `info` prints the honest project status;
`evaluate` runs a single ARC task through the v10 engine if available and
otherwise falls back to an identity baseline (so the command never pretends
to solve anything it cannot).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import DISCLAIMER, __version__, get_status
from .task_loader import load_task


def _cmd_info(_: argparse.Namespace) -> int:
    st = get_status()
    print(f"arc2-chimera v{st['version']}")
    print(f"status: {st['status']}")
    lo, hi = st["benchmark_accuracy_range"]
    print(f"measured ARC-AGI accuracy range: {lo*100:.2f}% - {hi*100:.2f}%")
    print(f"ARC Prize submission: {st['arc_prize_submission']}")
    print("")
    print(DISCLAIMER)
    print("")
    print("See PROJECT_STATUS.md at the repository root for details.")
    return 0


def _identity_predict(task: dict) -> list:
    """Fallback predictor: returns input grid as output. Honest baseline."""
    if "test" in task and isinstance(task["test"], list):
        return [{"output": pair["input"]} for pair in task["test"]]
    # challenge file form
    return {
        tid: [{"output": pair["input"]} for pair in t["test"]]
        for tid, t in task.items()
    }


def _cmd_evaluate(args: argparse.Namespace) -> int:
    task = load_task(args.task_file)
    try:
        # Best-effort import of the real engine. Not required for the CLI to work.
        from chimera_v10_0 import solve_arc_task  # type: ignore
        if "train" in task and "test" in task:
            result = solve_arc_task(task)
        else:
            result = {tid: solve_arc_task(t) for tid, t in task.items()}
        engine = "chimera_v10"
    except Exception as e:  # noqa: BLE001
        print(f"[arc2-chimera] engine unavailable ({e!r}); using identity baseline",
              file=sys.stderr)
        result = _identity_predict(task)
        engine = "identity-baseline"

    payload = {
        "engine": engine,
        "disclaimer": DISCLAIMER,
        "predictions": result,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {args.output} (engine={engine})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="arc2-chimera",
        description=(
            "Research proof-of-concept. ~2-5% accuracy on ARC-AGI. "
            "NOT an ARC Prize submission."
        ),
    )
    p.add_argument("--version", action="version", version=f"arc2-chimera {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    info = sub.add_parser("info", help="print project status and disclaimer")
    info.set_defaults(func=_cmd_info)

    ev = sub.add_parser("evaluate", help="run one ARC task through the engine")
    ev.add_argument("--task-file", required=True, help="path to ARC-format JSON")
    ev.add_argument("--output", required=True, help="where to write predictions JSON")
    ev.set_defaults(func=_cmd_evaluate)

    return p


def main(argv: list[str] | None = None) -> int:
    # Ensure stdout can carry unicode on Windows consoles.
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
