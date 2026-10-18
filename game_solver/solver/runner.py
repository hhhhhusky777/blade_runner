"""Submit Stage1/2/3 plans and verify results; default mode is read-only.

Reuse the supplied typed GameClient. The offline solver runs in a separate,
network-disabled process. Retry creation only after pre-send failures; use
GET reconciliation after ambiguous creation, and never retry submissions. The offline engine is the adopted packaged solver; the original research adapter remains frozen.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from time import monotonic, sleep
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
APP_ROOT = ROOT.parent


def validate_local(level, plan, stage=1):
    """Replay the child result on the original input in the parent process."""
    from .api import validate_plan

    return validate_plan(level, plan, stage)


def solver_child():
    """Enter explicit isolation; ordinary imports never disable sockets."""
    from .child import main

    main()


def solve_local(level, seconds=24.0, stage=1):
    """Run the offline child with a hard outer timeout, stripped tokens and parent replay."""
    child_env = {
        k: v for k, v in os.environ.items() if k not in ("GAME_SERVER_TOKEN", "ARBITER_TOKEN")
    }
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "solver.child"],
        input=json.dumps({"level": level, "seconds": seconds, "stage": stage}),
        capture_output=True,
        text=True,
        timeout=seconds + 1,
        env=child_env,
        check=True,
        cwd=APP_ROOT,
    )
    result = json.loads(completed.stdout)
    if result["status"] == "FEASIBLE":
        result["strict_replay"] = validate_local(level, result["plan"], stage)
    return result


def preflight(client, allow_complete=False, stage=1):
    """Read capabilities, progression and pending tasks before any authorized write."""
    if stage not in (1, 2, 3):
        raise ValueError("only Stage1, Stage2 and Stage3 are supported")
    capabilities = client.get_stage_capabilities(stage)
    cap = capabilities.available_capabilities() or capabilities.new
    for name, cost in (("ROAD", 1), ("STONE_QUARRY", 10)):
        detail = cap.structures_details.get(name)
        if detail is None or detail.build_cost != {"STONE": cost}:
            raise ValueError("server construction capabilities differ from the local model")
    quarry = cap.structures_details["STONE_QUARRY"]
    if quarry.rate != 5 or "STONE" not in quarry.resource_allow:
        raise ValueError("server extraction capabilities differ from the local model")
    if not {"BUILD", "MINE", "TRANSFER", "CLAIM_WIN"} <= set(cap.actions):
        raise ValueError("server does not advertise all required actions")
    if stage in (2, 3):
        mine = cap.structures_details.get("IRON_MINE")
        if (
            mine is None
            or mine.build_cost != {"STONE": 15}
            or mine.rate != 5
            or set(mine.resource_allow) != {"IRON_ORE"}
            or set(cap.resources)
            != ({"STONE", "IRON_ORE"} if stage == 2 else {"STONE", "IRON_ORE", "IRON"})
        ):
            raise ValueError(f"Stage{stage} capabilities differ from the validated local model")
    if stage == 3:
        smelter = cap.structures_details.get("SMELTER")
        produce = cap.actions.get("PRODUCE")
        if (
            smelter is None
            or smelter.build_cost != {"STONE": 20}
            or smelter.rate != 2
            or smelter.recipe != {"inputs": {"IRON_ORE": 1}, "outputs": {"IRON": 1}}
            or set(smelter.interfaces) != {"Buildable", "Storage", "Production"}
            or produce is None
            or set(produce.required_fields) != {"x", "y"}
            or any(
                name not in produce.fields or produce.fields[name].type != "integer"
                for name in ("x", "y")
            )
        ):
            raise ValueError("Stage3 production capabilities differ from the validated local model")
    progress = client.get_stage_progress(stage)
    tasks = client.get_tasks(stage)
    if not capabilities.ok or not progress.ok or not tasks.ok:
        raise ValueError("server read-only preflight was not successful")
    pending = []
    for task in tasks.tasks:
        status = getattr(task, "solved_at_all", None)
        if type(status) is not bool:
            raise ValueError(
                "task completion status is unknown; inspect before requesting another task"
            )
        if not status:
            pending.append(task.id)
    if len(pending) > 1:
        raise ValueError("multiple unfinished tasks; inspect before choosing one")
    if (
        not allow_complete
        and progress.order
        and (progress.current_index or 0) >= len(progress.order)
    ):
        raise ValueError(f"Stage{stage} is already complete; select a stage explicitly")
    return {
        "stage": stage,
        "capabilities": cap.model_dump(),
        "progress_before": progress.model_dump(),
        "pending_task_ids": pending,
        "listed_task_ids": [t.id for t in tasks.tasks],
        "listed_tasks": len(tasks.tasks),
    }


def redact(value, token):
    """Redact before JSON encoding, including secrets containing quotes/slashes."""
    if isinstance(value, str):
        return value.replace(token, "[REDACTED]") if token else value
    if isinstance(value, dict):
        return {redact(k, token): redact(v, token) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, token) for v in value]
    return value


def progress_changed(before, after, task_type):
    """Observed movement, not proof this command caused it; None=no baseline."""
    if not before or not after:
        return None
    bi, ai = before.get("current_index"), after.get("current_index")
    if type(bi) is int and type(ai) is int and ai > bi:
        return True

    def item(progress):
        return next((x for x in progress.get("items", []) if x.get("type") == task_type), {})

    old, new = item(before), item(after)
    bs, ns = old.get("series_index"), new.get("series_index")
    if type(bs) is int and type(ns) is int and ns > bs:
        return True
    if old and new and old.get("status") != "done" and new.get("status") == "done":
        return True
    return False if old and new else None


def assess_result(report):
    """Task-ID GET flags own countedness; progress is separate corroboration."""
    matches = [t for t in report.get("tasks_after", []) if t.get("id") == report.get("task_id")]
    result = {
        "outcome": "UNKNOWN",
        "reason": "Task status could not be verified.",
        "progress_changed": None,
        "server_seconds": None,
    }
    if len(matches) != 1 or report.get("tasks_verification_error_type"):
        return result
    task = matches[0]
    result.update(
        server_seconds=(
            task["pass_time_taken_ms"] / 1000
            if type(task.get("pass_time_taken_ms")) in (int, float)
            else None
        ),
        attempts=task.get("attempts_count"),
        progress_changed=progress_changed(
            report.get("progress_before"), report.get("progress_after"), task.get("type")
        ),
    )
    passed, timely = task.get("passed"), task.get("solved_first_try_in_time")
    submission = report.get("submit_result") or {}
    attempts = task.get("attempts_count")
    if type(attempts) is not int or attempts <= 0:
        result["reason"] = "No completed attempt is confirmed by the task readback."
        return result
    flags = ("passed", "passed_first_try", "solved_at_all", "solved_first_try_in_time")
    if (
        any(task.get(key) is not None and type(task[key]) is not bool for key in flags)
        or (passed is False and task.get("passed_first_try") is True)
        or (passed is True and task.get("solved_at_all") is False)
        or (timely is True and (passed is False or task.get("passed_first_try") is False))
    ):
        result["reason"] = "Server task flags are inconsistent or malformed."
        return result
    if passed is True and timely is True:
        if submission.get("accepted") is False or submission.get("ok") is False:
            result["reason"] = "Server task flags and submission response conflict."
        else:
            result.update(
                outcome="COUNTED", reason="Server verified a first-try pass within the deadline."
            )
    elif type(passed) is bool and timely is False:
        if submission.get("accepted") is True:
            result["reason"] = "Submission accepted but task readback does not yet confirm it."
        else:
            result.update(
                outcome="NOT_COUNTED",
                reason="Plan passed but did not count toward advancement."
                if passed
                else "Server did not pass this task.",
            )
    return result


def read_back(client, report):
    # Independent reads retain useful task proof even if progress is unavailable.
    """Fetch task flags and progression without creating or submitting a task."""
    try:
        tasks = client.get_tasks(report.get("stage", 1))
        if not tasks.ok:
            raise RuntimeError("task verification GET was unsuccessful")
        report["tasks_after"] = [t.model_dump() for t in tasks.tasks]
    except (Exception, KeyboardInterrupt) as exc:
        report["tasks_verification_error_type"] = type(exc).__name__
        if isinstance(exc, KeyboardInterrupt):
            report["error_type"] = "KeyboardInterrupt"
    try:
        progress = client.get_stage_progress(report.get("stage", 1))
        if not progress.ok:
            raise RuntimeError("progress verification GET was unsuccessful")
        report["progress_after"] = progress.model_dump()
    except (Exception, KeyboardInterrupt) as exc:
        report["progress_verification_error_type"] = type(exc).__name__
        if isinstance(exc, KeyboardInterrupt):
            report["error_type"] = "KeyboardInterrupt"
    report["verification"] = assess_result(report)


def exit_code(report):
    """Map verified outcomes to CLI success or failure without guessing advancement."""
    return {
        "COUNTED": 0,
        "COMPLETE": 0,
        "READY": 0,
        "OFFLINE_OK": 0,
        "NOT_COUNTED": 1,
        "STOPPED": 2,
        "ERROR": 2,
        "UNKNOWN": 3,
        "RECOVERED": 0,
    }[report["outcome"]]


def display(report, as_json=False, token=""):
    """Render a token-redacted result in JSON or plain text."""
    safe = redact(report, token)
    if as_json:
        print(json.dumps(safe, indent=2))
        return
    if safe.get("stage"):
        print("Stage: " + str(safe["stage"]))
    print(
        safe["outcome"] + ": " + safe.get("message", safe.get("verification", {}).get("reason", ""))
    )
    if safe.get("mode") == "loop":
        print(f"Tasks counted this run: {safe['counted_tasks']}")
    if safe.get("task_id"):
        print("Task: " + safe["task_id"])
    verified = safe.get("verification", {})
    if verified.get("server_seconds") is not None:
        print(
            f"Server time: {verified['server_seconds']:.3f}s; attempts: {verified.get('attempts')}"
        )
    progress = safe.get("progress_after") or safe.get("progress_before") or {}
    current = next((x for x in progress.get("items", []) if x.get("is_current")), None)
    if current:
        print(
            f"Current level: {current['type']}; series {current.get('series_index', 0)}/{current.get('series_total', '?')}"
        )
    if "progress_changed" in verified:
        movement = verified["progress_changed"]
        print(
            "Progress change: "
            + (
                "observed"
                if movement is True
                else "not observed"
                if movement is False
                else "no baseline or unavailable"
            )
        )
    if safe.get("progress_verification_error_type"):
        print("Progress readback unavailable; task result is reported separately.")
    if safe.get("checkpoint_error_type"):
        print("Receipt write failed; task ID and server verification are preserved here.")
    if safe.get("record_path"):
        print("Record: " + safe["record_path"])


def checkpoint(report, save, required=False):
    """Persist the receipt before consequential actions; preserve write failures."""
    try:
        save(report)
    except Exception as exc:
        report["checkpoint_error_type"] = type(exc).__name__
        if required:
            raise OSError("Cannot checkpoint safely before the next action.") from None


def request_task(client, stage, before, report, save, deadline):
    """Acquire one task, retrying safely within the original 30-second window.

    HTTPX limits inactivity per phase; deadline checks stop further work when
    an in-flight call returns late. They do not cancel an in-flight request.
    """
    import httpx
    from pydantic import ValidationError

    previous = set(before["listed_task_ids"])
    mode = "create"
    report["creation_requests"] = []
    report["creation_lookups"] = []
    while monotonic() < deadline:
        if mode == "create":
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            entry = dict(
                attempt=len(report["creation_requests"]) + 1,
                read_timeout=min(5.0, remaining),
                remaining_before=remaining,
            )
            report["creation_requests"].append(entry)
            report["phase"] = "requesting_task"
            checkpoint(report, save, required=True)
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            entry["read_timeout"] = min(5.0, remaining)
            try:
                response = client.request_next_task(stage, read_timeout=entry["read_timeout"])
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout) as error:
                entry.update(error_type=type(error).__name__, outcome="pre_send_failure")
                mode = "lookup_then_retry"
            except (
                httpx.RequestError,
                httpx.HTTPStatusError,
                ValidationError,
                json.JSONDecodeError,
                UnicodeDecodeError,
            ) as error:
                entry.update(error_type=type(error).__name__, outcome="ambiguous")
                # Authentication/permission errors are actionable, not transient.
                if isinstance(error, httpx.HTTPStatusError) and error.response.status_code in (
                    401,
                    403,
                ):
                    raise
                mode = "lookup_only"
            else:
                entry["outcome"] = "response"
                report["request_response"] = response.model_dump()
                if response.ok and response.task_id:
                    return response, None
                if not response.ok and getattr(response, "error", None) != "unfinished_task":
                    raise RuntimeError("server did not confirm task creation")
                # A confirmed creation without an ID also needs GET-only polling.
                mode = "lookup_only"
            report["creation_retry_mode"] = mode
            checkpoint(report, save, required=True)
        remaining = deadline - monotonic()
        if remaining <= 0:
            break
        report["phase"] = "identifying_created_task"
        lookup = dict(
            attempt=len(report["creation_lookups"]) + 1,
            timeout=min(3.0, remaining),
            remaining_before=remaining,
        )
        report["creation_lookups"].append(lookup)
        checkpoint(report, save, required=True)
        remaining = deadline - monotonic()
        if remaining <= 0:
            break
        lookup["timeout"] = min(3.0, remaining)
        try:
            refreshed = client.get_tasks(stage, timeout=lookup["timeout"])
        except httpx.RequestError as error:
            lookup["error_type"] = type(error).__name__
        else:
            if not refreshed.ok:
                raise RuntimeError("task ID reconciliation GET was unsuccessful")
            if any(type(getattr(t, "solved_at_all", None)) is not bool for t in refreshed.tasks):
                raise ValueError("task completion status is unknown during reconciliation")
            pending = [t.id for t in refreshed.tasks if t.solved_at_all is False]
            lookup["pending_task_ids"] = pending
            if any(identifier in previous for identifier in pending) or len(pending) > 1:
                raise ValueError("new task cannot be identified unambiguously")
            if pending:
                report.update(
                    task_id=pending[0],
                    task_id_source="GET tasks difference after creation retry/reconciliation",
                )
                checkpoint(report, save, required=True)
                if monotonic() >= deadline:
                    break
                return None, pending[0]
            if mode == "lookup_then_retry":
                mode = "create"
        checkpoint(report, save, required=True)
        remaining = deadline - monotonic()
        if remaining > 0:
            sleep(min(1.0, remaining))
    report["creation_retry_deadline_reached"] = True
    raise TimeoutError(
        "creation retry window exhausted; inspect existing tasks before another create"
    )


def attempt(client, before, save, solver=solve_local, *, recover_pending=False):
    """One fresh attempt, or one explicitly selected startup recovery submission."""
    from api_client.models import Action

    stage = before.get("stage", 1)
    if stage not in (1, 2, 3):
        raise ValueError("only Stage1, Stage2 and Stage3 are supported")
    if solver is solve_local and stage != 1:
        solver = lambda level, seconds: solve_local(level, seconds, stage=stage)
    report = {
        "stage": stage,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "submit_attempted": False,
        **before,
    }
    start = monotonic()  # Conservative: new task is created AFTER this timestamp.
    report["phase"] = "select_task"
    try:
        checkpoint(report, save, required=True)
        if "listed_task_ids" not in before:
            raise ValueError("read-only preflight task inventory is required")
        recovering = bool(before["pending_task_ids"]) and recover_pending
        if before["pending_task_ids"]:
            task_id = report["task_id"] = before["pending_task_ids"][0]
            if not recovering:
                raise ValueError(
                    "existing task keeps its original clock; inspect it before attempting"
                )
            report.update(mode="pending-recovery", reused_existing_task=True)
            snapshot = loop_progress(before["progress_before"])
            tasks = client.get_tasks(stage)
            matches = [t.model_dump() for t in tasks.tasks if t.id == task_id]
            if (
                not tasks.ok
                or snapshot is None
                or len(before["pending_task_ids"]) != 1
                or len(matches) != 1
                or snapshot[1][0] >= len(snapshot[0])
            ):
                raise ValueError("pending task cannot be bound to the current level")
            original = matches[0]
            if (
                original.get("type") != snapshot[0][snapshot[1][0]][0]
                or original.get("solved_at_all") is not False
                or type(original.get("attempts_count")) is not int
                or original["attempts_count"] < 0
            ):
                raise ValueError("pending task identity or attempt state is inconsistent")
            report["task_before"] = original

        else:
            report["phase"] = "requesting_task"
            checkpoint(report, save, required=True)
            creation_start = monotonic()
            try:
                response, task_id = request_task(client, stage, before, report, save, start + 30.0)
            finally:
                report["task_creation_elapsed"] = monotonic() - creation_start
                report["task_creation_read_timeout"] = 5.0
                report["task_creation_retry_budget"] = 30.0
            if response is not None:
                task_id = response.task_id
            if task_id and task_id in before["listed_task_ids"]:
                report["task_id"] = task_id
                raise ValueError(
                    "Create response names an existing task; inspect inventory before proceeding."
                )
            report["reused_existing_task"] = False
        report.update(task_id=task_id, phase="reading_task")
        checkpoint(report, save, required=True)
        if not recovering and monotonic() - start >= 30.0:
            raise TimeoutError("task acquisition window exhausted; nothing submitted")
        task = client.get_task(stage, task_id)
        if not task.ok or task.id != task_id:
            raise ValueError("task response does not match the selected task")
        level = task.level.model_dump()
        report.update(level=level, phase="solving")
        checkpoint(report, save, required=True)
        seconds = 24.0 if recovering else min(24.0, 29.0 - (monotonic() - start) - 4.0)
        if seconds <= 0:
            raise TimeoutError("no local solve budget remains")
        result = solver(level, seconds)
        report.update(solver=result, phase="validating")
        checkpoint(report, save, required=True)
        if result["status"] != "FEASIBLE" or not result.get("plan"):
            raise ValueError("no independently validated winning plan; nothing submitted")
        report["strict_replay"] = validate_local(level, result["plan"], stage)
        api_plan = [[Action.model_validate(action) for action in turn] for turn in result["plan"]]
        report.update(phase="submitting", elapsed_before_submit=monotonic() - start)
        checkpoint(report, save, required=True)
        if recovering:
            fresh = preflight(client, allow_complete=True, stage=stage)
            latest = client.get_tasks(stage)
            latest_input = client.get_task(stage, task_id)
            matches = [t.model_dump() for t in latest.tasks if t.id == task_id]
            if (
                fresh["pending_task_ids"] != [task_id]
                or loop_progress(fresh["progress_before"]) != snapshot
                or not latest.ok
                or len(matches) != 1
                or matches[0] != original
                or not latest_input.ok
                or latest_input.id != task_id
                or latest_input.level.model_dump() != level
            ):
                raise ValueError("pending task or progress changed before recovery submission")
        # Fresh tasks reserve transport time; cleanup keeps its original server clock.
        if not recovering and monotonic() - start >= 26.0:
            raise TimeoutError("submission reserve exhausted; nothing submitted")
        # Exactly one POST: a transport error may mean the server accepted it.
        report["submit_attempted"] = True
        response = client.submit_plan(stage, task_id, api_plan)
        report.update(
            submit_result=response.model_dump(),
            elapsed_after_submit=monotonic() - start,
            phase="submitted",
        )
        checkpoint(report, save)
    except (Exception, KeyboardInterrupt) as exc:
        # Keep evidence; ambiguous creation uses GETs, submissions are never retried.
        report.update(error_type=type(exc).__name__, failed_phase=report["phase"], phase="stopped")
        checkpoint(report, save)
    read_back(client, report)
    report["outcome"] = (
        report["verification"]["outcome"] if report["submit_attempted"] else "STOPPED"
    )
    if recover_pending and report.get("mode") == "pending-recovery" and report["submit_attempted"]:
        matches = [t for t in report.get("tasks_after", []) if t.get("id") == report["task_id"]]
        layout, (index, series) = snapshot
        counted = report["outcome"] == "COUNTED"
        next_cursor = (
            ((index, series + 1) if series + 1 < layout[index][1] else (index + 1, 0))
            if counted
            else (index, 0)
        )
        if (
            report["outcome"] not in ("COUNTED", "NOT_COUNTED")
            or (report.get("submit_result") or {}).get("ok") is False
            or len(matches) != 1
            or matches[0].get("passed") is not True
            or matches[0].get("solved_at_all") is not True
            or matches[0].get("type") != original["type"]
            or matches[0].get("attempts_count") != original["attempts_count"] + 1
            or (counted and original["attempts_count"] != 0)
            or any(t.get("solved_at_all") is not True for t in report.get("tasks_after", []))
            or report.get("progress_verification_error_type")
            or loop_progress(report.get("progress_after")) != (layout, next_cursor)
        ):
            report.update(
                outcome="UNKNOWN", message="Recovery not fully verified; no new task created."
            )
        elif not counted:
            report.update(
                outcome="RECOVERED",
                message="Pending task passed; series reset verified. This cleanup did not count.",
            )
    report["elapsed_total"] = monotonic() - start
    checkpoint(report, save)
    return report


def run_one(client, before, token, solver=solve_local, *, recover_pending=False):
    """Keep one attempt and its original input/plan in a private temporary receipt directory."""
    directory = Path(tempfile.mkdtemp(prefix="blade-runner-live-"))

    def save(value):
        (directory / "attempt.json").write_text(json.dumps(redact(value, token), indent=2) + "\n")

    report = attempt(client, before, save, solver, recover_pending=recover_pending)
    report["record_path"] = str(directory / "attempt.json")
    if report["outcome"] == "STOPPED":
        report["message"] = (
            "Stopped at " + report.get("failed_phase", "unknown") + "; no submission was attempted."
        )
    checkpoint(report, save)
    return report


def loop_progress(progress):
    """Validate the finite level/series cursor; incomplete data cannot drive POSTs."""
    if not progress or progress.get("ok") is not True:
        return None
    order, items = progress.get("order"), progress.get("items")
    if (
        not isinstance(order, list)
        or not order
        or any(type(x) is not str for x in order)
        or len(set(order)) != len(order)
        or not isinstance(items, list)
        or len(items) != len(order)
        or any(not isinstance(x, dict) for x in items)
    ):
        return None
    by_type = {x.get("type"): x for x in items}
    if set(by_type) != set(order):
        return None
    index = progress.get("current_index")
    if index is None and all(x.get("status") == "done" for x in items):
        index = len(order)
    if type(index) is not int or not 0 <= index <= len(order):
        return None
    layout = []
    for i, name in enumerate(order):
        item = by_type[name]
        total, series = item.get("series_total"), item.get("series_index")
        if type(total) is not int or total <= 0 or type(series) is not int:
            return None
        expected = "done" if i < index else "current" if i == index else "locked"
        allowed = {expected}
        # The server uses ready_for_gate both at a fresh series and after a
        # counted partial-series task. The label is not countedness evidence;
        # task flags and the exact numeric cursor still own continuation.
        if i == index:
            allowed.add("ready_for_gate")
        if item.get("status") not in allowed or item.get("is_current") is not (i == index):
            return None
        if (
            (i < index and series != total)
            or (i == index and not 0 <= series < total)
            or (i > index and series != 0)
        ):
            return None
        layout.append((name, total))
    series = by_type[order[index]]["series_index"] if index < len(order) else 0
    return tuple(layout), (index, series)


def run_loop(client, token, emit=None, solver=solve_local, stage=1):
    """Only an exact verified series step permits another task in the selected stage."""
    summary = {"stage": stage, "mode": "loop", "counted_tasks": 0, "task_results": []}
    expected_snapshot = None
    startup = True

    def finish(outcome, message):
        summary.update(outcome=outcome, message=message)
        return summary

    while True:
        try:
            before = preflight(client, allow_complete=True, stage=stage)
        except (Exception, KeyboardInterrupt) as exc:
            if isinstance(exc, KeyboardInterrupt):
                return finish(
                    "STOPPED", "Interrupted during readiness check; no next task created."
                )
            return finish(
                "ERROR",
                "Readiness check failed (" + type(exc).__name__ + "); no next task created.",
            )
        summary["progress_after"] = before["progress_before"]
        snapshot = loop_progress(before["progress_before"])
        if snapshot is None or (expected_snapshot is not None and snapshot != expected_snapshot):
            return finish(
                "UNKNOWN",
                "Progress is missing, inconsistent or changed since verification; stopped.",
            )
        layout, (index, series) = snapshot
        recovering = startup and bool(before["pending_task_ids"])
        if before["pending_task_ids"] and not recovering:
            summary["task_id"] = before["pending_task_ids"][0]
            return finish("STOPPED", "Unexpected pending task; no next task created.")
        if index == len(layout):
            if before["pending_task_ids"]:
                return finish(
                    "UNKNOWN", "Completed progress conflicts with a pending task; no writes."
                )
            return finish(
                "COMPLETE",
                "Stage1 complete. No Stage2 task requested."
                if stage == 1
                else f"Stage{stage} complete. No later-stage task requested.",
            )
        try:
            startup = False
            report = run_one(client, before, token, solver, recover_pending=recovering)
        except (Exception, KeyboardInterrupt) as exc:
            return finish(
                "STOPPED" if isinstance(exc, KeyboardInterrupt) else "ERROR",
                "Task execution stopped ("
                + type(exc).__name__
                + "); inspect private receipts; no automatic retry.",
            )
        summary["task_id"] = report.get("task_id")
        summary["task_results"].append(
            {
                key: report[key]
                for key in ("task_id", "outcome", "verification", "record_path")
                if key in report
            }
        )
        summary["counted_tasks"] += int(report["outcome"] == "COUNTED")
        summary["progress_after"] = report.get("progress_after") or before["progress_before"]
        if emit:
            emit(report)
        if report.get("error_type") == "KeyboardInterrupt":
            return finish(
                "STOPPED", "Interrupted; inspect the last task with --verify before resuming."
            )
        if report["outcome"] == "RECOVERED":
            if report.get("checkpoint_error_type"):
                return finish(
                    "STOPPED", "Recovery passed but receipt write failed; no next task created."
                )
            expected_snapshot = (layout, (index, 0))
            continue
        if report["outcome"] != "COUNTED":
            return finish(
                report["outcome"],
                "Stopped after the last task; "
                + (
                    report.get("message")
                    or report.get("verification", {}).get("reason", "inspect its receipt.")
                ),
            )
        if report.get("checkpoint_error_type"):
            return finish("STOPPED", "Task counted but receipt write failed; no next task created.")
        credited = [
            t for t in report.get("tasks_after", []) if t.get("id") == report.get("task_id")
        ]
        next_cursor = (index, series + 1) if series + 1 < layout[index][1] else (index + 1, 0)
        expected_snapshot = (layout, next_cursor)
        if (
            len(credited) != 1
            or credited[0].get("type") != layout[index][0]
            or loop_progress(report.get("progress_after")) != expected_snapshot
        ):
            return finish(
                "UNKNOWN",
                "Task counted but its expected series advancement was not verified; stopped.",
            )
        # Fresh preflight on the next iteration must agree before another create.


def main(argv=None, client_factory=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--solver-child", action="store_true", help=argparse.SUPPRESS)
    modes.add_argument(
        "--offline-smoke", action="store_true", help="test solver/replay locally; no network"
    )
    modes.add_argument("--check", action="store_true", help="read-only readiness check (default)")
    modes.add_argument(
        "--submit-one",
        action="store_true",
        help="create/solve/submit ONE fresh task in the selected stage",
    )
    modes.add_argument(
        "--loop",
        action="store_true",
        help="recover one pending task at startup, then continue verified passes until complete or stopped",
    )
    modes.add_argument(
        "--verify", metavar="TASK_ID", help="GET-only check of an existing task; never resubmit"
    )
    parser.add_argument(
        "--stage",
        type=int,
        choices=(1, 2, 3),
        default=1,
        help="explicit stage (default:1); never advances into another stage",
    )
    parser.add_argument("--env", type=Path, default=APP_ROOT / ".env")
    parser.add_argument("--json", action="store_true", help="print a machine-readable result")
    args = parser.parse_args(argv)
    if args.solver_child:
        solver_child()
        return 0
    if args.offline_smoke:
        case = json.loads((ROOT / "samples.json").read_text())[str(args.stage)]
        result = solve_local(case["level"], 1, stage=args.stage)
        assert result["status"] == "FEASIBLE" and result["strict_replay"]
        display(
            {
                "outcome": "OFFLINE_OK",
                "message": "Solver / strict replay / JSON plan path passed. No network.",
            },
            args.json,
        )
        return 0
    from dotenv import dotenv_values

    if client_factory is None:
        from api_client.client import GameClient

        client_factory = GameClient
    token = ""
    try:
        config = {**dotenv_values(args.env), **os.environ}
        token = config.get("GAME_SERVER_TOKEN") or config.get("ARBITER_TOKEN")
        base = config.get("GAME_SERVER_BASE_URL") or config.get("ARBITER_BASE_URL")
        if not token or not base:
            raise ValueError(
                "Configure GAME_SERVER_TOKEN and GAME_SERVER_BASE_URL in the ignored .env file."
            )
        parsed = urlsplit(base)
        origin = (
            parsed.scheme,
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
        )
        if (
            origin not in {("https", "bladerunner.reef.pl", 443), ("http", "172.237.120.135", 80)}
            or parsed.username
            or parsed.password
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Configured origin is not documented by the project/starter.")
        with client_factory(base, token, timeout=3.0) as client:
            if args.verify:
                report = {"stage": args.stage, "mode": "verify", "task_id": args.verify}
                read_back(client, report)
                report["outcome"] = report["verification"]["outcome"]
            elif args.loop:
                report = run_loop(
                    client,
                    token,
                    emit=None if args.json else lambda r: display(r, token=token),
                    stage=args.stage,
                )
            else:
                before = preflight(client, stage=args.stage)
                if not args.submit_one:
                    pending = before["pending_task_ids"]
                    report = {
                        "outcome": "READY" if not pending else "STOPPED",
                        **before,
                        "message": "Ready. No task created or submitted."
                        if not pending
                        else "Existing pending task requires inspection; no task created or submitted.",
                    }
                else:
                    report = run_one(client, before, token)
    except KeyboardInterrupt:
        report = {
            "outcome": "STOPPED",
            "message": "Interrupted; inspect the latest private blade-runner-live-* receipt and use --verify before resuming.",
        }
    except Exception as exc:
        # Known local validation messages are authored here; network exceptions
        # expose type only (never headers, token, or untrusted response text).
        report = {
            "outcome": "ERROR",
            "message": str(exc)
            if isinstance(exc, ValueError)
            else type(exc).__name__ + ": operation failed; no automatic retry.",
        }
    display(report, args.json, token or "")
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
