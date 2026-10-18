"""Behavioral checks independent of research imports and live game access."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from solver.capital import investment_thresholds
from solver.reference import oracle, validate_plan
from solver.stage1 import Model, State, road_parameters
from solver.stage1_preset import InvestmentModel, solve

FIXTURES = json.loads((Path(__file__).parent / "fixtures/stage1-basic.json").read_text())["cases"]


def level(cash=11, goal=15, turns=3):
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


def relaxed_maximum(cash, quarries, sites, remaining):
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
    def test_thresholds_match_independent_forward_relaxation(self):
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

    def test_tiny_raw_oracle_and_deadline_outcomes(self):
        for task in (level(), level(cash=10)):
            expected = oracle(task, seconds=3, max_states=50000)
            actual = solve(task, seconds=3)
            self.assertNotEqual(expected["status"], "UNKNOWN")
            self.assertEqual(actual["status"], expected["status"])
            if actual["plan"] is not None:
                validate_plan(task, actual["plan"])
        self.assertEqual(solve(level(), seconds=0)["status"], "UNKNOWN")

    def test_all_fixed_basic_plans_replay_without_input_mutation(self):
        for case in FIXTURES:
            with self.subTest(case=case["id"]):
                task = copy.deepcopy(case["level"])
                result = solve(task, seconds=5)
                self.assertNotEqual(result["status"], "UNKNOWN")
                self.assertEqual(task, case["level"])
                if result["plan"] is not None:
                    validate_plan(task, result["plan"])

    def test_topology_cache_immutable_and_per_model(self):
        model = InvestmentModel(level())
        state = model.step(model.initial(), 1)
        tree = model.tree(state)
        changed = State(state.turn + 1, state.roads, state.quarries, state.cash + 20, (7,))
        self.assertIs(tree, model.tree(changed))
        self.assertEqual(dict(tree), Model(level()).tree(state))
        with self.assertRaises(TypeError):
            tree[0] = -1
        other = InvestmentModel(level())
        self.assertIsNot(tree, other.tree(state))

    def test_failed_relaxation_cannot_remove_tiny_real_win(self):
        from functools import cache

        task = level()
        model = InvestmentModel(task)
        parameters = road_parameters(model)

        @cache
        def wins(state):
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

    def test_import_does_not_change_network_or_environment(self):
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
