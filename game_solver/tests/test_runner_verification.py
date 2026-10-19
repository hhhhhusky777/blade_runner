"""Verification and CLI failure boundaries; fake clients only, no network."""

from __future__ import annotations

from contextlib import redirect_stdout
from typing import Any, Literal, cast
from copy import deepcopy
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest

from api_client.client import GameClient
from api_client.models import StageCapabilitiesResponse
from solver import runner as live_attempt
from tests import test_runner_attempt
from tests.test_runner_attempt import FakeClient, Response


def task(**changes: Any) -> dict[str, Any]:
    """Build valid task flags and apply deliberately malformed test overrides."""
    return (
        dict(
            id="one",
            type="level1",
            passed=True,
            passed_first_try=True,
            solved_at_all=True,
            solved_first_try_in_time=True,
            attempts_count=1,
            pass_time_taken_ms=1318,
        )
        | changes
    )


class ReadClient(FakeClient):
    def __init__(
        self,
        tasks: list[dict[str, Any]] | None = None,
        progress_error: bool = False,
    ) -> None:
        """Prepare controlled task readback and optional progress failure."""
        super().__init__()
        self.tasks = tasks if tasks is not None else [task()]
        self.progress_error = progress_error
        self.reads: list[str] = []

    def __enter__(self) -> ReadClient:
        """Expose the fake client through the production context-manager path."""
        return self

    def __exit__(self, *args: object) -> Literal[False]:
        """Leave the fake client context without suppressing exceptions."""
        return False

    def get_tasks(self, stage: int) -> Response:  # type: ignore[override]  # Exercise the legacy read-only fake.
        """Return fake task flags used for independent result verification."""
        self.reads.append("tasks")
        return Response(ok=True, tasks=[Response(**t) for t in self.tasks])

    def get_stage_progress(self, stage: int) -> Response:
        """Return fake progression derived from the submission history."""
        self.reads.append("progress")
        if self.progress_error:
            raise TimeoutError("read unavailable")
        return Response(
            ok=True,
            current_index=1,
            order=["level1", "level2"],
            items=[
                {
                    "type": "level2",
                    "status": "in_progress",
                    "series_index": 0,
                    "series_total": 1,
                    "is_current": True,
                }
            ],
        )

    def get_stage_capabilities(self, stage: int) -> Response | StageCapabilitiesResponse:
        """Advertise the minimal Stage 1 rules required by preflight."""
        self.reads.append("capabilities")
        cap = Response(
            structures_details={
                "ROAD": Response(build_cost={"STONE": 1}),
                "STONE_QUARRY": Response(
                    build_cost={"STONE": 10}, rate=5, resource_allow=["STONE"]
                ),
            },
            actions={"BUILD": None, "MINE": None, "TRANSFER": None, "CLAIM_WIN": None},
        )
        return Response(ok=True, new=cap, available_capabilities=lambda: cap)


