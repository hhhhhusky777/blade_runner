"""Process isolation and portable corpus identity; no real network operations."""

from collections.abc import Callable
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from solver import runner
from solver.api import validate_plan

FIXTURES = Path(__file__).parent / "fixtures"


class PackageBoundaryTests(unittest.TestCase):
    def test_all_saved_task_witnesses_and_bindings(self) -> None:
        """Bind all 93 observed tasks to their saved inputs and replay every witness."""
        corpus = json.loads((FIXTURES / "server-regressions.json").read_text())
        self.assertEqual(len(corpus["tasks"]), 93)
        self.assertEqual(len(corpus["inputs"]), 92)
        self.assertEqual(
            {stage: sum(r["stage"] == stage for r in corpus["tasks"]) for stage in (1, 2, 3)},
            {1: 19, 2: 36, 3: 38},
        )
        self.assertEqual(len({r["task_id"] for r in corpus["tasks"]}), 93)
        self.assertEqual(sum(r["counted"] for r in corpus["tasks"]), 88)
        replay: Callable[[object, object, str], object]
        for row in corpus["tasks"]:
            level = corpus["inputs"][row["input_sha256"]]
            digest = hashlib.sha256(
                json.dumps(level, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            self.assertEqual(digest, row["input_sha256"])
            if row["stage"] == 1:
                validate_plan(level, row["witness"], 1)
            else:
                if row["stage"] == 2:
                    from solver.stage2_reference import validate_plan as replay
                else:
                    from solver.stage3_reference import validate_plan as replay
                for mode in ("matching", "unrestricted"):
                    replay(level, row["witness"], mode)
        self.assertEqual(len(corpus["historical_stops"]), 3)

    def test_child_denies_network_only_after_explicit_entry(self) -> None:
        """Leave imports inert, then forbid sockets inside the isolated solver process."""
        script = """import io,json,socket,sys
from solver import child
original=socket.socket
assert original is not child.no_network
def test_solve(*args: object, **kwargs: object) -> dict[str, object]:
    '''Assert that the child blocks both socket creation entry points.'''
    for operation in (socket.socket,socket.create_connection):
        try:operation()
        except RuntimeError:pass
        else:raise AssertionError('child allowed socket creation')
    return {'status':'INFEASIBLE','plan':None}
child.solve=test_solve
sys.stdin=io.StringIO(json.dumps({'level':{},'seconds':1}))
child.main()
"""
        subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)

    def test_parent_strips_tokens_and_uses_an_isolated_module(self) -> None:
        """Exclude game credentials from the child environment and use its fixed entry point."""
        result = subprocess.CompletedProcess(
            [], 0, json.dumps({"status": "INFEASIBLE", "plan": None}), ""
        )
        with patch.dict(
            os.environ, {"GAME_SERVER_TOKEN": "private-test", "ARBITER_TOKEN": "private-test"}
        ):
            # Patch the runner's private subprocess import to inspect the child boundary.
            with patch.object(runner.subprocess, "run", return_value=result) as invoke:  # type: ignore[attr-defined]
                runner.solve_local({}, seconds=1)
                args, kwargs = invoke.call_args
                self.assertEqual(args[0][1:], ["-m", "solver.child"])
                self.assertNotIn("GAME_SERVER_TOKEN", kwargs["env"])
                self.assertNotIn("ARBITER_TOKEN", kwargs["env"])
                self.assertEqual(kwargs["cwd"], runner.APP_ROOT)

    def test_offline_cli_accepts_original_task_json_on_stdin(self) -> None:
        """Accept original task JSON through the public CLI and replay the returned plan."""
        case = json.loads((runner.ROOT / "samples.json").read_text())["3"]
        done = subprocess.run(
            [sys.executable, "-m", "solver", "--stage", "3", "--seconds", "5"],
            input=json.dumps(case["level"]),
            capture_output=True,
            text=True,
            check=True,
        )
        result = json.loads(done.stdout)
        self.assertEqual(result["status"], "FEASIBLE")
        validate_plan(case["level"], result["plan"], 3)
