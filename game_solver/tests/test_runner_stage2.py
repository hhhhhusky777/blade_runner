"""Selected-stage runner coverage; fake clients and offline child only."""

import json
from pathlib import Path
import shutil
import unittest
from typing import Any, cast

from solver import runner as live_attempt
from api_client.client import GameClient
from api_client.models import StageCapabilities, StageCapabilitiesResponse


def make_cases() -> list[dict[str, Any]]:
    """Load the local Stage 2 inputs and their known winning plans."""
    return cast(
        list[dict[str, Any]],
        json.loads((Path(__file__).parent / "fixtures/stage2-fixtures.json").read_text())["cases"],
    )


from solver.stage2_reference import validate_plan
from tests.test_runner_loop import SeriesClient
from tests import test_runner_verification


class Stage2Client(SeriesClient):
    def __init__(self, **kwargs: Any) -> None:
        """Configure a fake stage client with the exact-cash ore fixture."""
        super().__init__(**kwargs)
        case = next(c for c in make_cases() if c["id"] == "ore-exact-construction-cash")
        self.level, self.plan = case["level"], case["witness"]

    def get_stage_capabilities(self, stage: int) -> StageCapabilitiesResponse:
        """Record the requested stage and return the saved Stage 2 contract."""
        self.calls.append(("capabilities", stage))
        snapshot = json.loads(
            (Path(__file__).parent / "fixtures/stage2-capabilities.json").read_text()
        )
        return StageCapabilitiesResponse.model_validate(snapshot["stage2_capabilities"])


