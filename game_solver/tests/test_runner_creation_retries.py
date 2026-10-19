"""Creation retries and reconciliation through the public attempt boundary."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any, cast
import json
import unittest
from unittest.mock import patch

import httpx
from solver import runner as live
from tests.test_runner_attempt import FakeClient, Response
from api_client.client import GameClient


class Clock:
    def __init__(self) -> None:
        """Start the controlled clock at zero."""
        self.now = 0.0

    def advance(self, seconds: float) -> None:
        """Advance the controlled clock by the simulated operation duration."""
        self.now += seconds


class RetryClient(FakeClient):
    def __init__(
        self,
        clock: Clock,
        creates: Sequence[tuple[float, Response | Exception]],
        lookups: Sequence[tuple[float, list[str] | Exception]] = (),
    ) -> None:
        """Prepare timed creation and inventory events for deterministic retries."""
        super().__init__()
        self.clock, self.create_events, self.lookup_events = clock, list(creates), list(lookups)
        self.create_timeouts: list[float | None]
        self.lookup_timeouts: list[float]
        self.create_timeouts, self.lookup_timeouts = [], []
        self.input_reads = 0

    def request_next_task(self, stage: int, *, read_timeout: float | None = None) -> Response:
        """Simulate task creation and count each attempted request."""
        self.creates += 1
        self.create_timeouts.append(read_timeout)
        seconds, value = self.create_events.pop(0)
        self.clock.advance(seconds)
        if isinstance(value, Exception):
            raise value
        return value

    def get_tasks(self, stage: int, *, timeout: float | None = None) -> Response:
        """Return fake task flags used for independent result verification."""
        if timeout is None:  # Independent final readback uses ordinary client settings.
            return super().get_tasks(stage)
        self.lookup_timeouts.append(timeout)
        seconds, value = self.lookup_events.pop(0) if self.lookup_events else (0, [])
        self.clock.advance(seconds)
        if isinstance(value, Exception):
            raise value
        return Response(ok=True, tasks=[Response(id=i, solved_at_all=False) for i in value])

    def get_task(self, stage: int, task_id: str) -> Response:
        """Return the saved level without contacting the server."""
        self.input_reads += 1
        return super().get_task(stage, task_id)


def lost_response() -> httpx.ReadTimeout:
    """Build the transport exception used for ambiguous creation."""
    return httpx.ReadTimeout("response lost")


class CreationRetryTests(unittest.TestCase):
    def run_attempt(
        self,
        client: RetryClient,
        clock: Clock,
        save_hook: Callable[[dict[str, Any]], None] | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[float]]:
        """Execute creation retries under the controlled clock and collect budgets."""
        records, budgets = [], []

        def save(report: dict[str, Any]) -> None:
            """Snapshot each receipt and apply the optional clock-changing checkpoint."""
            records.append(deepcopy(report))
            if save_hook:
                save_hook(report)

        def solver(level: dict[str, Any], seconds: float) -> dict[str, Any]:
            """Record the remaining solve budget and return the known witness."""
            budgets.append(seconds)
            return dict(status="FEASIBLE", plan=client.plan)

        with (
            patch.object(live, "monotonic", side_effect=lambda: clock.now),
            patch.object(live, "sleep", side_effect=clock.advance),
        ):
            report = live.attempt(
                cast(GameClient, client),
                dict(
                    pending_task_ids=[], listed_task_ids=[], progress_before=dict(current_index=0)
                ),
                save,
                solver,
            )
        return report, records, budgets

    def test_delayed_creation_is_recovered_without_another_post(self) -> None:
        """Recover a delayed inventory entry without duplicating task creation."""
        clock = Clock()
        client = RetryClient(clock, [(5, lost_response())], [(0, []), (0, ["one"])])
        report, records, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(client.create_timeouts, [5.0])
        self.assertEqual(budgets, [19.0])
        self.assertEqual(report["task_creation_elapsed"], 6.0)
        self.assertEqual(report["creation_requests"][0]["outcome"], "ambiguous")
        self.assertEqual(len(report["creation_lookups"]), 2)
        self.assertTrue(
            any(r.get("task_id") == "one" and not r["submit_attempted"] for r in records)
        )

    def test_confirmed_idless_creation_polls_until_inventory_appears(self) -> None:
        """Poll inventory after an acknowledged creation omits its identifier."""
        clock = Clock()
        client = RetryClient(clock, [(0, Response(ok=True, task_id=None))], [(0, []), (0, ["one"])])
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(budgets, [24.0])
        self.assertEqual(len(report["creation_lookups"]), 2)

    def test_confirmed_idless_creation_retries_get_transport_error(self) -> None:
        """Retry failed inventory reads after an acknowledged creation."""
        clock = Clock()
        client = RetryClient(
            clock, [(0, Response(ok=True, task_id=None))], [(3, lost_response()), (0, ["one"])]
        )
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(budgets, [21.0])
        self.assertEqual(report["creation_lookups"][0]["error_type"], "ReadTimeout")

    def test_malformed_creation_json_uses_only_get_reconciliation(self) -> None:
        """Treat malformed creation responses as ambiguous writes and reconcile by reads."""
        clock = Clock()
        client = RetryClient(
            clock, [(2, json.JSONDecodeError("invalid response", "?", 0))], [(0, []), (0, ["one"])]
        )
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(budgets, [22.0])
        self.assertEqual(report["creation_requests"][0]["error_type"], "JSONDecodeError")
        self.assertEqual(len(report["creation_lookups"]), 2)

    def test_empty_inventories_do_not_authorize_duplicate_creation(self) -> None:
        """Wait through empty inventories without issuing a second ambiguous write."""
        clock = Clock()
        client = RetryClient(clock, [(5, lost_response())])
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits), (1, 0))
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertTrue(report["creation_retry_deadline_reached"])
        self.assertEqual(report["task_creation_elapsed"], 30.0)
        self.assertEqual(clock.now, 30.0)
        self.assertEqual(budgets, [])
        self.assertEqual(report["listed_task_ids"], [])
        self.assertGreater(len(report["creation_lookups"]), 1)

    def test_only_definite_pre_send_failures_retry_create(self) -> None:
        """Retry creation only when transport evidence proves it was not sent."""
        for failure in (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout):
            with self.subTest(failure=failure):
                clock = Clock()
                client = RetryClient(
                    clock, [(3, failure("not sent")), (0, Response(ok=True, task_id="one"))]
                )
                report, _, budgets = self.run_attempt(client, clock)
                self.assertEqual((client.creates, client.submits), (2, 1))
                self.assertEqual(report["outcome"], "COUNTED")
                self.assertEqual(budgets, [21.0])
                self.assertEqual(report["creation_requests"][0]["outcome"], "pre_send_failure")
                self.assertEqual(client.create_timeouts, [5.0, 5.0])

    def test_response_loss_permanently_ends_create_retries(self) -> None:
        """Switch permanently to read reconciliation after a lost creation response."""
        clock = Clock()
        client = RetryClient(
            clock,
            [(1, httpx.ConnectTimeout("not sent")), (5, lost_response())],
            [(0, []), (0, []), (0, ["one"])],
        )
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits), (2, 1))
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(budgets, [17.0])
        self.assertEqual(
            [r["outcome"] for r in report["creation_requests"]], ["pre_send_failure", "ambiguous"]
        )

    def test_lookup_transport_timeouts_retry_only_the_lookup(self) -> None:
        """Retry a timed-out lookup while preserving the single creation attempt."""
        clock = Clock()
        client = RetryClient(clock, [(5, lost_response())], [(3, lost_response()), (0, ["one"])])
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits), (1, 1))
        self.assertEqual(report["outcome"], "COUNTED")
        self.assertEqual(budgets, [16.0])
        self.assertEqual(report["creation_lookups"][0]["error_type"], "ReadTimeout")

    def test_late_lookup_keeps_task_id_but_never_solves_or_submits(self) -> None:
        """Retain a late-discovered identifier without starting work past the deadline."""
        clock = Clock()
        client = RetryClient(clock, [(5, lost_response())], [(26, ["one"])])
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits, client.input_reads), (1, 0, 0))
        self.assertEqual(report["task_id"], "one")
        self.assertTrue(report["creation_retry_deadline_reached"])
        self.assertEqual(budgets, [])
        self.assertEqual(report["outcome"], "STOPPED")

    def test_late_create_response_stops_before_input_read(self) -> None:
        """Stop before reading the input when creation itself exceeds the deadline."""
        clock = Clock()
        client = RetryClient(clock, [(31, Response(ok=True, task_id="one"))])
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits, client.input_reads), (1, 0, 0))
        self.assertEqual(report["task_id"], "one")
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual(budgets, [])

    def test_multiple_pending_tasks_stop_reconciliation(self) -> None:
        """Reject ambiguous inventory containing more than one pending task."""
        clock = Clock()
        client = RetryClient(clock, [(5, lost_response())], [(0, ["one", "two"])])
        report, _, budgets = self.run_attempt(client, clock)
        self.assertEqual((client.creates, client.submits), (1, 0))
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual(report["error_type"], "ValueError")
        self.assertEqual(budgets, [])

    def test_checkpoint_cost_cannot_start_post_after_deadline(self) -> None:
        """Include checkpoint time when deciding whether another request may start."""
        clock = Clock()
        client = RetryClient(clock, [])

        def save_hook(report: dict[str, Any]) -> None:
            """Consume the remaining fake time at the selected checkpoint phase."""
            if report["phase"] == "requesting_task" and report.get("creation_requests"):
                clock.now = 30

        report, _, _ = self.run_attempt(client, clock, save_hook)
        self.assertEqual((client.creates, client.submits), (0, 0))
        self.assertEqual(report["outcome"], "STOPPED")

    def test_last_lookup_timeout_is_clipped_to_remaining_window(self) -> None:
        """Limit the last read timeout to the remaining creation window."""
        clock = Clock()
        client = RetryClient(clock, [(28, lost_response())], [(2, [])])
        report, _, _ = self.run_attempt(client, clock)
        self.assertEqual(client.lookup_timeouts, [2.0])
        self.assertEqual((client.creates, client.submits), (1, 0))
        self.assertEqual(report["task_creation_elapsed"], 30.0)

    def test_reconciliation_does_not_reset_submission_reserve(self) -> None:
        """Charge reconciliation time against the original submission deadline."""
        clock = Clock()
        client = RetryClient(clock, [(5, lost_response())], [(19, ["one"])])

        def save_hook(report: dict[str, Any]) -> None:
            """Consume the remaining fake time at the selected checkpoint phase."""
            if report["phase"] == "submitting":
                clock.now = 26

        report, _, budgets = self.run_attempt(client, clock, save_hook)
        self.assertEqual(budgets, [1.0])
        self.assertEqual((client.creates, client.submits), (1, 0))
        self.assertEqual(report["failed_phase"], "submitting")

    def test_real_malformed_response_is_reconciled_without_reposting(self) -> None:
        """Exercise invalid JSON and invalid UTF-8 through the real offline HTTP client."""
        fixture = FakeClient()
        for body, error_type in ((b"{", "JSONDecodeError"), (b"\xff", "UnicodeDecodeError")):
            with self.subTest(error_type=error_type):
                calls, submitted = [], [False]

                def respond(request: httpx.Request) -> httpx.Response:
                    """Serve deterministic HTTP responses through the offline transport."""
                    calls.append((request.method, request.url.path))
                    if request.url.path.endswith("/request"):
                        return httpx.Response(200, content=body)
                    if request.url.path.endswith("/submit"):
                        submitted[0] = True
                        return httpx.Response(200, json=dict(ok=True, accepted=True))
                    if request.url.path.endswith("/tasks"):
                        return httpx.Response(
                            200,
                            json=dict(
                                ok=True,
                                tasks=[
                                    dict(
                                        id="one",
                                        solved_at_all=submitted[0],
                                        passed=submitted[0],
                                        passed_first_try=submitted[0],
                                        solved_first_try_in_time=submitted[0],
                                        attempts_count=int(submitted[0]),
                                    )
                                ],
                            ),
                        )
                    if request.url.path.endswith("/progress"):
                        return httpx.Response(
                            200, json=dict(ok=True, current_index=int(submitted[0]))
                        )
                    return httpx.Response(
                        200, json=dict(ok=True, id="one", level=dict(fixture.level, spec_number=1))
                    )

                with GameClient("https://example.invalid", "fake", timeout=3) as client:
                    client._client.close()
                    client._client = httpx.Client(
                        base_url=client.base_url, timeout=3, transport=httpx.MockTransport(respond)
                    )
                    clock = Clock()
                    with (
                        patch.object(live, "monotonic", side_effect=lambda: clock.now),
                        patch.object(live, "sleep", side_effect=clock.advance),
                    ):
                        report = live.attempt(
                            client,
                            dict(
                                pending_task_ids=[],
                                listed_task_ids=[],
                                progress_before=dict(current_index=0),
                            ),
                            lambda report: None,
                            lambda *args: dict(status="FEASIBLE", plan=fixture.plan),
                        )
                self.assertEqual(report["outcome"], "COUNTED")
                self.assertEqual(report["creation_requests"][0]["error_type"], error_type)
                self.assertEqual(len(report["creation_lookups"]), 1)
                self.assertEqual(
                    sum(
                        method == "POST" and endpoint.endswith("/request")
                        for method, endpoint in calls
                    ),
                    1,
                )
                self.assertEqual(
                    sum(
                        method == "POST" and endpoint.endswith("/submit")
                        for method, endpoint in calls
                    ),
                    1,
                )

    def test_client_per_call_timeouts_leave_defaults_unchanged(self) -> None:
        """Keep per-request timeout overrides from changing the client defaults."""
        observed = []

        def respond(request: httpx.Request) -> httpx.Response:
            """Serve deterministic HTTP responses through the offline transport."""
            observed.append(request.extensions["timeout"])
            data = (
                {"ok": True, "task_id": "one"}
                if request.url.path.endswith("/request")
                else {"ok": True, "tasks": []}
                if request.url.path.endswith("/tasks")
                else {"ok": True, "accepted": True}
            )
            return httpx.Response(200, json=data)

        with GameClient("https://example.invalid", "fake", timeout=3) as client:
            client._client.close()
            client._client = httpx.Client(
                base_url=client.base_url, timeout=3, transport=httpx.MockTransport(respond)
            )
            client.request_next_task(2, read_timeout=5)
            client.get_tasks(2, timeout=0.5)
            client.request_next_task(2, read_timeout=0.4)
            client.get_tasks(2)
            client.submit_plan(2, "one", [])
        self.assertEqual(observed[0], dict(connect=3, read=5, write=3, pool=3))
        self.assertEqual(observed[1], dict.fromkeys(("connect", "read", "write", "pool"), 0.5))
        self.assertEqual(observed[2], dict.fromkeys(("connect", "read", "write", "pool"), 0.4))
        self.assertEqual(observed[3:], [dict.fromkeys(("connect", "read", "write", "pool"), 3)] * 2)


if __name__ == "__main__":
    unittest.main()