class VerificationTests(unittest.TestCase):
    def assess(self, entry: dict[str, Any] | None = None, **changes: Any) -> dict[str, Any]:
        """Assess one task fixture with optional report-level overrides."""
        return live_attempt.assess_result(
            dict(task_id="one", tasks_after=[task() if entry is None else entry]) | changes
        )

    def test_task_flags_own_counted_result(self) -> None:
        """Require consistent task flags before reporting advancement credit."""
        self.assertEqual(self.assess()["outcome"], "COUNTED")
        # Later attempts do not erase the server's recorded first-try result.
        self.assertEqual(self.assess(task(attempts_count=2))["outcome"], "COUNTED")
        for changes in (
            {"passed_first_try": False},
            {"solved_at_all": False},
            {"attempts_count": 0},
            {"attempts_count": None},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(self.assess(task(**changes))["outcome"], "UNKNOWN")
        for submission in ({"accepted": False}, {"ok": False}):
            self.assertEqual(self.assess(submit_result=submission)["outcome"], "UNKNOWN")

    def test_late_or_failed_plan_does_not_count(self) -> None:
        """Distinguish failed or late plans from verified advancement."""
        for passed in (False, True):
            entry = task(
                passed=passed,
                passed_first_try=passed,
                solved_at_all=passed,
                solved_first_try_in_time=False,
            )
            self.assertEqual(self.assess(entry)["outcome"], "NOT_COUNTED")
            self.assertEqual(
                self.assess(entry, submit_result={"accepted": True})["outcome"], "UNKNOWN"
            )

    def test_stale_missing_and_malformed_readback_is_unknown(self) -> None:
        """Keep incomplete or contradictory task readback explicitly unknown."""
        for entry in (
            task(passed=False, solved_first_try_in_time=False, attempts_count=0),
            {"id": "one"},
            {"id": "one", "passed": True},
            task(passed="true"),
            task(solved_first_try_in_time="true"),
        ):
            with self.subTest(entry=entry):
                self.assertEqual(self.assess(entry)["outcome"], "UNKNOWN")
        for rows in ([], [task(id="other")], [task(), task()]):
            self.assertEqual(self.assess(tasks_after=rows)["outcome"], "UNKNOWN")
        self.assertEqual(
            self.assess(tasks_verification_error_type="TimeoutError")["outcome"], "UNKNOWN"
        )

    def test_progress_is_separate_and_handles_same_level_series(self) -> None:
        """Track series movement separately from a task's validated result."""
        old: dict[str, Any] = {
            "current_index": 1,
            "items": [{"type": "level2", "series_index": 1, "status": "in_progress"}],
        }
        new: dict[str, Any] = {
            "current_index": 1,
            "items": [{"type": "level2", "series_index": 2, "status": "in_progress"}],
        }
        self.assertTrue(live_attempt.progress_changed(old, new, "level2"))
        self.assertFalse(live_attempt.progress_changed(old, old, "level2"))
        self.assertIsNone(live_attempt.progress_changed(None, new, "level2"))
        done = deepcopy(old)
        done["items"][0]["status"] = "done"
        self.assertTrue(live_attempt.progress_changed(old, done, "level2"))
        result = self.assess(
            task(
                passed=False,
                passed_first_try=False,
                solved_at_all=False,
                solved_first_try_in_time=False,
            ),
            progress_before={"current_index": 0},
            progress_after={"current_index": 1},
        )
        self.assertTrue(result["progress_changed"])
        self.assertEqual(result["outcome"], "NOT_COUNTED")

    def test_independent_reads_retain_task_proof(self) -> None:
        """Preserve task verification even when the independent progress read fails."""
        report: dict[str, Any] = {"task_id": "one"}
        client = ReadClient(progress_error=True)
        live_attempt.read_back(cast(GameClient, client), report)
        self.assertEqual(client.reads, ["tasks", "progress"])
        self.assertEqual(report["verification"]["outcome"], "COUNTED")
        self.assertIn("progress_verification_error_type", report)
        client = ReadClient()
        client.get_tasks = lambda stage: Response(ok=False, tasks=[Response(**task())])  # type: ignore[method-assign]  # Inject failed readback.
        report = {"task_id": "one"}
        live_attempt.read_back(cast(GameClient, client), report)
        self.assertEqual(report["verification"]["outcome"], "UNKNOWN")
        self.assertIn("progress_after", report)

    def test_ambiguous_submit_can_be_verified_without_retry(self) -> None:
        """Resolve a lost submission response using task readback rather than another POST."""
        client = FakeClient("submit")
        report, _ = test_runner_attempt.LiveAttemptTests().execute(client)
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual((client.creates, client.submits), (1, 1))
        client = ReadClient([task(passed=False, solved_first_try_in_time=False, attempts_count=0)])
        client.fail = "submit"
        report, _ = test_runner_attempt.LiveAttemptTests().execute(client)
        self.assertEqual(report["outcome"], "UNKNOWN")
        self.assertEqual((client.creates, client.submits), (1, 1))

    def test_accepted_response_does_not_override_stale_get(self) -> None:
        """Require fresh task evidence even when a submission response says accepted."""
        client = ReadClient([task(passed=False, solved_first_try_in_time=False, attempts_count=0)])
        report, _ = test_runner_attempt.LiveAttemptTests().execute(client)
        self.assertTrue(report["submit_result"]["accepted"])
        self.assertEqual(report["outcome"], "UNKNOWN")
        self.assertEqual((client.creates, client.submits), (1, 1))

    def invoke(self, args: list[str], client: ReadClient) -> tuple[int, str]:
        """Run the CLI with isolated environment values and capture its output."""
        token = 'fake-quote-"-slash-\\-token'
        keys = ("GAME_SERVER_TOKEN", "GAME_SERVER_BASE_URL", "ARBITER_TOKEN", "ARBITER_BASE_URL")
        saved = {key: os.environ.pop(key, None) for key in keys}
        output = StringIO()
        try:
            with tempfile.TemporaryDirectory() as directory:
                env = Path(directory) / ".env"
                env.write_text("GAME_SERVER_BASE_URL=http://172.237.120.135/\n")
                os.environ["GAME_SERVER_TOKEN"] = token

                def factory(base: str, secret: str, timeout: float) -> GameClient:
                    """Verify CLI client configuration and return the fake client."""
                    self.assertEqual(secret, token)
                    self.assertEqual(timeout, 3.0)
                    return cast(GameClient, client)

                with redirect_stdout(output):
                    code = live_attempt.main(["--env", str(env), *args], client_factory=cast(live_attempt.ClientFactory, factory))
        finally:
            for key in keys:
                os.environ.pop(key, None)
                if saved[key] is not None:
                    os.environ[key] = cast(str, saved[key])
        return code, output.getvalue()

    def test_verify_is_get_only_and_has_no_progress_baseline(self) -> None:
        """Verify an existing task without writes or an invented progress baseline."""
        client = ReadClient()
        code, output = self.invoke(["--verify", "one", "--json"], client)
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertIsNone(report["verification"]["progress_changed"])
        self.assertEqual(client.reads, ["tasks", "progress"])
        self.assertEqual((client.creates, client.submits), (0, 0))

    def test_default_readiness_is_get_only(self) -> None:
        """Keep the default readiness command free of task creation and submission."""
        client = ReadClient()
        code, output = self.invoke([], client)
        self.assertEqual(code, 0)
        self.assertIn("READY:", output)
        self.assertEqual(client.reads, ["capabilities", "progress", "tasks"])
        self.assertEqual((client.creates, client.submits), (0, 0))

    def test_verify_exit_codes_distinguish_failure_and_uncertainty(self) -> None:
        """Expose failed, unknown and stopped outcomes through distinct exit codes."""
        for entries, expected in (
            ([task(passed=True, solved_first_try_in_time=False)], 1),
            ([], 3),
        ):
            client = ReadClient(entries)
            code, _ = self.invoke(["--verify", "one"], client)
            self.assertEqual(code, expected)
            self.assertEqual((client.creates, client.submits), (0, 0))
        self.assertEqual(live_attempt.exit_code({"outcome": "STOPPED"}), 2)

    def test_modes_are_exclusive_before_any_client_access(self) -> None:
        """Reject conflicting CLI modes before constructing a client."""
        output = StringIO()
        from contextlib import redirect_stderr

        with redirect_stderr(output), self.assertRaises(SystemExit) as caught:
            live_attempt.main(
                ["--verify", "one", "--submit-one"], client_factory=cast(live_attempt.ClientFactory, lambda *a: self.fail("network"))
            )
        self.assertEqual(caught.exception.code, 2)

    def test_conflicting_negative_flags_remain_unknown(self) -> None:
        """Reject contradictory or mistyped negative task flags as uncertain."""
        for entry in (
            task(passed=False, passed_first_try=True, solved_first_try_in_time=False),
            task(passed=True, solved_at_all=False, solved_first_try_in_time=False),
            task(passed=False, passed_first_try=False, solved_first_try_in_time=True),
            task(passed=False, passed_first_try="false", solved_first_try_in_time=False),
        ):
            self.assertEqual(self.assess(entry)["outcome"], "UNKNOWN")

    def test_checkpoint_failure_preserves_reconciliation_without_another_post(self) -> None:
        """Retain readback evidence when receipt writing fails without repeating writes."""
        for failure_phase, counts in (
            ("select_task", (0, 0)),
            ("reading_task", (1, 0)),
            ("submitted", (1, 1)),
            ("stopped", (1, 1)),
        ):
            client = FakeClient("submit" if failure_phase == "stopped" else None)

            def save(report: dict[str, Any]) -> None:
                """Raise at the selected checkpoint phase to exercise persistence failure."""
                if report["phase"] == failure_phase:
                    raise OSError("disk unavailable")

            report = live_attempt.attempt(
                cast(GameClient, client),
                {"pending_task_ids": [], "listed_task_ids": []},
                save,
                lambda *args: {"status": "FEASIBLE", "plan": client.plan},
            )
            self.assertEqual((client.creates, client.submits), counts)
            self.assertEqual(report["checkpoint_error_type"], "OSError")
            self.assertIn("tasks_after", report)
            self.assertIn("progress_after", report)
            self.assertEqual(report["outcome"], "COUNTED" if counts[1] else "STOPPED")
            if counts[0]:
                self.assertEqual(report["task_id"], "one")
            output = StringIO()
            with redirect_stdout(output):
                live_attempt.display(report)
            self.assertIn("Receipt write failed", output.getvalue())

    def test_redaction_precedes_json_encoding(self) -> None:
        """Remove secrets containing escaping characters before JSON serialization."""
        token = 'quote-"-slash-\\-newline-\n-token'
        payload = {token: [token, {"value": "prefix " + token + " suffix"}]}
        encoded = json.dumps(live_attempt.redact(payload, token))
        self.assertNotIn(json.dumps(token)[1:-1], encoded)
        self.assertEqual(
            json.loads(encoded),
            {"[REDACTED]": ["[REDACTED]", {"value": "prefix [REDACTED] suffix"}]},
        )
