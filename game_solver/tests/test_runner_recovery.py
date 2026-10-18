"""Public-loop recovery boundaries with fake server state; no network."""

from copy import deepcopy
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
import httpx

from solver import runner as live
from tests.test_runner_loop import SeriesClient
from tests.test_runner_attempt import Response
from tests.test_runner_verification import task


class RecoveryClient(SeriesClient):
    def __init__(self, mode="late", attempts=0, drift=None, fresh_failure=None):
        super().__init__(totals=(1, 2), failure=fresh_failure)
        self.index, self.series = 1, 1
        self.mode, self.drift = mode, drift
        self.input_reads = 0
        self.pending_submits = 0
        self.tasks = [
            task(
                id="pending",
                type="2",
                created_at="2020-01-01T00:00:00+00:00",
                passed=False,
                passed_first_try=False,
                solved_at_all=False,
                solved_first_try_in_time=False,
                attempts_count=attempts,
            )
        ]

    def get_task(self, stage, task_id):
        self.input_reads += 1
        response = super().get_task(stage, task_id)
        if self.drift == "input" and self.input_reads > 1:
            level = deepcopy(self.level)
            level["max_turns"] += 1
            return Response(ok=True, id=task_id, level=Response(model_dump=lambda: level))
        return response

    def get_tasks(self, stage, **kwargs):
        if self.input_reads and not self.pending_submits and self.drift == "attempts":
            self.tasks[0]["attempts_count"] += 1
        return super().get_tasks(stage, **kwargs)

    def get_stage_progress(self, stage):
        if self.input_reads and not self.pending_submits and self.drift == "cursor":
            self.series = 0
        return super().get_stage_progress(stage)

    def submit_plan(self, stage, task_id, plan):
        if task_id != "pending":
            return super().submit_plan(stage, task_id, plan)
        self.calls.append(("submit", stage))
        self.submits += 1
        self.pending_submits += 1
        current = self.tasks[0]
        if self.mode == "unconfirmed":
            raise httpx.ReadTimeout("lost response")
        current["attempts_count"] += 2 if self.mode == "wrong_attempts" else 1
        current.update(
            passed=self.mode != "failed",
            solved_at_all=self.mode != "failed",
            passed_first_try=current["attempts_count"] == 1 and self.mode != "failed",
            solved_first_try_in_time=self.mode in ("timely", "wrong_counted_cursor"),
        )
        if self.mode == "timely":
            self.index, self.series = 2, 0
        elif self.mode not in ("wrong_reset", "wrong_counted_cursor"):
            self.series = 0
        if self.mode == "ambiguous":
            raise httpx.ReadTimeout("lost response after pass")
        return Response(
            ok=self.mode != "false_ok",
            accepted=self.mode in ("timely", "wrong_counted_cursor", "conflict"),
        )


