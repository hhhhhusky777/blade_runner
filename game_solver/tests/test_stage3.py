"""Raw production semantics and independently enumerated tiny truth."""

from copy import deepcopy
from functools import lru_cache
from collections.abc import Iterable
from typing import Any
import unittest
from solver.stage3 import Model, Bounds, ProductionDP, State, solve
from solver.stage3_reference import read_level, initial, apply, validate_plan, oracle
from solver.reference import _action


def level(
    w: int = 5,
    h: int = 3,
    stone: int = 40,
    ore: int = 0,
    iron: int = 0,
    goal: dict[str, int] | None = None,
    turns: int = 3,
    nodes: Iterable[tuple[int, int, str]] = (),
) -> dict[str, Any]:
    """Build a compact production task with explicit inventories and resource sites."""
    return dict(
        spec_number=3,
        max_turns=turns,
        board=dict(
            width=w,
            height=h,
            grid=[["GRASS"] * w for _ in range(h)],
            resource_nodes=[dict(x=x, y=y, resource=r) for x, y, r in nodes],
        ),
        structures=[
            dict(type="BASE", x=0, y=0, storage=dict(STONE=stone, IRON_ORE=ore, IRON=iron))
        ],
        level_goal=dict(target_structure_type="BASE", target_resources=goal or {"IRON": 4}),
    )


