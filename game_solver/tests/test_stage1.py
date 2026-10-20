"""Behavioral checks independent of research imports and live game access."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
import unittest
from unittest.mock import patch

from solver.api import solve as solve_public
from solver.capital import investment_thresholds
from solver.reference import oracle, validate_plan
from solver.stage1 import Model, State, road_parameters
from solver.stage1_preset import InvestmentModel, solve

FIXTURES = json.loads((Path(__file__).parent / "fixtures/stage1-basic.json").read_text())["cases"]


def level(cash: int = 11, goal: int = 15, turns: int = 3) -> dict[str, Any]:
    """Build a minimal road-and-quarry task with adjustable funding and horizon."""
    return {
        "board": {
            "width": 3,
            "height": 1,
            "grid": [["GRASS"] * 3],
            "resource_nodes": [{"x": 2, "y": 0, "resource": "STONE"}],
        },
        "structures": [{"type": "BASE", "x": 0, "y": 0, "storage": {"STONE": cash}}],
        "level_goal": {"target_structure_type": "BASE", "target_resources": {"STONE": goal}},
        "max_turns": turns,
    }


def relaxed_maximum(cash: int, quarries: int, sites: int, remaining: int) -> int:
    """Forward atomic enumeration; independent of the threshold recurrence."""
    seen, pending, maximum = set(), [(cash, quarries, remaining)], cash
    while pending:
        state = pending.pop()
        if state in seen:
            continue
        seen.add(state)
        cash, quarries, remaining = state
        maximum = max(maximum, cash)
        if quarries < sites and cash >= 10:
            pending.append((cash - 5, quarries + 1, remaining))
        if remaining:
            pending.append((cash + 5 * quarries, quarries, remaining - 1))
    return maximum


class Stage1Tests(unittest.TestCase):
    def test_stage_entry_rejects_an_invalid_search_candidate(self) -> None:
        """Reject an unearned win through both the preset and public entry points."""
        invalid = {
            "status": "FEASIBLE",
            "reason": "one_quarry_completion",
            "plan": [[{"action": "CLAIM_WIN", "args": {"x": 0, "y": 0}}]],
        }
        for entry in (solve, solve_public):
            with self.subTest(entry=entry.__module__):
                # Fault injection preserves real replay: the search falsely
                # claims victory while BASE stock is still below the goal.
                with patch("solver.stage1_preset.search_core", return_value=invalid):
                    with self.assertRaisesRegex(ValueError, "BASE goal inventory"):
                        entry(level())

    def test_thresholds_match_independent_forward_relaxation(self) -> None:
        """Check all 20,925 small economic decisions against a forward enumerator."""
        comparisons = 0
        goals = (0, 1, 5, 10, 15, 25, 30, 40, 60)
        for sites in range(5):
            tables = {g: investment_thresholds(g, sites, 5) for g in goals}
            for remaining in range(5):
                for quarries in range(sites + 1):
                    for cash in range(31):
                        maximum = relaxed_maximum(cash, quarries, sites, remaining)
                        for goal in goals:
                            self.assertEqual(
                                cash >= tables[goal][remaining][quarries], maximum >= goal
                            )
                            comparisons += 1
        self.assertEqual(comparisons, 20925)

    def test_tiny_raw_oracle_and_deadline_outcomes(self) -> None:
        """Match raw-action truth and distinguish an expired deadline from impossibility."""
        for task in (level(), level(cash=10)):
            expected = oracle(task, seconds=3, max_states=50000)
            actual = solve(task, seconds=3)
            self.assertNotEqual(expected["status"], "UNKNOWN")
            self.assertEqual(actual["status"], expected["status"])
            if actual["plan"] is not None:
                validate_plan(task, actual["plan"])
        self.assertEqual(solve(level(), seconds=0)["status"], "UNKNOWN")

    def test_all_fixed_basic_plans_replay_without_input_mutation(self) -> None:
        """Require valid fixed-fixture plans while preserving the caller's task data."""
        for case in FIXTURES:
            with self.subTest(case=case["id"]):
                task = copy.deepcopy(case["level"])
                result = solve(task, seconds=5)
                self.assertNotEqual(result["status"], "UNKNOWN")
                self.assertEqual(task, case["level"])
                if result["plan"] is not None:
                    validate_plan(task, result["plan"])

    def test_topology_cache_immutable_and_per_model(self) -> None:
        """Reuse topology only within a model and expose no mutable cached tree."""
        model = InvestmentModel(level())
        state = model.step(model.initial(), 1)
        tree = model.tree(state)
        changed = State(state.turn + 1, state.roads, state.quarries, state.cash + 20, (7,))
        self.assertIs(tree, model.tree(changed))
        self.assertEqual(dict(tree), Model(level()).tree(state))
        with self.assertRaises(TypeError):
            # Deliberately attempt mutation to verify the read-only cache contract.
            tree[0] = -1  # type: ignore[index]
        other = InvestmentModel(level())
        self.assertIsNot(tree, other.tree(state))

    def test_failed_relaxation_cannot_remove_tiny_real_win(self) -> None:
        """Ensure the optimistic road bound never rejects a genuinely winning state."""
        from functools import cache

        task = level()
        model = InvestmentModel(task)
        parameters = road_parameters(model)

        @cache
        def wins(state: State) -> bool:
            """Enumerate every continuation to establish independent winning truth."""
            return state.cash >= model.goal or any(
                wins(model.step(state, cell)) for cell in model.choices(state)
            )

        seen, pending = set(), [model.initial()]
        while pending:
            state = pending.pop()
            if state in seen:
                continue
            seen.add(state)
            if model.road_bound(state, parameters) < model.goal:
                self.assertFalse(wins(state))
            pending.extend(model.step(state, cell) for cell in model.choices(state))

    def test_import_does_not_change_network_or_environment(self) -> None:
        """Keep solver imports free of process-wide network or environment side effects."""
        code = """import os, socket, ssl, sys
before = (socket.socket, socket.create_connection, dict(os.environ))
from solver import stage1_preset, stage2_reference, stage3_reference
assert before == (socket.socket, socket.create_connection, dict(os.environ))
assert not any(name in sys.modules for name in ('run', 'memory_benchmark', 'cache_benchmark'))
ssl.create_default_context()
"""
        subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )


if __name__ == "__main__":
    unittest.main()
