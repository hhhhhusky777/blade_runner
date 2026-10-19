"""One-attempt boundaries without making network requests."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any, cast
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from api_client.models import Action
from api_client.client import GameClient
from solver import runner as live_attempt


class Response(SimpleNamespace):
    def model_dump(self) -> dict[str, Any]:
        """Return the mutable namespace as a response-shaped mapping."""
        return vars(self)


class FakeClient:
    def __init__(self, fail: str | None = None) -> None:
        """Load a witness and initialize fake request counters."""
        self.fail = fail
        self.creates = self.submits = 0
        case = json.loads((live_attempt.ROOT / "samples.json").read_text())["1"]
        self.level, self.plan = case["level"], case["witness"]

    def request_next_task(self, stage: int, *, read_timeout: float | None = None) -> Response:
        """Simulate task creation and count each attempted request."""
        self.creates += 1
        if self.fail == "create":
            raise TimeoutError("response lost after create")
        return Response(ok=True, task_id="one")

    def get_task(self, stage: int, task_id: str) -> Response:
        """Return the saved level without contacting the server."""
        return Response(ok=True, id=task_id, level=Response(model_dump=lambda: self.level))

    def submit_plan(self, stage: int, task_id: str, plan: list[list[Action]]) -> Response:
        """Record one submission and return the configured fake result."""
        self.submits += 1
        if self.fail == "submit":
            raise TimeoutError("response lost after submit")
        return Response(ok=True, success=True, accepted=True)

    def get_stage_progress(self, stage: int) -> Response:
        """Return fake progression derived from the submission history."""
        return Response(ok=True, current_index=int(bool(self.submits)))

    def get_tasks(self, stage: int, *, timeout: float | None = None) -> Response:
        """Return fake task flags used for independent result verification."""
        return Response(
            ok=True,
            tasks=[
                Response(
                    id="one",
                    solved_at_all=bool(self.submits),
                    passed=bool(self.submits),
                    passed_first_try=bool(self.submits),
                    solved_first_try_in_time=bool(self.submits),
                    attempts_count=self.submits,
                )
            ],
        )


class LiveAttemptTests(unittest.TestCase):
    def execute(
        self,
        client: FakeClient,
        solver: Callable[[dict[str, Any], float], dict[str, Any]] | None = None,
        pending: list[str] | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Run one attempt with a fake client and capture immutable receipt snapshots."""
        records = []
        solver = solver or (lambda *a: {"status": "FEASIBLE", "plan": client.plan})
        report = live_attempt.attempt(
            cast(GameClient, client),
            {
                "pending_task_ids": pending or [],
                "listed_task_ids": [],
                "progress_before": {"current_index": 0},
            },
            lambda r: records.append(deepcopy(r)),
            solver,
        )
        return report, records

    def test_one_create_one_submit_and_verified_progress(self) -> None:
        """Verify one creation and submission advance only after server readback."""
        client = FakeClient()
        report, records = self.execute(client)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["phase"], "submitted")
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(report["progress_after"]["current_index"], 1)
        self.assertTrue(report["strict_replay"])
        self.assertTrue(any(r["phase"] == "submitting" for r in records))
        reused = FakeClient()
        report, _ = self.execute(reused, pending=["one"])
        self.assertEqual((reused.creates, reused.submits), (0, 0))
        self.assertEqual(report["phase"], "stopped")

    def test_unknown_and_invalid_plan_are_never_submitted(self) -> None:
        """Keep unknown answers and invalid plans away from the submission endpoint."""
        for result in (
            {"status": "UNKNOWN", "plan": None},
            {"status": "FEASIBLE", "plan": [[{"action": "CLAIM_WIN", "args": {"x": 0, "y": 0}}]]},
        ):
            client = FakeClient()
            report, _ = self.execute(client, lambda *a: result)
            self.assertEqual((client.creates, client.submits), (1, 0))
            self.assertEqual(report["phase"], "stopped")
            self.assertEqual(report["task_id"], "one")

    def test_uncertain_posts_are_not_retried_and_reads_reconcile(self) -> None:
        """Use readback to reconcile uncertain writes without repeating them."""
        for phase, counts in [("create", (1, 0)), ("submit", (1, 1))]:
            client = FakeClient(phase)
            report, _ = self.execute(client)
            self.assertEqual((client.creates, client.submits), counts)
            self.assertEqual(report["error_type"], "TimeoutError")
            self.assertEqual(report["phase"], "stopped")
            self.assertIn("progress_after", report)
            self.assertIn("tasks_after", report)

    def test_final_checkpoint_cannot_consume_submission_reserve(self) -> None:
        """Stop when receipt writing consumes the final submission reserve."""
        client = FakeClient()
        current = [0.0]
        saved = live_attempt.monotonic  # type: ignore[attr-defined]  # Patch the runner's imported clock.
        live_attempt.monotonic = lambda: current[0]  # type: ignore[attr-defined]  # Patch the runner's imported clock.

        def expensive_checkpoint(report: dict[str, Any]) -> None:
            """Advance the clock when the final receipt consumes the reserve."""
            if report["phase"] == "submitting":
                current[0] = 27.0

        try:
            report = live_attempt.attempt(
                cast(GameClient, client),
                {"pending_task_ids": [], "listed_task_ids": []},
                expensive_checkpoint,
                lambda *a: {"status": "FEASIBLE", "plan": client.plan},
            )
        finally:
            live_attempt.monotonic = saved  # type: ignore[attr-defined]  # Patch the runner's imported clock.
        self.assertEqual((client.creates, client.submits), (1, 0))
        self.assertEqual(report["error_type"], "TimeoutError")
        self.assertEqual(report["failed_phase"], "submitting")

    def test_live_missing_task_id_is_reconciled_without_a_second_post(self) -> None:
        """Recover an omitted task ID through inventory reads alone."""
        client = FakeClient()

        def request_without_known_id(stage: int, *, read_timeout: float | None = None) -> Response:
            """Simulate successful creation whose response omits the task ID."""
            client.creates += 1
            return Response(ok=True, task_id=None)

        client.request_next_task = request_without_known_id  # type: ignore[method-assign]  # Inject the transport response for this test.
        report, _ = self.execute(client)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["task_id"], "one")
        self.assertEqual(report["phase"], "submitted")
        self.assertIn("GET tasks difference", report["task_id_source"])

    def test_missing_id_stops_on_unsuccessful_or_ambiguous_get(self) -> None:
        """Stop when inventory reads cannot identify exactly one created task."""
        for ok, ids in [(False, ["new"]), (True, []), (True, ["new1", "new2"])]:
            client = FakeClient()

            def missing_id(stage: int, *, read_timeout: float | None = None) -> Response:
                """Create a task without returning an identifier to the caller."""
                client.creates += 1
                return Response(ok=True, task_id=None)

            client.request_next_task = missing_id  # type: ignore[method-assign]  # Inject the transport response for this test.
            client.get_tasks = lambda stage, **kwargs: Response(  # type: ignore[method-assign]  # Inject the transport response for this test.
                ok=ok, tasks=[Response(id=i, solved_at_all=False) for i in ids]
            )
            clock = [0.0]

            def pause(seconds: float) -> None:
                """Advance the fake clock instead of sleeping."""
                clock[0] += seconds

            with (
                patch.object(live_attempt, "monotonic", side_effect=lambda: clock[0]),
                patch.object(live_attempt, "sleep", side_effect=pause),
            ):
                report, _ = self.execute(client)
            self.assertEqual((client.creates, client.submits), (1, 0))
            self.assertEqual(report["phase"], "stopped")
            self.assertEqual(report["failed_phase"], "identifying_created_task")
