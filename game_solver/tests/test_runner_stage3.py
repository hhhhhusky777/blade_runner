"""Stage3 adapter contract and automatic submission path, without network."""

import json
import unittest
from unittest.mock import patch

from solver import runner as live_attempt
from api_client.models import StageCapabilitiesResponse
from pathlib import Path
from tests.test_runner_stage2 import Stage2Client
from tests import test_runner_verification


class Stage3Client(Stage2Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        case = json.loads((live_attempt.ROOT / "samples.json").read_text())["3"]
        self.level, self.plan = case["level"], case["witness"]

    def get_stage_capabilities(self, stage):
        self.calls.append(("capabilities", stage))
        raw = json.loads((Path(__file__).parent / "fixtures/stage3-capabilities.json").read_text())
        return StageCapabilitiesResponse.model_validate(
            raw["responses"]["/api/stage/3/capabilities"]
        )


class Stage3LiveTests(unittest.TestCase):
    def test_readiness_is_stage3_and_get_only(self):
        client = Stage3Client()
        before = live_attempt.preflight(client, stage=3)
        self.assertEqual(before["stage"], 3)
        self.assertEqual((client.creates, client.submits), (0, 0))
        self.assertTrue(all(stage == 3 for _, stage in client.calls))

    def test_child_produces_and_independently_replays_iron(self):
        answer = live_attempt.solve_local(Stage3Client().level, seconds=2, stage=3)
        self.assertEqual(answer["status"], "FEASIBLE")
        self.assertGreaterEqual(answer["strict_replay"]["base_inventory"]["IRON"], 4)
        self.assertTrue(any(a["action"] == "PRODUCE" for turn in answer["plan"] for a in turn))

    def test_adopted_settings_and_saved_failure_through_actual_child(self):
        from solver import stage3

        self.assertEqual(
            (
                stage3.INITIAL_PROBE_DECISIONS,
                stage3.PROBE_INTERVAL,
                stage3.FOLLOWUP_PROBE_DECISIONS,
            ),
            (512, 512, 32),
        )
        corpus = json.loads(
            (Path(__file__).parent / "fixtures/server-regressions.json").read_text()
        )
        row = next(
            r for r in corpus["tasks"] if r["task_id"] == "3f0d26c4-a6c0-4cd1-8deb-554e0772f8a5"
        )
        answer = live_attempt.solve_local(corpus["inputs"][row["input_sha256"]], seconds=5, stage=3)
        self.assertEqual(answer["status"], "FEASIBLE")
        self.assertTrue(answer["strict_replay"])

    def test_one_fresh_stage3_task_counts_without_entering_next_level(self):
        client = Stage3Client(totals=(1, 3))
        report = live_attempt.attempt(
            client, live_attempt.preflight(client, stage=3), lambda report: None
        )
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual((client.creates, client.submits, client.index), (1, 1, 1))
        self.assertGreaterEqual(report["strict_replay"]["base_inventory"]["IRON"], 4)
        self.assertTrue(all(stage == 3 for _, stage in client.calls))

    def test_stage3_capability_drift_blocks_before_create(self):
        changes = [
            lambda c: setattr(c.available.structures_details["SMELTER"], "rate", 3),
            lambda c: setattr(
                c.available.structures_details["SMELTER"], "build_cost", {"STONE": 19}
            ),
            lambda c: setattr(
                c.available.structures_details["SMELTER"],
                "recipe",
                {"inputs": {"IRON_ORE": 2}, "outputs": {"IRON": 1}},
            ),
            lambda c: c.available.actions.pop("PRODUCE"),
            lambda c: c.available.actions["PRODUCE"].required_fields.append("amount"),
            lambda c: setattr(c.available.actions["PRODUCE"].fields["x"], "type", "string"),
            lambda c: c.available.structures_details["SMELTER"].interfaces.append("Transport"),
        ]
        for change in changes:
            with self.subTest(change=change):
                client = Stage3Client()
                original = client.get_stage_capabilities

                def changed(stage):
                    cap = original(stage)
                    change(cap)
                    return cap

                client.get_stage_capabilities = changed
                with self.assertRaises(ValueError):
                    live_attempt.preflight(client, stage=3)
                self.assertEqual((client.creates, client.submits), (0, 0))

    def test_invalid_iron_claim_is_not_submitted(self):
        client = Stage3Client()
        report = live_attempt.attempt(
            client,
            live_attempt.preflight(client, stage=3),
            lambda report: None,
            solver=lambda *args: dict(
                status="FEASIBLE", plan=[[{"action": "CLAIM_WIN", "args": {"x": 0, "y": 0}}]]
            ),
        )
        self.assertEqual((report["outcome"], client.submits), ("STOPPED", 0))

    def test_stage3_cli_one_routes_selected_stage(self):
        client = Stage3Client(totals=(1, 3))
        with patch.object(
            live_attempt,
            "run_one",
            side_effect=lambda client, before, token: live_attempt.attempt(
                client, before, lambda r: None
            ),
        ):
            code, output = test_runner_verification.VerificationTests().invoke(
                ["--stage", "3", "--submit-one", "--json"], client
            )
        self.assertEqual((code, json.loads(output)["outcome"]), (0, "COUNTED"))
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertTrue(all(stage == 3 for _, stage in client.calls))

    def test_ambiguous_submit_is_not_retried(self):
        client = Stage3Client(failure="submit_timeout")
        report = live_attempt.attempt(
            client,
            live_attempt.preflight(client, stage=3),
            lambda report: None,
            solver=lambda *args: dict(status="FEASIBLE", plan=client.plan),
        )
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["outcome"], "COUNTED")

    def test_stage3_loop_stops_at_stage_completion(self):
        import shutil
        from pathlib import Path

        client = Stage3Client(totals=(1, 2))
        report = live_attempt.run_loop(
            client,
            "fake-token",
            stage=3,
            solver=lambda *args: dict(status="FEASIBLE", plan=client.plan),
        )
        for row in report["task_results"]:
            self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
        self.assertEqual((report["outcome"], report["counted_tasks"]), ("COMPLETE", 3))
        self.assertEqual((client.creates, client.submits), (3, 3))
        self.assertIn("Stage3 complete", report["message"])
        self.assertTrue(all(stage == 3 for _, stage in client.calls))

    def test_verify_is_stage3_get_only(self):
        client = Stage3Client()
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
            ["--stage", "3", "--verify", "one", "--json"], client
        )
        self.assertEqual((code, json.loads(output)["outcome"]), (0, "COUNTED"))
        self.assertEqual((client.creates, client.submits), (0, 0))
        self.assertTrue(all(stage == 3 for _, stage in client.calls))


if __name__ == "__main__":
    unittest.main()
