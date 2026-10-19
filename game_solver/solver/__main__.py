"""Offline JSON entry point: python -m solver --stage 3 input.json."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import sys

from .api import solve


def main(argv: Sequence[str] | None = None) -> int:
    """Solve JSON from a file or stdin; return zero only for a validated plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="task JSON; stdin if omitted")
    parser.add_argument("--stage", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--seconds", type=float, default=24.0)
    args = parser.parse_args(argv)
    level = json.loads(args.input.read_text()) if args.input else json.load(sys.stdin)
    result = solve(level, args.stage, args.seconds)
    print(json.dumps(result))
    return 0 if result["status"] == "FEASIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
