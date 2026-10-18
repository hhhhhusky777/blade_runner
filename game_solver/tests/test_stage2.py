"""Typed resource/funding boundaries retained from the independent research tests."""

from collections import deque
import unittest
from solver.stage2 import (
    CapitalDP,
    VARIANTS,
    solve,
)
from solver.stage2_reference import validate_plan, oracle


def level(stone=16, ore=0, goal=None, turns=2, nodes=None, width=3, height=1):
    return {
        "board": {
            "width": width,
            "height": height,
            "grid": [["GRASS"] * width for _ in range(height)],
            "resource_nodes": nodes
            if nodes is not None
            else [{"x": 2, "y": 0, "resource": "IRON_ORE"}],
        },
        "structures": [
            {"type": "BASE", "x": 0, "y": 0, "storage": {"STONE": stone, "IRON_ORE": ore}}
        ],
        "level_goal": {
            "target_structure_type": "BASE",
            "target_resources": goal or {"IRON_ORE": 10},
        },
        "max_turns": turns,
    }


def forward_economy(d, qs, qo, stone, ore, gs, go, ks, ko):
    """Forward enumeration, not the candidate backward threshold recurrence."""
    initial = d, qs, qo, stone, ore
    seen, queue = {initial}, deque([initial])
    while queue:
        remaining, q, m, capital, output = queue.popleft()
        if capital >= gs and output >= go:
            return True
        children = []
        if remaining:
            children.append((remaining - 1, q, m, capital + 5 * q, output + 5 * m))
        if q < ks and capital >= 10:
            children.append((remaining, q + 1, m, capital - 5, output))
        if m < ko and capital >= 15:
            children.append((remaining, q, m + 1, capital - 15, output + 5))
        for child in children:
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return False


class Stage2Tests(unittest.TestCase):
    def test_final_turn_and_ore_wait(self):
        for turns, goal in ((1, 5), (2, 10)):
            task = level(turns=turns, goal={"IRON_ORE": goal})
            for variant in VARIANTS:
                answer = solve(task, variant)
                self.assertEqual(answer["status"], "FEASIBLE")
                replay = validate_plan(task, answer["plan"])
                self.assertEqual(replay["base_iron_ore"], goal)
                self.assertEqual(replay["base_stone"], 0)
                self.assertEqual(replay["turns"], turns)

    def test_ore_cannot_pay_for_construction(self):
        task = level(stone=15, ore=100, goal={"IRON_ORE": 105}, turns=1)
        for variant in VARIANTS:
            self.assertEqual(solve(task, variant)["status"], "INFEASIBLE")
        self.assertEqual(oracle(task)["status"], "INFEASIBLE")

    def test_common_wait_for_mixed_goals(self):
        task = level(
            stone=27,
            goal={"STONE": 10, "IRON_ORE": 10},
            turns=3,
            width=3,
            height=3,
            nodes=[{"x": 2, "y": 0, "resource": "STONE"}, {"x": 0, "y": 2, "resource": "IRON_ORE"}],
        )
        for variant in VARIANTS:
            answer = solve(task, variant)
            self.assertEqual(answer["status"], "FEASIBLE")
            r = validate_plan(task, answer["plan"])
            self.assertGreaterEqual(r["base_stone"], 10)
            self.assertGreaterEqual(r["base_iron_ore"], 10)

    def test_initial_goal_and_zero_turns(self):
        task = level(stone=5, ore=6, goal={"STONE": 5, "IRON_ORE": 6})
        self.assertEqual(solve(task)["status"], "FEASIBLE")
        task["max_turns"] = 0
        self.assertEqual(solve(task)["status"], "INFEASIBLE")

    def test_caps_are_unknown(self):
        task = level()
        self.assertEqual(solve(task, seconds=0)["status"], "UNKNOWN")
        self.assertEqual(solve(task, max_states=1, use_probe=False)["status"], "UNKNOWN")
        self.assertEqual(oracle(task, seconds=0)["status"], "UNKNOWN")
        self.assertEqual(oracle(task, max_states=1)["status"], "UNKNOWN")

    def test_dp_against_forward_enumeration(self):
        decisions = 0
        for ks, ko in ((0, 1), (1, 0), (1, 1), (2, 2)):
            for gs, go in ((0, 1), (0, 10), (7, 6), (13, 0)):
                dp = CapitalDP(gs, ks, ko)
                for d in range(3):
                    for qs in range(ks + 1):
                        for qo in range(ko + 1):
                            for ore in (0, 1, 4, 6):
                                threshold = dp.required(d, qs, qo, (max(0, go - ore) + 4) // 5)
                                for cash in (0, 5, 9, 10, 14, 15, 19, 25):
                                    expected = forward_economy(d, qs, qo, cash, ore, gs, go, ks, ko)
                                    self.assertEqual(
                                        cash >= threshold,
                                        expected,
                                        (d, qs, qo, cash, ore, gs, go, ks, ko, threshold),
                                    )
                                    decisions += 1
        self.assertEqual(decisions, 6528)