class Stage2LiveTests(unittest.TestCase):
    def test_readiness_is_stage2_and_get_only(self) -> None:
        """Check readiness uses Stage 2 reads without creating or submitting tasks."""
        client = Stage2Client()
        before = live_attempt.preflight(cast(GameClient, client), stage=2)
        self.assertEqual(before["stage"], 2)
        self.assertEqual((client.creates, client.submits), (0, 0))
        self.assertTrue(all(stage == 2 for _, stage in client.calls))

    def test_offline_typed_child_plan_is_valid_under_both_relay_rules(self) -> None:
        """Check the offline child plan wins under both supported relay rules."""
        client = Stage2Client()
        answer = live_attempt.solve_local(client.level, seconds=1, stage=2)
        self.assertEqual(answer["status"], "FEASIBLE")
        for mode in ("matching", "unrestricted"):
            self.assertEqual(validate_plan(client.level, answer["plan"], mode)["base_iron_ore"], 5)

    def test_one_fresh_stage2_task_counts_and_every_endpoint_matches(self) -> None:
        """Verify one fresh Stage 2 task earns credit with consistent stage routing."""
        client = Stage2Client(totals=(1, 1))
        before = live_attempt.preflight(cast(GameClient, client), stage=2)
        report = live_attempt.attempt(cast(GameClient, client), before, lambda report: None)
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(report["stage"], 2)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertTrue(all(stage == 2 for _, stage in client.calls))
        self.assertEqual(report["strict_replay"]["base_iron_ore"], 5)

    def execute_loop(self, client: Stage2Client) -> dict[str, Any]:
        """Run a fake Stage 2 series and register cleanup for its task records."""
        report = live_attempt.run_loop(
            cast(GameClient, client),
            "fake-token",
            stage=2,
            solver=lambda *args: dict(status="FEASIBLE", plan=client.plan),
        )
        for row in report["task_results"]:
            self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
        self.assertTrue(all(stage == 2 for _, stage in client.calls))
        return report

    def test_stage2_loop_completes_remaining_levels_without_entering_stage3(self) -> None:
        """Verify the loop completes remaining Stage 2 levels and stops at the boundary."""
        client = Stage2Client(totals=(1, 3, 2))
        client.index = 1
        report = self.execute_loop(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual(report["stage"], 2)
        self.assertEqual((client.creates, client.submits, report["counted_tasks"]), (5, 5, 5))
        self.assertEqual(report["progress_after"]["current_index"], 3)

    def test_stage2_loop_stops_on_failed_late_or_unverified_task(self) -> None:
        """Check failed, late, ambiguous, and uncreated tasks stop the loop."""
        for failure, expected in (
            ("failed", "NOT_COUNTED"),
            ("late", "NOT_COUNTED"),
            ("stale_submit", "UNKNOWN"),
            ("create_timeout", "STOPPED"),
        ):
            client = Stage2Client(totals=(3, 2), failure=failure)
            report = self.execute_loop(client)
            self.assertEqual(report["outcome"], expected)
            self.assertEqual(client.creates, 1)
            self.assertEqual(client.submits, int(failure != "create_timeout"))
            self.assertEqual(report["counted_tasks"], 0)

    def test_stage2_loop_stops_on_pending_task_and_progress_disagreement(self) -> None:
        """Check pending work and conflicting progress prevent unsafe continuation."""
        client = Stage2Client()
        client.tasks = [test_runner_verification.task(id="old", solved_at_all=False)]
        self.assertEqual(self.execute_loop(client)["outcome"], "STOPPED")
        self.assertEqual((client.creates, client.submits), (0, 0))
        client = Stage2Client()
        client.progress_overrides[2] = client.progress()
        self.assertEqual(self.execute_loop(client)["outcome"], "UNKNOWN")
        self.assertEqual((client.creates, client.submits), (1, 1))

    def test_server_ready_for_gate_label_after_counted_partial_series(self) -> None:
        """Accept the observed gate-ready status during a partially completed series."""
        client = Stage2Client(totals=(1, 3, 2))
        client.index = 1
        original = client.progress

        def observed_progress() -> dict[str, Any]:
            """Simulate the server gate-ready label after a current series earns credit."""
            progress = original()
            for item in progress["items"]:
                if item["is_current"] and item["series_index"]:
                    item["status"] = "ready_for_gate"
            return progress

        # Deliberately replace this fake method to reproduce the server status.
        client.progress = observed_progress  # type: ignore[method-assign]
        report = self.execute_loop(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual((client.creates, client.submits, report["counted_tasks"]), (5, 5, 5))

    def test_stage2_cli_loop_routes_selected_stage(self) -> None:
        """Verify the command-line loop selects Stage 2 for every endpoint."""
        client = Stage2Client(totals=(1,))
        code, output = test_runner_verification.VerificationTests().invoke(
            ["--stage", "2", "--loop", "--json"], client
        )
        report = json.loads(output)
        for row in report["task_results"]:
            self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
        self.assertEqual((code, report["outcome"]), (0, "COMPLETE"))
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertTrue(all(stage == 2 for _, stage in client.calls))

    def test_bad_mine_capability_stops_before_create(self) -> None:
        """Reject a changed mine cost before creating a live task."""
        client = Stage2Client()
        original = client.get_stage_capabilities

        def changed(stage: int) -> StageCapabilitiesResponse:
            """Inject an unsupported mine cost into the saved capability response."""
            cap = original(stage)
            cast(StageCapabilities, cap.available).structures_details["IRON_MINE"].build_cost = {"STONE": 99}
            return cap

        # Deliberately replace this fake method to simulate capability drift.
        client.get_stage_capabilities = changed  # type: ignore[method-assign]
        with self.assertRaises(ValueError):
            live_attempt.preflight(cast(GameClient, client), stage=2)
        self.assertEqual((client.creates, client.submits), (0, 0))

    def test_verify_is_stage2_get_only(self) -> None:
        """Verify an existing Stage 2 result using reads alone."""
        client = Stage2Client()
        client.tasks = [
            dict(
                id="one",
                type="1",
                passed=True,
                passed_first_try=True,
                solved_at_all=True,
                solved_first_try_in_time=True,
                attempts_count=1,
                pass_time_taken_ms=1000,
            )
        ]
        code, output = test_runner_verification.VerificationTests().invoke(
            ["--stage", "2", "--verify", "one", "--json"], client
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["outcome"], "COUNTED")
        self.assertTrue(all(stage == 2 for _, stage in client.calls))
        self.assertEqual((client.creates, client.submits), (0, 0))

    def test_stage2_invalid_plan_and_ambiguous_posts_keep_no_retry(self) -> None:
        """Ensure invalid plans and ambiguous writes never trigger a blind retry."""
        for failure in ("create_timeout", "submit_timeout", None):
            client = Stage2Client(failure=failure)
            before = live_attempt.preflight(cast(GameClient, client), stage=2)
            solver = (
                (
                    lambda *args: dict(
                        status="FEASIBLE",
                        plan=[[{"action": "CLAIM_WIN", "args": {"x": 0, "y": 0}}]],
                    )
                )
                if failure is None
                else (lambda *args: dict(status="FEASIBLE", plan=client.plan))
            )
            report = live_attempt.attempt(cast(GameClient, client), before, lambda report: None, solver)
            self.assertEqual(client.creates, 1)
            self.assertEqual(client.submits, int(failure == "submit_timeout"))
            self.assertTrue(all(stage == 2 for _, stage in client.calls))
            self.assertIn("tasks_after", report)


if __name__ == "__main__":
    unittest.main()