class Stage3Tests(unittest.TestCase):
    def test_production_rate_input_location_and_activation(self) -> None:
        """Consume ore at the smelter, at most once per turn, including partial batches."""
        task = level(w=3, h=1, stone=21, ore=5, goal={"IRON": 5}, turns=3)
        model = read_level(task)
        s = initial(model)
        for a in (
            _action("BUILD", x=1, y=0, type="ROAD"),
            _action("BUILD", x=2, y=0, type="SMELTER"),
        ):
            apply(model, s, a)
        with self.assertRaises(ValueError):
            apply(model, s, _action("PRODUCE", x=2, y=0))
        apply(
            model,
            s,
            _action("TRANSFER", path=[[0, 0], [1, 0], [2, 0]], resource="IRON_ORE", amount=5),
        )
        apply(model, s, _action("PRODUCE", x=2, y=0))
        self.assertEqual(s.inventory[2, 0], (0, 3, 2))
        with self.assertRaises(ValueError):
            apply(model, s, _action("PRODUCE", x=2, y=0))
        s.mined.clear()
        apply(model, s, _action("PRODUCE", x=2, y=0))
        self.assertEqual(s.inventory[2, 0], (0, 1, 4))
        s.mined.clear()
        apply(model, s, _action("PRODUCE", x=2, y=0))
        self.assertEqual(s.inventory[2, 0], (0, 0, 5))

    def test_partial_feed_preserves_ore_goal(self) -> None:
        """Feed only spare ore so an iron conversion cannot destroy the ore target."""
        task = level(w=3, h=1, stone=21, ore=3, goal={"IRON": 1, "IRON_ORE": 2}, turns=1)
        a = solve(task, seconds=2)
        self.assertEqual(a["status"], "FEASIBLE")
        for mode in ("matching", "unrestricted"):
            self.assertEqual(validate_plan(task, a["plan"], mode)["base_inventory"]["IRON_ORE"], 2)
        bad = deepcopy(a["plan"])
        feed = next(
            x
            for turn in bad
            for x in turn
            if x["action"] == "TRANSFER" and x["args"]["resource"] == "IRON_ORE"
        )
        feed["args"]["amount"] = 3
        with self.assertRaises(ValueError):
            validate_plan(task, bad)

    def test_tiny_raw_oracle_matches_all_four_variants(self) -> None:
        """Require every pruning configuration to agree with raw-action tiny-case truth."""
        for ore, iron_goal, ore_goal, stone, turns in [
            (3, 1, 2, 21, 1),
            (3, 2, 2, 21, 1),
            (3, 3, 0, 21, 1),
            (3, 3, 0, 21, 2),
            (1, 1, 0, 20, 3),
            (0, 1, 0, 100, 2),
            (1, 1, 0, 21, 1),
            (4, 3, 1, 21, 2),
        ]:
            task = level(
                w=3,
                h=1,
                stone=stone,
                ore=ore,
                goal={"IRON": iron_goal, "IRON_ORE": ore_goal},
                turns=turns,
            )
            truth = oracle(task, seconds=5)
            self.assertNotEqual(truth["status"], "UNKNOWN")
            for variant in ("none", "resource", "dp", "both"):
                with self.subTest(
                    ore=ore, goal=(iron_goal, ore_goal), stone=stone, turns=turns, variant=variant
                ):
                    answer = solve(task, seconds=5, bounds=variant)
                    self.assertEqual(answer["status"], truth["status"])
                    if answer["plan"]:
                        validate_plan(task, answer["plan"])

    def test_every_tiny_winning_continuation_survives_both_filters(self) -> None:
        """Check every enumerated winning state against both resource and capital bounds."""
        task = level(w=3, h=1, stone=21, ore=3, goal={"IRON": 1, "IRON_ORE": 2}, turns=2)
        m = Model(task)
        b = Bounds(m, float("inf"))
        states = set()

        @lru_cache(None)
        def winning(s: State) -> bool:
            """Record the tiny reachable graph and establish each state's winning truth."""
            states.add(s)
            children = [m.step(s, c)[0] for c in m.choices(s)]
            results = [winning(child) for child in children]
            return m.won(s) or any(results)

        self.assertTrue(winning(m.initial()))
        self.assertGreater(len(states), 10)
        for s in states:
            if winning(s):
                self.assertTrue(b.resource(s), s)
                self.assertTrue(b.capital(s), s)

    def test_storage_is_not_transport_and_node_placement_is_checked(self) -> None:
        """Require explicit storage relays and reject smelters placed on resource nodes."""
        task = level(w=5, h=1, stone=100, ore=3, goal={"IRON": 1}, turns=1)
        model = read_level(task)
        s = initial(model)
        for x, kind in ((1, "ROAD"), (2, "SMELTER"), (3, "ROAD"), (4, "SMELTER")):
            apply(model, s, _action("BUILD", x=x, y=0, type=kind))
        with self.assertRaises(ValueError):
            apply(
                model,
                s,
                _action(
                    "TRANSFER",
                    path=[[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]],
                    resource="IRON_ORE",
                    amount=1,
                ),
            )
        # Split at the Storage endpoint is legal.
        apply(
            model,
            s,
            _action("TRANSFER", path=[[0, 0], [1, 0], [2, 0]], resource="IRON_ORE", amount=1),
        )
        apply(
            model,
            s,
            _action("TRANSFER", path=[[2, 0], [3, 0], [4, 0]], resource="IRON_ORE", amount=1),
        )
        task = level(stone=100, nodes=[(1, 0, "STONE")])
        model = read_level(task)
        s = initial(model)
        with self.assertRaises(ValueError):
            apply(model, s, _action("BUILD", x=1, y=0, type="SMELTER"))

    def test_malformed_inputs_do_not_silently_become_empty_inventory(self) -> None:
        """Reject malformed inventories, structure lists, and missing goals explicitly."""
        storage: object
        for storage in (0, False, [], ""):
            task = level()
            task["structures"][0]["storage"] = storage
            with self.assertRaises(ValueError):
                read_level(task)
        for structures in (None, [], [None]):
            task = level()
            task["structures"] = structures
            with self.assertRaises(ValueError):
                read_level(task)
        task = level()
        del task["level_goal"]
        with self.assertRaises(ValueError):
            read_level(task)

    def test_raw_oracle_covers_mining_income_and_remote_pool_merge(self) -> None:
        """Check funding and remote resource merges against independent raw actions."""
        cases = [
            level(w=3, h=1, stone=11, goal={"STONE": 12}, turns=3, nodes=[(2, 0, "STONE")]),
            level(w=3, h=1, stone=11, goal={"STONE": 12}, turns=2, nodes=[(2, 0, "STONE")]),
            level(w=3, h=1, stone=15, goal={"IRON_ORE": 1}, turns=2, nodes=[(2, 0, "IRON_ORE")]),
            level(w=3, h=2, stone=36, goal={"IRON": 1}, turns=1, nodes=[(2, 0, "IRON_ORE")]),
            level(w=3, h=2, stone=35, goal={"IRON": 1}, turns=1, nodes=[(2, 0, "IRON_ORE")]),
            level(w=3, h=2, stone=38, goal={"IRON": 1}, turns=1, nodes=[(1, 0, "IRON_ORE")]),
        ]
        for task in cases:
            truth = oracle(task, seconds=5)
            self.assertNotEqual(truth["status"], "UNKNOWN")
            for variant in ("none", "resource", "dp", "both"):
                answer = solve(task, seconds=5, bounds=variant, probes=False)
                self.assertEqual(answer["status"], truth["status"])
                if answer["plan"]:
                    validate_plan(task, answer["plan"])

    def test_deadline_is_unknown_and_zero_turn_cannot_claim(self) -> None:
        """Separate deadline exhaustion, invalid budgets, and an illegal zero-turn claim."""
        self.assertEqual(solve(level(), seconds=0)["status"], "UNKNOWN")
        self.assertEqual(solve(level(iron=5, turns=0))["status"], "INFEASIBLE")
        for seconds in (-1, True, float("inf")):
            with self.assertRaises(ValueError):
                solve(level(), seconds=seconds)

    def test_capital_dp_detects_no_first_investment_despite_future_supply(self) -> None:
        """Reject an economy with optimistic future output but no affordable first build."""
        task = level(w=3, h=2, stone=9, ore=2, goal={"IRON": 1}, turns=5, nodes=[(2, 0, "STONE")])
        self.assertEqual(oracle(task, seconds=5)["status"], "INFEASIBLE")
        m = Model(task)
        b = Bounds(m, float("inf"))
        self.assertTrue(b.resource(m.initial()))
        self.assertFalse(b.capital(m.initial()))
        answer = solve(task, seconds=2, bounds="both")
        self.assertEqual((answer["status"], answer["reason"]), ("INFEASIBLE", "initial_bound"))

    def test_dp_budget_exhaustion_weakens_filter(self) -> None:
        """Keep a state when the capital bound runs out of computation budget."""
        m = Model(level())
        b = Bounds(m, float("-inf"))
        self.assertTrue(b.capital(m.initial()))
        self.assertTrue(any(d.skipped for d in b.dps.values()))

    def test_on_demand_dp_and_budget_skip(self) -> None:
        """Avoid root DP for quick wins and keep skipped production bounds conservative."""
        from unittest.mock import patch

        task = level(w=3, h=1, stone=21, ore=1, goal={"IRON": 1}, turns=1)
        with patch.object(Bounds, "production", side_effect=AssertionError("root wins need no DP")):
            result = solve(task, seconds=5)
        self.assertEqual(result["status"], "FEASIBLE")
        self.assertEqual(result["production_dp_queries"], 0)
        with patch.object(ProductionDP, "required", return_value=0):
            result = solve(task, seconds=5, probes=False)
        self.assertEqual(result["status"], "FEASIBLE")
        self.assertEqual(result["production_dp_activations"], 1)
        self.assertEqual(result["production_prunes"], 0)