class StartupRecoveryTests(unittest.TestCase):
    def execute(self, client, solver=None):
        emitted = []
        report = live.run_loop(
            client,
            "fake-token",
            emit=emitted.append,
            solver=solver or (lambda *args: dict(status="FEASIBLE", plan=client.plan)),
        )
        for row in report["task_results"]:
            self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
        self.assertTrue(all(stage == 1 for _, stage in client.calls))
        return report, emitted

    def test_expired_pending_is_completed_reset_then_loop_finishes(self):
        client = RecoveryClient()
        report, rows = self.execute(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual((client.pending_submits, client.creates, client.submits), (1, 2, 3))
        self.assertEqual(report["counted_tasks"], 2)
        self.assertEqual([r["outcome"] for r in rows], ["RECOVERED", "COUNTED", "COUNTED"])
        self.assertEqual(rows[0]["task_before"]["created_at"], "2020-01-01T00:00:00+00:00")
        self.assertTrue(rows[0]["reused_existing_task"])
        self.assertEqual(rows[0]["verification"]["outcome"], "NOT_COUNTED")

    def test_timely_pending_counts_and_completes_without_new_create(self):
        client = RecoveryClient(mode="timely")
        report, rows = self.execute(client)
        self.assertEqual((report["outcome"], report["counted_tasks"]), ("COMPLETE", 1))
        self.assertEqual((client.pending_submits, client.creates), (1, 0))
        self.assertEqual(rows[0]["outcome"], "COUNTED")

    def test_previously_failed_pending_can_pass_on_one_new_attempt(self):
        client = RecoveryClient(attempts=2)
        report, rows = self.execute(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual(rows[0]["tasks_after"][0]["attempts_count"], 3)
        self.assertEqual(rows[0]["outcome"], "RECOVERED")
        self.assertEqual(client.pending_submits, 1)

    def test_unknown_or_invalid_recovery_plan_never_submits_or_creates(self):
        for answer in (
            dict(status="UNKNOWN", plan=None),
            dict(status="FEASIBLE", plan=[[dict(action="CLAIM_WIN", args=dict(x=-1, y=-1))]]),
        ):
            with self.subTest(answer=answer):
                client = RecoveryClient()
                report, _ = self.execute(client, lambda *args: answer)
                self.assertEqual(report["outcome"], "STOPPED")
                self.assertEqual((client.submits, client.creates), (0, 0))

    def test_input_attempt_or_cursor_drift_stops_before_recovery_post(self):
        for drift in ("input", "attempts", "cursor"):
            with self.subTest(drift=drift):
                client = RecoveryClient(drift=drift)
                report, _ = self.execute(client)
                self.assertEqual(report["outcome"], "STOPPED")
                self.assertEqual((client.submits, client.creates), (0, 0))

    def test_missing_identity_or_unknown_attempt_count_never_submits(self):
        for changes in (
            {"type": "1"},
            {"attempts_count": None},
            {"attempts_count": True},
            {"attempts_count": -1},
        ):
            with self.subTest(changes=changes):
                client = RecoveryClient()
                client.tasks[0].update(changes)
                report, _ = self.execute(client)
                self.assertEqual(report["outcome"], "STOPPED")
                self.assertEqual((client.submits, client.creates), (0, 0))

    def test_failed_or_unverified_cleanup_never_creates(self):
        for mode in (
            "failed",
            "unconfirmed",
            "wrong_attempts",
            "wrong_reset",
            "wrong_counted_cursor",
            "conflict",
            "false_ok",
        ):
            with self.subTest(mode=mode):
                client = RecoveryClient(mode=mode)
                report, _ = self.execute(client)
                self.assertEqual(report["outcome"], "UNKNOWN")
                self.assertEqual((client.pending_submits, client.creates), (1, 0))

    def test_ambiguous_submit_can_reconcile_without_reposting(self):
        client = RecoveryClient(mode="ambiguous")
        report, rows = self.execute(client)
        self.assertEqual(report["outcome"], "COMPLETE")
        self.assertEqual(client.pending_submits, 1)
        self.assertEqual(rows[0]["outcome"], "RECOVERED")
        self.assertEqual(rows[0]["error_type"], "ReadTimeout")

    def test_new_failure_after_recovery_stops_without_second_recovery(self):
        client = RecoveryClient(fresh_failure="failed")
        report, rows = self.execute(client)
        self.assertEqual(report["outcome"], "NOT_COUNTED")
        self.assertEqual((client.pending_submits, client.creates, client.submits), (1, 1, 2))
        self.assertEqual([r["outcome"] for r in rows], ["RECOVERED", "NOT_COUNTED"])

    def test_recovery_receipt_failure_stops_without_new_create(self):
        client = RecoveryClient()
        original = live.checkpoint

        def checkpoint(report, save, required=False):
            def unreliable(value):
                if value["phase"] == "submitted":
                    raise OSError("disk unavailable")
                save(value)

            original(report, unreliable, required)

        with patch.object(live, "checkpoint", side_effect=checkpoint):
            report, _ = self.execute(client)
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual((client.pending_submits, client.creates), (1, 0))

    def test_stage2_and_stage3_default_child_recover_then_complete_selected_stage(self):
        from types import MethodType
        from tests.test_runner_stage2 import Stage2Client
        from tests.test_runner_stage3 import Stage3Client

        for stage, kind in ((2, Stage2Client), (3, Stage3Client)):
            with self.subTest(stage=stage):
                source = kind()
                client = RecoveryClient()
                client.level, client.plan = source.level, source.plan
                client.get_stage_capabilities = MethodType(kind.get_stage_capabilities, client)
                rows = []
                report = live.run_loop(client, "fake-token", stage=stage, emit=rows.append)
                for row in report["task_results"]:
                    self.addCleanup(shutil.rmtree, Path(row["record_path"]).parent)
                self.assertEqual((report["outcome"], report["counted_tasks"]), ("COMPLETE", 2))
                self.assertEqual((client.pending_submits, client.creates), (1, 2))
                self.assertEqual([r["outcome"] for r in rows], ["RECOVERED", "COUNTED", "COUNTED"])
                self.assertTrue(all(selected == stage for _, selected in client.calls))
                self.assertTrue(all(row["strict_replay"] for row in rows))

    def test_completed_progress_with_pending_inventory_is_not_complete(self):
        client = RecoveryClient()
        client.index = 2
        client.series = 0
        report, _ = self.execute(client)
        self.assertEqual(report["outcome"], "UNKNOWN")
        self.assertEqual((client.submits, client.creates), (0, 0))


if __name__ == "__main__":
    unittest.main()
