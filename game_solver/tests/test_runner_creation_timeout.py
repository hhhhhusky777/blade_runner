"""Creation-only HTTP timeout policy with HTTPX's offline mock transport."""

from __future__ import annotations

from typing import Any

import json
import os
import subprocess
import sys
import unittest

from solver import runner as live_attempt
from tests import test_runner_attempt


class CreationTimeoutTests(unittest.TestCase):
    def test_real_client_override_is_per_request_and_not_retried(self) -> None:
        """Verify creation timeout overrides through an isolated offline HTTP transport."""
        # Other PoCs deliberately disable sockets. Isolate HTTPX/SSL imports;
        # MockTransport makes every call below local, including the POSTs.
        script = """
import httpx,json
from api_client.client import GameClient
observed=[]
def respond(request: httpx.Request) -> httpx.Response:
    '''Serve local responses and simulate a lost creation response.'''
    observed.append({'path':request.url.path,'timeout':request.extensions['timeout']})
    if len(observed)==5:
        raise httpx.ReadTimeout('response lost',request=request)
    if request.url.path.endswith('/tasks/request'):
        return httpx.Response(200,json={'ok':True,'task_id':'new'})
    return httpx.Response(200,json={'ok':True,'accepted':True})
with GameClient('https://example.invalid','fake-token',timeout=3.0) as client:
    client._client.close()
    client._client=httpx.Client(base_url=client.base_url,timeout=3.0,transport=httpx.MockTransport(respond))
    client.request_next_task(1,read_timeout=10.0)
    client.get_stage_progress(1)
    client.submit_plan(1,'new',[])
    client.request_next_task(1)
    try:
        client.request_next_task(1,read_timeout=10.0)
    except httpx.ReadTimeout:
        pass
    else:
        raise AssertionError('expected timeout')
    client.get_stage_progress(1)
print(json.dumps(observed))
"""
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in ("GAME_SERVER_TOKEN", "ARBITER_TOKEN")
        }
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=True,
            cwd=live_attempt.APP_ROOT,
            env=env,
        )
        calls = json.loads(result.stdout)
        self.assertEqual(len(calls), 6)  # No automatic retry of the timed-out POST.
        for i, call in enumerate(calls):
            self.assertEqual(
                call["timeout"],
                {"connect": 3.0, "read": 10.0 if i in (0, 4) else 3.0, "write": 3.0, "pool": 3.0},
            )

    def test_long_creation_reduces_solver_budget_and_is_recorded(self) -> None:
        """Deduct creation time from the solver budget and retain the measured cost."""
        client = test_runner_attempt.FakeClient()
        clock = [0.0]
        budgets = []
        original = live_attempt.monotonic  # type: ignore[attr-defined]  # Patch the runner's imported clock.

        def create(
            stage: int,
            *,
            read_timeout: float | None = None,
        ) -> test_runner_attempt.Response:
            """Advance the simulated creation time and return the new task ID."""
            self.assertEqual(read_timeout, 5.0)
            client.creates += 1
            clock[0] += 10.0
            return test_runner_attempt.Response(ok=True, task_id="one")

        client.request_next_task = create  # type: ignore[method-assign]  # Inject the transport response for this test.
        live_attempt.monotonic = lambda: clock[0]  # type: ignore[attr-defined]  # Patch the runner's imported clock.
        try:

            def solver(level: dict[str, Any], seconds: float) -> dict[str, Any]:
                """Record the remaining solve budget and return the known witness."""
                budgets.append(seconds)
                return {"status": "FEASIBLE", "plan": client.plan}

            report, _ = test_runner_attempt.LiveAttemptTests().execute(client, solver)
        finally:
            live_attempt.monotonic = original  # type: ignore[attr-defined]  # Patch the runner's imported clock.
        self.assertEqual(budgets, [15.0])
        self.assertEqual(report["task_creation_elapsed"], 10.0)
        self.assertEqual(report["task_creation_read_timeout"], 5.0)
        self.assertEqual((client.creates, client.submits), (1, 1))

    def test_creation_that_exhausts_budget_never_solves_or_submits(self) -> None:
        """Avoid solving and submission after creation consumes the available budget."""
        client = test_runner_attempt.FakeClient()
        clock = [0.0]
        original = live_attempt.monotonic  # type: ignore[attr-defined]  # Patch the runner's imported clock.

        def create(
            stage: int,
            *,
            read_timeout: float | None = None,
        ) -> test_runner_attempt.Response:
            """Advance the simulated creation time and return the new task ID."""
            client.creates += 1
            clock[0] += 27.0
            return test_runner_attempt.Response(ok=True, task_id="one")

        client.request_next_task = create  # type: ignore[method-assign]  # Inject the transport response for this test.
        live_attempt.monotonic = lambda: clock[0]  # type: ignore[attr-defined]  # Patch the runner's imported clock.
        try:
            report, _ = test_runner_attempt.LiveAttemptTests().execute(
                client, lambda *args: self.fail("no solve budget")
            )
        finally:
            live_attempt.monotonic = original  # type: ignore[attr-defined]  # Patch the runner's imported clock.
        self.assertEqual(report["outcome"], "STOPPED")
        self.assertEqual(report["task_creation_elapsed"], 27.0)
        self.assertEqual((client.creates, client.submits), (1, 0))
