"""Complete local Stage1 sequences and conservative loop stop boundaries."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
import shutil
from typing import Any, cast
import unittest

from solver import runner as live_attempt
from tests import test_runner_verification
from tests.test_runner_attempt import Response
from api_client.client import GameClient
from api_client.models import Action, StageCapabilitiesResponse


class SeriesClient(test_runner_verification.ReadClient):
    def __init__(
        self,
        totals: tuple[int, ...] = (2, 1),
        completed: bool = False,
        failure: str | None = None,
    ) -> None:
        """Create a configurable sequence of levels and injected server failures."""
        super().__init__(tasks=[])
        self.totals = totals
        self.index = len(totals) if completed else 0
        self.series = 0
        self.failure = failure
        self.calls: list[tuple[str, int]] = []
        self.progress_reads = 0
        self.progress_overrides: dict[int, dict[str, Any] | BaseException] = {}
        self.task_override: Callable[[dict[str, Any]], None] | None = None
        self.bad_cap_after: int | None = None

    def progress(self) -> dict[str, Any]:
        """Build the current progression snapshot from the simulated series cursor."""
        return {
            "ok": True,
            "order": [str(i + 1) for i in range(len(self.totals))],
            "current_index": self.index,
            "items": [
                {
                    "type": str(i + 1),
                    "status": "done"
                    if i < self.index
                    else "current"
                    if i == self.index
                    else "locked",
                    "is_current": i == self.index,
                    "series_index": total
                    if i < self.index
                    else self.series
                    if i == self.index
                    else 0,
                    "series_total": total,
                }
                for i, total in enumerate(self.totals)
            ],
        }

    def get_stage_capabilities(self, stage: int) -> StageCapabilitiesResponse:
        """Return supported rules, optionally introducing drift after a submission."""
        self.calls.append(("capabilities", stage))
        cost = 99 if self.bad_cap_after is not None and self.submits >= self.bad_cap_after else 10
        return StageCapabilitiesResponse.model_validate(
            {
                "stage": stage,
                "new": {
                    "structures_details": {
                        "ROAD": {"build_cost": {"STONE": 1}},
                        "STONE_QUARRY": {
                            "build_cost": {"STONE": cost},
                            "rate": 5,
                            "resource_allow": ["STONE"],
                        },
                    },
                    "actions": {
                        name: {
                            "description": "",
                            "fields": {},
                            "required_fields": [],
                            "model_class": name,
                        }
                        for name in ("BUILD", "MINE", "TRANSFER", "CLAIM_WIN")
                    },
                },
            }
        )

    def get_stage_progress(self, stage: int) -> Response:
        """Read progression or inject a configured snapshot, error, or interrupt."""
        self.calls.append(("progress", stage))
        self.progress_reads += 1
        override = self.progress_overrides.get(self.progress_reads)
        if isinstance(override, BaseException):
            raise override
        return Response(**(override if override is not None else self.progress()))

    def get_tasks(self, stage: int, *, timeout: float | None = None) -> Response:
        """Return an isolated task inventory with any configured readback mutation."""
        self.calls.append(("tasks", stage))
        entries = deepcopy(self.tasks)
        if self.task_override and entries:
            self.task_override(entries[-1])
        return Response(ok=True, tasks=[Response(**t) for t in entries])

    def request_next_task(self, stage: int, *, read_timeout: float | None = None) -> Response:
        """Create one pending task and simulate missing IDs or interrupted responses."""
        self.calls.append(("create", stage))
        self.creates += 1
        assert self.index < len(self.totals), "must stop before another stage"
        assert all(t["solved_at_all"] for t in self.tasks), "must not replace pending task"
        identifier = "task-" + str(self.creates)
        self.tasks.append(
            test_runner_verification.task(
                id=identifier,
                type=str(self.index + 1),
                passed=False,
                passed_first_try=False,
                solved_at_all=False,
                solved_first_try_in_time=False,
                attempts_count=0,
            )
        )
        if self.failure == "create_timeout":
            raise TimeoutError("ambiguous create")
        if self.failure == "create_interrupt":
            raise KeyboardInterrupt()
        # Exercise the observed live missing-ID response on every iteration.
        return Response(ok=True, task_id=None)

    def get_task(self, stage: int, task_id: str) -> Response:
        """Return the sample level for the requested task identity."""
        self.calls.append(("input", stage))
        return Response(ok=True, id=task_id, level=Response(model_dump=lambda: self.level))

    def submit_plan(self, stage: int, task_id: str, plan: list[list[Action]]) -> Response:
        """Record one submission and apply the configured outcome to progression."""
        self.calls.append(("submit", stage))
        self.submits += 1
        assert task_id == self.tasks[-1]["id"]
        current = self.tasks[-1]
        current.update(attempts_count=1, passed=True, passed_first_try=True, solved_at_all=True)
        if self.failure in ("late", "failed"):
            if self.failure == "failed":
                current.update(passed=False, passed_first_try=False, solved_at_all=False)
            return Response(ok=True, accepted=False)
        if self.failure == "stale_submit":
            current.update(
                attempts_count=0, passed=False, passed_first_try=False, solved_at_all=False
            )
            return Response(ok=True, accepted=True)
        current["solved_first_try_in_time"] = True
        self.series += 1
        if self.series == self.totals[self.index]:
            self.index += 1
            self.series = 0
        if self.failure == "submit_timeout":
            raise TimeoutError("ambiguous submit")
        if self.failure == "submit_interrupt":
            raise KeyboardInterrupt()
        return Response(ok=True, accepted=True)


class LoopTests(unittest.TestCase):
    def execute(
        self,
        client: SeriesClient,
        solver: Callable[[dict[str, Any], float], dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Run the local loop, collect emitted receipts, and register file cleanup."""
        emitted: list[dict[str, Any]] = []
        report = live_attempt.run_loop(
            cast(GameClient, client),
            "fake-token",
            emit=emitted.append,
            solver=solver or (lambda *args: {"status": "FEASIBLE", "plan": client.plan}),
        )
        self.assertTrue(all(stage == 1 for _, stage in client.calls))
        for row in report["task_results"]:
            self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
        return report, emitted

    def test_multiple_tasks_per_level_then_next_level_and_stage_completion(self) -> None:
        """Complete every series position and stop when the selected stage ends."""
        client = SeriesClient()
        report, emitted = self.execute(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual(live_attempt.exit_code(report), 0)
        self.assertEqual((client.creates, client.submits, report["counted_tasks"]), (3, 3, 3))
        self.assertEqual(len({r["record_path"] for r in emitted}), 3)
        self.assertEqual([r["task_id"] for r in emitted], ["task-1", "task-2", "task-3"])
        self.assertTrue(all(r["strict_replay"] for r in emitted))
        self.assertEqual(report["progress_after"]["current_index"], 2)

    def test_recovered_level_ready_for_gate_can_start_fresh_series(self) -> None:
        """Allow a recovered current level to begin its required fresh series."""
        client = SeriesClient()
        ready = client.progress()
        ready["items"][0]["status"] = "ready_for_gate"
        client.progress_overrides[1] = ready
        report, _ = self.execute(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual((client.creates, client.submits), (3, 3))

    def test_ready_for_gate_with_partial_series_is_a_valid_current_cursor(self) -> None:
        """Resume a valid partial series without replaying its credited position."""
        client = SeriesClient()
        client.series = 1
        ready = client.progress()
        ready["items"][0]["status"] = "ready_for_gate"
        client.progress_overrides[1] = ready
        report, _ = self.execute(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual((client.creates, client.submits), (2, 2))

    def test_already_complete_never_creates(self) -> None:
        """Recognize both completed-cursor forms without creating another task."""
        for index in (2, None):
            client = SeriesClient(completed=True)
            initial = client.progress()
            initial["current_index"] = index
            client.progress_overrides[1] = initial
            report, _ = self.execute(client)
            self.assertEqual(report["outcome"], "COMPLETE")
            self.assertEqual((client.creates, client.submits), (0, 0))

    def test_failed_late_unknown_and_ambiguous_create_stop_without_next_task(self) -> None:
        """Stop after failed, late, uncertain, or interrupted task attempts."""
        for failure, outcome, submits in (
            ("late", "NOT_COUNTED", 1),
            ("failed", "NOT_COUNTED", 1),
            ("stale_submit", "UNKNOWN", 1),
            ("create_timeout", "STOPPED", 0),
            ("create_interrupt", "STOPPED", 0),
            ("submit_interrupt", "STOPPED", 1),
        ):
            with self.subTest(failure=failure):
                client = SeriesClient(failure=failure)
                report, _ = self.execute(client)
                self.assertEqual(report["outcome"], outcome)
                self.assertEqual((client.creates, client.submits), (1, submits))
                self.assertNotEqual(live_attempt.exit_code(report), 0)

    def test_ambiguous_submit_resolved_by_get_can_continue(self) -> None:
        """Continue when readback proves a timed-out submission counted."""
        client = SeriesClient(failure="submit_timeout")
        report, _ = self.execute(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual((client.creates, client.submits), (3, 3))

    def test_solver_unknown_does_not_submit_or_start_another_task(self) -> None:
        """Stop without submission or replacement when the solver returns UNKNOWN."""
        client = SeriesClient()
        report, _ = self.execute(client, lambda *a: {"status": "UNKNOWN", "plan": None})
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual((client.creates, client.submits), (1, 0))

    def test_uncertain_progress_after_counted_pass_stops(self) -> None:
        """Reject stale, malformed, or unreadable progression after a credited pass."""
        original = SeriesClient().progress()
        bad = []
        bad.append(original)  # stale, no series movement
        for field, value in (
            ("order", ["2", "1"]),
            ("order", ["1", "1"]),
            ("order", None),
            ("current_index", -1),
            ("current_index", True),
            ("items", []),
        ):
            entry = deepcopy(original)
            entry[field] = value
            bad.append(entry)
        entry = deepcopy(original)
        entry["items"][0]["series_total"] = 3
        entry["items"][0]["series_index"] = 1
        bad.append(entry)
        entry = deepcopy(original)
        entry["items"][0]["series_index"] = 2
        bad.append(entry)  # invalid current cursor
        entry = deepcopy(original)
        entry["items"][0]["series_index"] = True
        bad.append(entry)
        for progress in bad + [TimeoutError("no progress readback")]:
            with self.subTest(progress=progress):
                client = SeriesClient()
                client.progress_overrides[2] = progress
                report, _ = self.execute(client)
                self.assertEqual(report["outcome"], "UNKNOWN")
                self.assertEqual(report["counted_tasks"], 1)
                self.assertEqual((client.creates, client.submits), (1, 1))

    def test_fresh_preflight_must_match_last_verified_cursor(self) -> None:
        """Reject cursor drift between verified readback and the next preflight."""
        for change in ("regress", "grow", "jump", "error"):
            client = SeriesClient()
            next_read: dict[str, Any] | TimeoutError = client.progress()
            if change == "grow":
                cast(dict[str, Any], next_read)["items"][0].update(series_total=3, series_index=1)
            elif change == "jump":
                cast(dict[str, Any], next_read).update(current_index=1)
                cast(dict[str, Any], next_read)["items"][0].update(status="done", series_index=2, is_current=False)
                cast(dict[str, Any], next_read)["items"][1].update(status="current", is_current=True)
            elif change == "error":
                next_read = TimeoutError("preflight lost")
            client.progress_overrides[3] = next_read
            report, _ = self.execute(client)
            self.assertIn(report["outcome"], ("UNKNOWN", "ERROR"))
            self.assertEqual((client.creates, client.submits), (1, 1))
            self.assertEqual(len(report["task_results"]), 1)

    def test_wrong_credited_type_or_missing_task_get_stops(self) -> None:
        """Reject readback that identifies a different level or task."""
        for override in (lambda t: t.update(type="other"), lambda t: t.update(id="other")):
            client = SeriesClient()
            client.task_override = override
            report, _ = self.execute(client)
            self.assertEqual(report["outcome"], "UNKNOWN")
            self.assertEqual((client.creates, client.submits), (1, 1))

    def test_pending_task_and_later_capability_mismatch_stop(self) -> None:
        """Stop for incompatible pending work or later changes to game rules."""
        client = SeriesClient()
        client.tasks = [test_runner_verification.task(id="old", solved_at_all=False)]
        report, _ = self.execute(client)
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual((client.creates, client.submits), (0, 0))
        client = SeriesClient()
        client.bad_cap_after = 1
        report, _ = self.execute(client)
        self.assertEqual(report["outcome"], "ERROR")
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["counted_tasks"], 1)

    def test_receipt_failure_after_counted_pass_stops_before_next_create(self) -> None:
        """Preserve the counted result but stop when its receipt cannot be saved."""
        client = SeriesClient()
        original = live_attempt.checkpoint

        def checkpoint(
            report: dict[str, Any],
            save: Callable[[dict[str, Any]], None],
            required: bool = False,
        ) -> None:
            """Inject a receipt-write failure immediately after submission."""
            def unreliable(value: dict[str, Any]) -> None:
                """Persist receipts until the simulated post-submission disk failure."""
                if value["phase"] == "submitted":
                    raise OSError("disk unavailable")
                save(value)

            original(report, unreliable, required)

        live_attempt.checkpoint = checkpoint
        try:
            report, _ = self.execute(client)
        finally:
            live_attempt.checkpoint = original
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual(report["counted_tasks"], 1)
        self.assertEqual((client.creates, client.submits), (1, 1))

    def test_nonempty_create_id_cannot_reuse_a_previously_known_task(self) -> None:
        """Reject a creation response that reuses an existing task identity."""
        client = SeriesClient()
        client.tasks = [test_runner_verification.task(id="old", type="1")]
        original = client.request_next_task

        def stale_response(stage: int, *, read_timeout: float | None = None) -> Response:
            """Create a task but return an already known task ID."""
            original(stage, read_timeout=read_timeout)
            return Response(ok=True, task_id="old")

        # Replace this fake method to exercise stale server identity evidence.
        client.request_next_task = stale_response  # type: ignore[method-assign]
        report, _ = self.execute(client)
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual((client.creates, client.submits), (1, 0))
        self.assertFalse(any(call == "input" for call, _ in client.calls))

    def test_interrupt_retains_json_summary_at_readback_and_later_preflight(self) -> None:
        """Keep a usable JSON summary when later reads are interrupted."""
        import json

        for read in (2, 3):
            with self.subTest(progress_read=read):
                client = SeriesClient()
                client.progress_overrides[read] = KeyboardInterrupt()
                code, output = test_runner_verification.VerificationTests().invoke(
                    ["--loop", "--json"], client
                )
                report = json.loads(output)
                for row in report["task_results"]:
                    self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
                self.assertEqual(code, 2)
                self.assertEqual(report["outcome"], "STOPPED")
                self.assertEqual(report["counted_tasks"], 1)
                self.assertEqual(len(report["task_results"]), 1)
                self.assertEqual(report["task_results"][0]["task_id"], "task-1")
                self.assertTrue(Path(report["task_results"][0]["record_path"]).exists())
                self.assertEqual((client.creates, client.submits), (1, 1))

    def test_interrupt_in_task_readback_preserves_known_task_and_receipt(self) -> None:
        """Preserve task identity and receipt when task readback is interrupted."""
        client = SeriesClient()
        original = client.get_tasks

        def interrupted(stage: int, **kwargs: float | None) -> Response:
            """Interrupt task readback only after a submission has occurred."""
            if client.submits:
                raise KeyboardInterrupt()
            return original(stage, **kwargs)

        # Replace this fake method to inject a readback interruption.
        client.get_tasks = interrupted  # type: ignore[method-assign]
        report, emitted = self.execute(client)
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(emitted[0]["task_id"], "task-1")
        self.assertEqual(emitted[0]["verification"]["outcome"], "UNKNOWN")
        self.assertTrue(Path(report["task_results"][0]["record_path"]).exists())

    def test_cli_loop_json_is_one_summary_and_modes_remain_exclusive(self) -> None:
        """Emit one loop summary and reject incompatible CLI mode combinations."""
        import json
        from contextlib import redirect_stderr
        from io import StringIO

        client = SeriesClient(totals=(1,))
        code, output = test_runner_verification.VerificationTests().invoke(
            ["--loop", "--json"], client
        )
        report = json.loads(output)
        for row in report["task_results"]:
            self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
        self.assertEqual((code, report["outcome"]), (0, "COMPLETE"))
        self.assertEqual((client.creates, client.submits), (1, 1))
        for mode in ("--submit-one", "--check", "--offline-smoke"):
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as caught:
                live_attempt.main(
                    ["--loop", mode],
                    client_factory=cast(
                        live_attempt.ClientFactory, lambda *a: self.fail("network")
                    ),
                )
            self.assertEqual(caught.exception.code, 2)
