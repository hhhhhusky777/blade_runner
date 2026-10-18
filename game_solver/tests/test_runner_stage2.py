"""Selected-stage runner coverage; fake clients and offline child only."""

import json
from pathlib import Path
import shutil
import unittest

from solver import runner as live_attempt
from api_client.models import StageCapabilitiesResponse


def make_cases():
    return json.loads((Path(__file__).parent / "fixtures/stage2-fixtures.json").read_text())[
        "cases"
    ]


from solver.stage2_reference import validate_plan
from tests.test_runner_loop import SeriesClient
from tests import test_runner_verification


class Stage2Client(SeriesClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        case = next(c for c in make_cases() if c["id"] == "ore-exact-construction-cash")
        self.level, self.plan = case["level"], case["witness"]

    def get_stage_capabilities(self, stage):
        self.calls.append(("capabilities", stage))
        snapshot = json.loads(
            (Path(__file__).parent / "fixtures/stage2-capabilities.json").read_text()
        )
        return StageCapabilitiesResponse.model_validate(snapshot["stage2_capabilities"])


class Stage2LiveTests(unittest.TestCase):
    def test_readiness_is_stage2_and_get_only(self):
        client = Stage2Client()
        before = live_attempt.preflight(client, stage=2)
        self.assertEqual(before["stage"], 2)
        self.assertEqual((client.creates, client.submits), (0, 0))
        self.assertTrue(all(stage == 2 for _, stage in client.calls))

    def test_offline_typed_child_plan_is_valid_under_both_relay_rules(self):
        client = Stage2Client()
        answer = live_attempt.solve_local(client.level, seconds=1, stage=2)
        self.assertEqual(answer["status"], "FEASIBLE")
        for mode in ("matching", "unrestricted"):
            self.assertEqual(validate_plan(client.level, answer["plan"], mode)["base_iron_ore"], 5)

    def test_one_fresh_stage2_task_counts_and_every_endpoint_matches(self):
        client = Stage2Client(totals=(1, 1))
        before = live_attempt.preflight(client, stage=2)
        report = live_attempt.attempt(client, before, lambda report: None)
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(report["stage"], 2)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertTrue(all(stage == 2 for _, stage in client.calls))
        self.assertEqual(report["strict_replay"]["base_iron_ore"], 5)

    def execute_loop(self, client):
        report = live_attempt.run_loop(
            client,
            "fake-token",
            stage=2,
            solver=lambda *args: dict(status="FEASIBLE", plan=client.plan),
        )
        for row in report["task_results"]:
            self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
        self.assertTrue(all(stage == 2 for _, stage in client.calls))
        return report

    def test_stage2_loop_completes_remaining_levels_without_entering_stage3(self):
        client = Stage2Client(totals=(1, 3, 2))
        client.index = 1
        report = self.execute_loop(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual(report["stage"], 2)
        self.assertEqual((client.creates, client.submits, report["counted_tasks"]), (5, 5, 5))
        self.assertEqual(report["progress_after"]["current_index"], 3)

    def test_stage2_loop_stops_on_failed_late_or_unverified_task(self):
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

    def test_stage2_loop_stops_on_pending_task_and_progress_disagreement(self):
        client = Stage2Client()
        client.tasks = [test_runner_verification.task(id="old", solved_at_all=False)]
        self.assertEqual(self.execute_loop(client)["outcome"], "STOPPED")
        self.assertEqual((client.creates, client.submits), (0, 0))
        client = Stage2Client()
        client.progress_overrides[2] = client.progress()
        self.assertEqual(self.execute_loop(client)["outcome"], "UNKNOWN")
        self.assertEqual((client.creates, client.submits), (1, 1))

    def test_server_ready_for_gate_label_after_counted_partial_series(self):
        client = Stage2Client(totals=(1, 3, 2))
        client.index = 1
        original = client.progress

        def observed_progress():
            progress = original()
            for item in progress["items"]:
                if item["is_current"] and item["series_index"]:
                    item["status"] = "ready_for_gate"
            return progress

        client.progress = observed_progress
        report = self.execute_loop(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual((client.creates, client.submits, report["counted_tasks"]), (5, 5, 5))

    def test_stage2_cli_loop_routes_selected_stage(self):
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

    def test_bad_mine_capability_stops_before_create(self):
        client = Stage2Client()
        original = client.get_stage_capabilities

        def changed(stage):
            cap = original(stage)
            cap.available.structures_details["IRON_MINE"].build_cost = {"STONE": 99}
            return cap

        client.get_stage_capabilities = changed
        with self.assertRaises(ValueError):
            live_attempt.preflight(client, stage=2)
        self.assertEqual((client.creates, client.submits), (0, 0))

    def test_verify_is_stage2_get_only(self):
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

    def test_stage2_invalid_plan_and_ambiguous_posts_keep_no_retry(self):
        for failure in ("create_timeout", "submit_timeout", None):
            client = Stage2Client(failure=failure)
            before = live_attempt.preflight(client, stage=2)
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
            report = live_attempt.attempt(client, before, lambda report: None, solver)
            self.assertEqual(client.creates, 1)
            self.assertEqual(client.submits, int(failure == "submit_timeout"))
            self.assertTrue(all(stage == 2 for _, stage in client.calls))
            self.assertIn("tasks_after", report)


if __name__ == "__main__":
    unittest.main()
