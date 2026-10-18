"""One-attempt boundaries without making network requests."""

from copy import deepcopy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from solver import runner as live_attempt


class Response(SimpleNamespace):
    def model_dump(self):
        return vars(self)


class FakeClient:
    def __init__(self, fail=None):
        self.fail = fail
        self.creates = self.submits = 0
        case = json.loads((live_attempt.ROOT / "samples.json").read_text())["1"]
        self.level, self.plan = case["level"], case["witness"]

    def request_next_task(self, stage, *, read_timeout=None):
        self.creates += 1
        if self.fail == "create":
            raise TimeoutError("response lost after create")
        return Response(ok=True, task_id="one")

    def get_task(self, stage, task_id):
        return Response(ok=True, id=task_id, level=Response(model_dump=lambda: self.level))

    def submit_plan(self, stage, task_id, plan):
        self.submits += 1
        if self.fail == "submit":
            raise TimeoutError("response lost after submit")
        return Response(ok=True, success=True, accepted=True)

    def get_stage_progress(self, stage):
        return Response(ok=True, current_index=int(bool(self.submits)))

    def get_tasks(self, stage, *, timeout=None):
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
    def execute(self, client, solver=None, pending=None):
        records = []
        solver = solver or (lambda *a: {"status": "FEASIBLE", "plan": client.plan})
        report = live_attempt.attempt(
            client,
            {
                "pending_task_ids": pending or [],
                "listed_task_ids": [],
                "progress_before": {"current_index": 0},
            },
            lambda r: records.append(deepcopy(r)),
            solver,
        )
        return report, records

    def test_one_create_one_submit_and_verified_progress(self):
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

    def test_unknown_and_invalid_plan_are_never_submitted(self):
        for result in (
            {"status": "UNKNOWN", "plan": None},
            {"status": "FEASIBLE", "plan": [[{"action": "CLAIM_WIN", "args": {"x": 0, "y": 0}}]]},
        ):
            client = FakeClient()
            report, _ = self.execute(client, lambda *a: result)
            self.assertEqual((client.creates, client.submits), (1, 0))
            self.assertEqual(report["phase"], "stopped")
            self.assertEqual(report["task_id"], "one")

    def test_uncertain_posts_are_not_retried_and_reads_reconcile(self):
        for phase, counts in [("create", (1, 0)), ("submit", (1, 1))]:
            client = FakeClient(phase)
            report, _ = self.execute(client)
            self.assertEqual((client.creates, client.submits), counts)
            self.assertEqual(report["error_type"], "TimeoutError")
            self.assertEqual(report["phase"], "stopped")
            self.assertIn("progress_after", report)
            self.assertIn("tasks_after", report)

    def test_final_checkpoint_cannot_consume_submission_reserve(self):
        client = FakeClient()
        current = [0.0]
        saved = live_attempt.monotonic
        live_attempt.monotonic = lambda: current[0]

        def expensive_checkpoint(report):
            if report["phase"] == "submitting":
                current[0] = 27.0

        try:
            report = live_attempt.attempt(
                client,
                {"pending_task_ids": [], "listed_task_ids": []},
                expensive_checkpoint,
                lambda *a: {"status": "FEASIBLE", "plan": client.plan},
            )
        finally:
            live_attempt.monotonic = saved
        self.assertEqual((client.creates, client.submits), (1, 0))
        self.assertEqual(report["error_type"], "TimeoutError")
        self.assertEqual(report["failed_phase"], "submitting")

    def test_live_missing_task_id_is_reconciled_without_a_second_post(self):
        client = FakeClient()

        def request_without_known_id(stage, *, read_timeout=None):
            client.creates += 1
            return Response(ok=True, task_id=None)

        client.request_next_task = request_without_known_id
        report, _ = self.execute(client)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["task_id"], "one")
        self.assertEqual(report["phase"], "submitted")
        self.assertIn("GET tasks difference", report["task_id_source"])

    def test_missing_id_stops_on_unsuccessful_or_ambiguous_get(self):
        for ok, ids in [(False, ["new"]), (True, []), (True, ["new1", "new2"])]:
            client = FakeClient()

            def missing_id(stage, *, read_timeout=None):
                client.creates += 1
                return Response(ok=True, task_id=None)

            client.request_next_task = missing_id
            client.get_tasks = lambda stage, **kwargs: Response(
                ok=ok, tasks=[Response(id=i, solved_at_all=False) for i in ids]
            )
            clock = [0.0]

            def pause(seconds):
                clock[0] += seconds

            with (
                patch.object(live_attempt, "monotonic", side_effect=lambda: clock[0]),
                patch.object(live_attempt, "sleep", side_effect=pause),
            ):
                report, _ = self.execute(client)
            self.assertEqual((client.creates, client.submits), (1, 0))
            self.assertEqual(report["phase"], "stopped")
            self.assertEqual(report["failed_phase"], "identifying_created_task")
