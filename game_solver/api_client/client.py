"""Authenticated HTTP transport and typed responses for the game service."""

from __future__ import annotations

from types import TracebackType
from typing import Any, TypedDict, cast

import httpx

from . import models as m


class _TimeoutOptions(TypedDict, total=False):
    """Optional HTTPX keyword; omission retains the configured session timeout."""

    timeout: float | httpx.Timeout


class GameClient:
    """
    A typed client for the Recruitment Game Server API.

    Configure with base_url and a bearer token, then call the endpoints.
    """

    def __init__(
        self, base_url: str, token: str | None = None, *, timeout: float = 30.0
    ) -> None:
        """Create a reusable HTTP session; timeout is the default seconds per phase."""
        if not base_url:
            raise ValueError("base_url is required, e.g. 'https://example.com'")
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    @property
    def token(self) -> str | None:
        """Return the configured bearer token without making a request."""
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        """Replace the token used by subsequent authenticated requests."""
        self._token = value

    # --- Internal helpers ---
    def _auth_headers(self) -> dict[str, str]:
        """Build authorization headers; fail locally when no token is configured."""
        if not self._token:
            raise RuntimeError("Bearer token not set. Set GameClient.token first.")
        return {"Authorization": f"Bearer {self._token}"}

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Send an authenticated GET, preserving the session default if omitted."""
        options: _TimeoutOptions = {"timeout": timeout} if timeout is not None else {}
        return self._client.get(path, headers=self._auth_headers(), params=params, **options)

    def _post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> httpx.Response:
        """Send one authenticated POST with an optional per-request timeout."""
        options: _TimeoutOptions = {"timeout": timeout} if timeout is not None else {}
        return self._client.post(path, headers=self._auth_headers(), json=json, **options)

    # --- Public API methods ---
    def get_stages(self) -> m.StagesResponse:
        """Read the stages currently exposed by the service."""
        r = self._get("/api/stages")
        r.raise_for_status()
        return m.StagesResponse.model_validate(r.json())

    def get_stage_capabilities(self, stage: int) -> m.StageCapabilitiesResponse:
        """Read action, resource and construction rules for the selected stage."""
        r = self._get(f"/api/stage/{stage}/capabilities")
        r.raise_for_status()
        return m.StageCapabilitiesResponse.model_validate(r.json())

    def get_stage_progress(self, stage: int) -> m.StageProgress:
        """Read level and series progress without creating a timed task."""
        r = self._get(f"/api/stage/{stage}/progress")
        r.raise_for_status()
        return m.StageProgress.model_validate(r.json())

    def get_tasks(self, stage: int, *, timeout: float | None = None) -> m.TasksResponse:
        """List task identities and server status, optionally bounding this GET."""
        r = self._get(f"/api/stage/{stage}/tasks", timeout=timeout)
        r.raise_for_status()
        return m.TasksResponse.model_validate(r.json())

    def request_next_task(
        self, stage: int, *, read_timeout: float | None = None
    ) -> m.RequestTaskResponse:
        """Request a timed task once; preserve an unfinished-task conflict as data.

        A read timeout does not prove creation failed. The runner reconciles
        task identities before considering another creation request.
        """
        # Copy per-request settings so longer creation reads do not affect submit.
        timeout = None
        if read_timeout is not None:
            timeout = httpx.Timeout(self._client.timeout)
            timeout.read = read_timeout
            # Short remaining windows must also bound connect/write/pool waits.
            for phase in ("connect", "write", "pool"):
                current = getattr(timeout, phase)
                setattr(
                    timeout, phase,
                    min(current, read_timeout) if current is not None else read_timeout,
                )
        r = self._post(f"/api/stage/{stage}/tasks/request", timeout=timeout)
        if r.status_code == 409:
            # likely {"ok": False, "error": "unfinished_task"}
            try:
                data = r.json()
            except Exception:
                data = {"ok": False, "error": "conflict"}
            return m.RequestTaskResponse.model_validate(data)
        r.raise_for_status()
        return m.RequestTaskResponse.model_validate(r.json())

    def get_task(self, stage: int, task_id: str) -> m.TaskDetail:
        """Fetch one existing input and normalize the optional task response wrapper."""
        r = self._get(f"/api/stage/{stage}/tasks/{task_id}")
        r.raise_for_status()
        data = r.json()
        # Some implementations wrap the task under a top-level "task" key
        # Normalize so TaskDetail always receives id/level at the top level
        if isinstance(data, dict) and "task" in data and isinstance(data["task"], dict):
            inner = {**data["task"]}
            # propagate ok flag if present
            if "ok" in data and "ok" not in inner:
                inner["ok"] = data["ok"]
            data = inner
        return m.TaskDetail.model_validate(data)

    def submit_plan(self, stage: int, task_id: str, plan: list[list[m.Action]]) -> m.SubmitResult:
        """Submit one typed action plan exactly once; the caller verifies progression."""
        # Convert plan to serializable format
        norm_plan: list[list[dict[str, Any]]] = []
        for turn in plan:
            norm_turn: list[dict[str, Any]] = []
            for action in turn:
                # Actions should already be API Action instances
                if isinstance(action, m.Action):
                    norm_turn.append(action.model_dump())
                else:
                    raise TypeError("Actions must be API Action instances")
            norm_plan.append(norm_turn)
        payload = {"plan": norm_plan}

        r = self._post(f"/api/stage/{stage}/tasks/{task_id}/submit", json=payload)
        # The API returns 200 with an ok flag; raise for other errors
        r.raise_for_status()
        return m.SubmitResult.model_validate(r.json())

    # Schema helper
    def get_level_schema(self) -> dict[str, Any]:
        """Read the extensible JSON schema used to describe level inputs."""
        r = self._get("/api/schema/level")
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    # --- Context management ---
    def close(self) -> None:
        """Release the underlying connection pool."""
        self._client.close()

    def __enter__(self) -> GameClient:
        """Return this session for use in a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the session on normal exit or exception without suppressing errors."""
        self.close()
