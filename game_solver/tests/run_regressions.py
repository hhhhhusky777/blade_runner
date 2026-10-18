"""Run portable regressions; optionally compare an owner-held research checkout.

From game_solver: python -m tests.run_regressions --suite all --output results.json
The official package never imports this test driver or reads expected labels.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

FIXTURES = Path(__file__).resolve().parent / "fixtures"
APP_ROOT = FIXTURES.parent.parent


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def cases(suite):
    """Keep every observed task association, including repeated inputs."""
    values = []
    if suite in ("all", "server"):
        corpus = json.loads((FIXTURES / "server-regressions.json").read_text())
        values += [
            dict(
                id=row["task_id"],
                suite="server",
                stage=row["stage"],
                level=corpus["inputs"][row["input_sha256"]],
                expected_status=row["expected_status"],
                relay_mode="matching",
            )
            for row in corpus["tasks"]
        ]
    for stage in (1, 2, 3):
        if suite not in ("all", f"stage{stage}"):
            continue
        rows = json.loads((FIXTURES / f"stage{stage}-controls.json").read_text())["cases"]
        values += [dict(row, suite=f"stage{stage}", stage=stage) for row in rows]
    return values


def worker(request, reference_root=None):
    """One solve per fresh child; research side effects never reach the driver."""
    stage = request["stage"]
    mode = request.get("relay_mode", "matching")
    options = dict(seconds=request["seconds"])
    if reference_root:
        # This optional, test-only adapter is not part of the solver import path.
        sys.path.insert(0, str(reference_root))
        if stage == 1:
            from memory_benchmark import execute

            return execute({"level": request["level"]}, "both", **options)
        if stage == 2:
            from stage2 import solve
        else:
            from stage3 import solve
    else:
        if stage == 1:
            from solver.stage1_preset import solve
        elif stage == 2:
            from solver.stage2 import solve
        else:
            from solver.stage3 import solve
    if stage == 2:
        options.update(relay_mode=mode, guidance="both", max_states=None)
    elif stage == 3:
        options.update(relay_mode=mode, probes=request.get("probes", True))
    return solve(request["level"], **options)


def measure(case, seconds, reference_root=None):
    """Record actual outcomes; an outer timeout stays UNKNOWN and fails truth."""
    command = [sys.executable, "-m", "tests.run_regressions", "--worker"]
    if reference_root:
        command += ["--reference-root", str(reference_root)]
    environment = {
        k: v for k, v in os.environ.items() if k not in ("GAME_SERVER_TOKEN", "ARBITER_TOKEN")
    }
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = perf_counter()
    try:
        done = subprocess.run(
            command,
            input=json.dumps(dict(case, seconds=seconds)),
            capture_output=True,
            text=True,
            cwd=APP_ROOT,
            env=environment,
            timeout=seconds + 3,
            check=True,
        )
        result = json.loads(done.stdout)
    except subprocess.TimeoutExpired:
        result = dict(status="UNKNOWN", reason="outer_timeout", plan=None)
    return result, perf_counter() - started


def semantic(result):
    """Compare deterministic results and work; elapsed clock fields are excluded."""
    if isinstance(result, dict):
        return {k: semantic(v) for k, v in result.items() if "second" not in k}
    if isinstance(result, list):
        return [semantic(v) for v in result]
    return result


def replay(case, plan):
    """Use raw actions on the original input, independently of search internals."""
    stage = case["stage"]
    if stage == 1:
        from solver.reference import validate_plan

        validate_plan(case["level"], plan)
        return ["stone"]
    if stage == 2:
        from solver.stage2_reference import validate_plan
    else:
        from solver.stage3_reference import validate_plan
    modes = (
        ("matching", "unrestricted")
        if case.get("relay_mode", "matching") == "matching"
        else ("unrestricted",)
    )
    for mode in modes:
        validate_plan(case["level"], plan, mode)
    return list(modes)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite", choices=("all", "server", "stage1", "stage2", "stage3"), default="all"
    )
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--case", action="append", help="run only these exact case/task IDs")
    parser.add_argument(
        "--reference-root", type=Path, help="optional original research source directory"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    reference = args.reference_root.resolve() if args.reference_root else None
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin), reference)))
        return 0
    selected = cases(args.suite)
    if args.case:
        requested = set(args.case)
        selected = [c for c in selected if c["id"] in requested]
        if {c["id"] for c in selected} != requested:
            parser.error("one or more requested case IDs are absent")
    report = dict(
        scope="Local migration validation, not live progression or a universal timing guarantee.",
        seconds_per_solve=args.seconds,
        reference_enabled=bool(reference),
        complete=False,
        rows=[],
    )
    for index, case in enumerate(selected, 1):
        result, elapsed = measure(case, args.seconds)
        modes = replay(case, result["plan"]) if result.get("plan") is not None else []
        row = dict(
            id=case["id"],
            suite=case["suite"],
            stage=case["stage"],
            input_sha256=digest(case["level"]),
            status=result["status"],
            reason=result["reason"],
            expected_status=case["expected_status"],
            elapsed_seconds=elapsed,
            replayed_modes=modes,
            expanded=result.get("expanded"),
            plan_sha256=digest(result["plan"]) if result.get("plan") is not None else None,
            passed=result["status"] == case["expected_status"],
        )
        if reference:
            old, old_elapsed = measure(case, args.seconds, reference)
            if old.get("plan") is not None:
                replay(case, old["plan"])
            row.update(
                reference_status=old["status"],
                reference_elapsed_seconds=old_elapsed,
                same_plan_and_semantic_counters=semantic(old) == semantic(result),
            )
            row["passed"] &= row["same_plan_and_semantic_counters"]
        report["rows"].append(row)
        if args.output:
            args.output.write_text(json.dumps(report, indent=2) + "\n")
        if index % 20 == 0 or not row["passed"]:
            print(index, "/", len(selected), case["id"], row["status"], row["passed"], flush=True)
    report.update(
        complete=True, passed=sum(r["passed"] for r in report["rows"]), total=len(selected)
    )
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
