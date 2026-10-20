"""Typed resource/funding boundaries retained from the independent research tests."""

from collections import deque
from copy import deepcopy
from functools import partial
from random import Random
from typing import Any
import unittest
from unittest.mock import patch
from solver.stage1 import connection_routes
from solver.stage2 import (
    CapitalDP,
    Model,
    RouteTree,
    State,
    VARIANTS,
    resource_possible,
    scalar_possible,
    solve,
)
from solver.stage2_reference import validate_plan, oracle


def level(
    stone: int = 16,
    ore: int = 0,
    goal: dict[str, int] | None = None,
    turns: int = 2,
    nodes: list[dict[str, int | str]] | None = None,
    width: int = 3,
    height: int = 1,
) -> dict[str, Any]:
    """Build a small mining task with independent construction and goal resources."""
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


def forward_economy(
    d: int, qs: int, qo: int, stone: int, ore: int, gs: int, go: int, ks: int, ko: int
) -> bool:
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


def cardinal_neighbors(cell: int, width: int, cells: int) -> tuple[int, ...]:
    """Reconstruct the original up/down/left/right order without candidate caches."""
    return tuple(
        neighbor
        for neighbor in (
            cell - width if cell >= width else -1,
            cell + width if cell + width < cells else -1,
            cell - 1 if cell % width else -1,
            cell + 1 if cell % width + 1 < width else -1,
        )
        if neighbor >= 0
    )


class ReferenceGeometry(Model):
    """Retain the original uncached transfer BFS for geometry differential checks."""

    def __init__(self, task: dict[str, Any], relay_mode: str) -> None:
        """Reuse task parsing, but reconstruct the legacy adjacency independently."""
        super().__init__(task, relay_mode)
        self.neighbors = tuple(cardinal_neighbors(p, self.w, self.v) for p in range(self.v))

    def tree(self, state: State, resource: int | None = None) -> RouteTree:
        """Apply original edge predicates in BFS order without calling candidate tree."""
        if self.relay_mode == "unrestricted":
            resource = None
        occupied = state.roads | state.quarries | (1 << self.base)
        parent: RouteTree = {self.base: None}
        queue = deque([self.base])
        while queue:
            p = queue.popleft()
            for q in self.neighbors[p]:
                if q in parent or not occupied >> q & 1:
                    continue
                if not (state.roads >> p & 1 or state.roads >> q & 1):
                    continue
                if (
                    resource is not None
                    and q in self.node_index
                    and self.resources[self.node_index[q]] != resource
                ):
                    continue
                parent[q] = p
                queue.append(q)
        return parent


def geometry_level(width: int, height: int, seed: int) -> dict[str, Any]:
    """Create a fixed seeded board with both node types and unbuilt planned roads."""
    random = Random(seed)
    cells = width * height
    sites = random.sample(range(1, cells), min(24, (cells - 1) // 3))
    task = level(
        stone=10_000,
        ore=2,
        turns=3,
        width=width,
        height=height,
        nodes=[
            {"x": p % width, "y": p // width, "resource": ("STONE", "IRON_ORE")[i % 2]}
            for i, p in enumerate(sites)
        ],
    )
    task["board"]["grid"] = [
        [
            "PLANNED_ROAD"
            if y * width + x not in sites and (y * width + x + seed) % 3 == 0
            else "GRASS"
            for x in range(width)
        ]
        for y in range(height)
    ]
    return task


def geometry_states(model: Model, seed: int) -> tuple[State, ...]:
    """Generate affordable adjacent build prefixes without consulting tree or routes."""
    random = Random(seed)
    state = model.initial()
    occupied = {model.base}
    frontier = set(cardinal_neighbors(model.base, model.w, model.v))
    second_count = min(model.v - 1, max(2, model.v // 2))
    first_count = min(second_count, max(1, model.v // 4))
    snapshots = {0: state}
    for count in range(1, second_count + 1):
        cell = random.choice(sorted(frontier))
        frontier.remove(cell)
        occupied.add(cell)
        frontier.update(
            p for p in cardinal_neighbors(cell, model.w, model.v) if p not in occupied
        )
        # advance mines a new extractor and charges its correct cost. Its raw
        # state is also the input used by plan output before free settlement.
        state = model.advance(state, cell)
        if count in (first_count, second_count):
            snapshots[count] = state
    first, second = snapshots[first_count], snapshots[second_count]
    # A-B-A revisits and turn/inventory-only changes must not reuse another tree.
    return first, model.advance(first, None), second, first, model.advance(second, None)


class Stage2GeometryTests(unittest.TestCase):
    def assert_geometry(
        self, model: Model, reference: ReferenceGeometry, state: State
    ) -> None:
        """Compare ordered geometry and stock movement against the original transfer BFS."""
        for resource in (None, 0, 1, 0, None):
            self.assertEqual(
                list(model.tree(state, resource).items()),
                list(reference.tree(state, resource).items()),
                (state.roads, state.quarries, resource),
            )
        for resource in (1, 0, 1):
            actual = model.routes(state, resource)
            # The uncapped shared helper receives the reference tree, so an
            # incorrect candidate tree cannot silently affect the route oracle.
            expected = connection_routes(reference, state, affordable_only=False, resource=resource)
            self.assertEqual(list(actual[0].items()), list(expected[0].items()))
            self.assertEqual(list(actual[1].items()), list(expected[1].items()))
        totals, stocks, income = [state.cash, state.ore], list(state.stocks), [0, 0]
        trees = [reference.tree(state, resource) for resource in (0, 1)]
        for index, cell in enumerate(reference.nodes):
            resource = reference.resources[index]
            if cell in trees[resource]:
                totals[resource] += stocks[index]
                stocks[index] = 0
                if state.quarries >> cell & 1:
                    income[resource] += 5
        self.assertEqual(
            model.settle(state),
            State(state.turn, state.roads, state.quarries, totals[0], totals[1], tuple(stocks)),
        )
        self.assertEqual(model.income(state), income)

    def test_zero_stock_settlement_preserves_later_geometry_queries(self) -> None:
        """Refresh geometry after a topology change even when settlement has no stock."""
        task = level(stone=30, width=3, height=2)
        for mode in ("matching", "unrestricted"):
            model, reference = Model(task, mode), ReferenceGeometry(task, mode)
            state = model.step(model.step(model.initial(), 1), 2)
            self.assertFalse(any(state.stocks))
            self.assert_geometry(model, reference, state)
            changed = model.advance(state, 3)
            self.assertEqual(model.settle(changed), changed)
            self.assert_geometry(model, reference, changed)
            self.assertIn(3, model.tree(changed, 1))
            self.assertEqual(model.income(changed), [0, 5])

    def test_seeded_geometry_preserves_order_across_models_and_topologies(self) -> None:
        """Cover topology/resource cache keys, inventories, planned roads and 625 cells."""
        for width, height, seed in ((1, 1, 11), (1, 7, 23), (7, 1, 47), (6, 5, 103), (25, 25, 617)):
            original = geometry_level(width, height, seed)
            swapped, plain = deepcopy(original), deepcopy(original)
            for node in swapped["board"]["resource_nodes"]:
                node["resource"] = "IRON_ORE" if node["resource"] == "STONE" else "STONE"
            plain["board"]["grid"] = [["GRASS"] * width for _ in range(height)]
            cases = [
                (Model(task, mode), ReferenceGeometry(task, mode))
                for task in (original, swapped, plain)
                for mode in ("matching", "unrestricted")
            ]
            for index, (model, reference) in enumerate([*cases, cases[0]]):
                states = geometry_states(model, seed + 1)
                with self.subTest(width=width, height=height, model=index, mode=model.relay_mode):
                    self.assert_geometry(model, reference, model.initial())
                    for state in states:
                        self.assertGreaterEqual(state.cash, 0)
                        self.assertFalse(state.roads & state.quarries)
                        self.assertFalse(state.roads & sum(1 << p for p in model.nodes))
                        self.assert_geometry(model, reference, state)

    def test_transfer_connectivity_does_not_wrap_board_rows(self) -> None:
        """Keep disconnected stocks behind storage at both row edges, including 25 by 25."""
        for width, height in ((3, 2), (25, 25)):
            for mirrored in (False, True):
                last = width * height - 1
                base, site = (last, last - 1) if mirrored else (0, 1)
                builds = (
                    [last - p for p in range(1, width + 1)]
                    if mirrored
                    else list(range(1, width + 1))
                )
                task = level(
                    stone=1_000,
                    width=width,
                    height=height,
                    nodes=[{"x": site % width, "y": site // width, "resource": "STONE"}],
                )
                task["structures"][0].update(x=base % width, y=base // width)
                for mode in ("matching", "unrestricted"):
                    model, reference = Model(task, mode), ReferenceGeometry(task, mode)
                    state = model.initial()
                    for cell in builds:
                        state = model.advance(state, cell)
                    with self.subTest(width=width, mirrored=mirrored, mode=mode):
                        self.assert_geometry(model, reference, state)
                        adjacent = last - width if mirrored else width
                        self.assertEqual(list(model.tree(state)), [base, adjacent])
                        self.assertEqual(model.settle(state), state)
                        self.assertEqual(model.income(state), [0, 0])

    def test_storage_adjacency_requires_road_and_preserves_parent_order(self) -> None:
        """Reject direct storage edges even when a longer road path reaches one endpoint."""
        task = level(
            stone=100,
            width=3,
            height=2,
            nodes=[{"x": 1, "y": 0, "resource": "STONE"}, {"x": 2, "y": 0, "resource": "STONE"}],
        )
        for mode in ("matching", "unrestricted"):
            model, reference = Model(task, mode), ReferenceGeometry(task, mode)
            state = model.initial()
            for cell in (1, 2, 3, 4):
                state = model.advance(state, cell)
            self.assert_geometry(model, reference, state)
            self.assertEqual(list(model.tree(state, 0).items()), [(0, None), (3, 0), (4, 3), (1, 4)])
            distance, parent = model.routes(state, 0)
            self.assertEqual(list(distance.items()), [(0, 0), (3, 0), (4, 0), (1, 0), (5, 1), (2, 1)])
            self.assertEqual((parent[5], parent[2]), (4, 5))

    def test_matching_relay_uses_alternative_road_route(self) -> None:
        """Keep wrong-type storage out of the tree while finding a legal road bypass."""
        task = level(
            stone=100,
            width=4,
            height=2,
            nodes=[{"x": 2, "y": 0, "resource": "STONE"}, {"x": 3, "y": 1, "resource": "IRON_ORE"}],
        )
        for mode in ("matching", "unrestricted"):
            model, reference = Model(task, mode), ReferenceGeometry(task, mode)
            state = model.initial()
            for cell in (1, 2, 3, 7):
                state = model.advance(state, cell)
            self.assert_geometry(model, reference, state)
            self.assertEqual(list(model.tree(state, None)), [0, 1, 2, 3, 7])
            if mode == "matching":
                self.assertEqual(list(model.tree(state, 0)), [0, 1, 2, 3])
                self.assertEqual(list(model.tree(state, 1)), [0, 1])
                distance, parent = model.routes(state, 1)
                self.assertEqual(
                    list(distance.items()), [(0, 0), (1, 0), (4, 1), (5, 1), (6, 2), (7, 2), (3, 2)]
                )
                self.assertEqual(
                    list(parent.items()),
                    [(0, None), (1, None), (4, 0), (5, 1), (6, 5), (7, 6), (3, 7)],
                )
            else:
                self.assertEqual(list(model.tree(state, 1)), [0, 1, 2, 3, 7])


class Stage2Tests(unittest.TestCase):
    def test_final_turn_and_ore_wait(self) -> None:
        """Allow ore production on the final turn and preserve the requested wait count."""
        for turns, goal in ((1, 5), (2, 10)):
            task = level(turns=turns, goal={"IRON_ORE": goal})
            for mode in ("matching", "unrestricted"):
                for variant in VARIANTS:
                    with self.subTest(turns=turns, mode=mode, variant=variant):
                        answer = solve(task, variant, relay_mode=mode, use_probe=False)
                        self.assertEqual(answer["status"], "FEASIBLE")
                        replay = validate_plan(task, answer["plan"], relay_mode=mode)
                        self.assertEqual(replay["base_iron_ore"], goal)
                        self.assertEqual(replay["base_stone"], 0)
                        self.assertEqual(replay["turns"], turns)

    def test_ore_cannot_pay_for_construction(self) -> None:
        """Reject a mine that lacks stone even when the base holds abundant ore."""
        task = level(stone=15, ore=100, goal={"IRON_ORE": 105}, turns=1)
        for variant in VARIANTS:
            self.assertEqual(solve(task, variant)["status"], "INFEASIBLE")
        self.assertEqual(oracle(task)["status"], "INFEASIBLE")

    def test_common_wait_for_mixed_goals(self) -> None:
        """Satisfy stone and ore targets on the same legal completion turn."""
        task = level(
            stone=27,
            goal={"STONE": 10, "IRON_ORE": 10},
            turns=3,
            width=3,
            height=3,
            nodes=[{"x": 2, "y": 0, "resource": "STONE"}, {"x": 0, "y": 2, "resource": "IRON_ORE"}],
        )
        for mode in ("matching", "unrestricted"):
            for variant in VARIANTS:
                with self.subTest(mode=mode, variant=variant):
                    answer = solve(task, variant, relay_mode=mode, use_probe=False)
                    self.assertEqual(answer["status"], "FEASIBLE")
                    r = validate_plan(task, answer["plan"], relay_mode=mode)
                    self.assertGreaterEqual(r["base_stone"], 10)
                    self.assertGreaterEqual(r["base_iron_ore"], 10)

    def test_precomputed_summaries_preserve_both_bounds(self) -> None:
        """Reusable totals preserve accepting and rejecting standalone bound decisions."""
        decisions: dict[str, set[bool]] = {"resource": set(), "scalar": set()}
        for goal in (10, 11):
            for mode in ("matching", "unrestricted"):
                model = Model(level(goal={"IRON_ORE": goal}), mode)
                state = model.initial()
                states = [state]
                for cell in (1, 2, None):
                    state = model.step(state, cell)
                    states.append(state)
                for state in states:
                    summary = model.totals(state)
                    original = deepcopy(summary)
                    for name, bound in (("resource", resource_possible), ("scalar", scalar_possible)):
                        expected = bound(model, state)
                        self.assertEqual(bound(model, state, summary), expected)
                        decisions[name].add(expected)
                    self.assertEqual(summary, original)
        self.assertEqual(decisions, {"resource": {False, True}, "scalar": {False, True}})

    def test_wait_witness_passes_bounds_with_disconnected_stock(self) -> None:
        """A raw-replayed final-turn wait remains possible despite stranded quarry stock."""
        task = level(
            stone=36, ore=2, goal={"STONE": 9, "IRON_ORE": 8}, turns=2,
            width=3, height=2,
            nodes=[
                {"x": 2, "y": 0, "resource": "STONE"},
                {"x": 1, "y": 1, "resource": "IRON_ORE"},
                {"x": 0, "y": 1, "resource": "STONE"},
            ],
        )
        for mode in ("matching", "unrestricted"):
            model = Model(task, mode)
            state = model.initial()
            for cell in (3, 1, 2, 4):
                state = model.step(state, cell)
            stranded = model.node_index[3]
            self.assertEqual((state.cash, state.ore, state.stocks[stranded]), (5, 7, 5))
            self.assertEqual(model.income(state), [5, 5])
            self.assertEqual(model.completion(state), 1)
            final = model.step(state, None)
            self.assertEqual((final.cash, final.ore, final.stocks[stranded]), (10, 12, 10))
            self.assertEqual(model.completion(final), 0)
            for current in (state, final):
                total, built = model.totals(current)
                self.assertEqual(total, [current.cash + current.stocks[stranded], current.ore])
                self.assertTrue(resource_possible(model, current))
                self.assertTrue(scalar_possible(model, current))
                dp = CapitalDP(model.goals[0], model.site_counts[0], model.site_counts[1])
                required = dp.required(
                    model.turns - current.turn, built[0], built[1],
                    (max(0, model.goals[1] - total[1]) + 4) // 5,
                )
                self.assertLessEqual(required, total[0])
            replay = validate_plan(task, model.plan([3, 1, 2, 4, None]), relay_mode=mode)
            self.assertEqual((replay["base_stone"], replay["base_iron_ore"], replay["turns"]), (10, 12, 2))

    def test_pruning_switch_preserves_tiny_raw_oracle_results(self) -> None:
        """Compare exact search with independent raw reachability, with probes disabled."""
        for task, expected in ((level(), "FEASIBLE"), (level(stone=15), "INFEASIBLE")):
            for mode in ("matching", "unrestricted"):
                self.assertEqual(oracle(task, relay_mode=mode)["status"], expected)
                for variant in VARIANTS:
                    for pruning in (False, True):
                        with self.subTest(expected=expected, mode=mode, variant=variant, pruning=pruning):
                            answer = solve(
                                task, variant, relay_mode=mode, use_probe=False,
                                use_pruning=pruning,
                            )
                            self.assertEqual(answer["status"], expected)
                            if expected == "FEASIBLE":
                                validate_plan(task, answer["plan"], relay_mode=mode)

    def test_exhausted_optional_dp_is_a_weak_pass(self) -> None:
        """Exhausted work limits cannot turn a feasible exact search into a rejection."""
        for dp in (CapitalDP(0, 0, 1, max_entries=0), CapitalDP(0, 0, 1, deadline=0)):
            self.assertEqual(dp.required(1, 0, 0, 2), 0)
            self.assertEqual(dp.skipped, 1)
            self.assertFalse(dp.cache)
        task = level()
        with patch("solver.stage2.CapitalDP", new=partial(CapitalDP, max_entries=0)):
            for mode in ("matching", "unrestricted"):
                for variant in ("typed", "both"):
                    answer = solve(task, variant, relay_mode=mode, use_probe=False)
                    self.assertEqual(answer["status"], "FEASIBLE")
                    self.assertGreater(answer["dp_skipped"], 0)
                    self.assertEqual(answer["dp_entries"], 0)
                    validate_plan(task, answer["plan"], relay_mode=mode)

    def test_initial_goal_and_zero_turns(self) -> None:
        """Require a legal turn for claiming an already satisfied goal."""
        task = level(stone=5, ore=6, goal={"STONE": 5, "IRON_ORE": 6})
        self.assertEqual(solve(task)["status"], "FEASIBLE")
        task["max_turns"] = 0
        self.assertEqual(solve(task)["status"], "INFEASIBLE")

    def test_caps_are_unknown(self) -> None:
        """Report exhausted time or state budgets without claiming impossibility."""
        task = level()
        self.assertEqual(solve(task, seconds=0)["status"], "UNKNOWN")
        self.assertEqual(solve(task, max_states=1, use_probe=False)["status"], "UNKNOWN")
        self.assertEqual(oracle(task, seconds=0)["status"], "UNKNOWN")
        self.assertEqual(oracle(task, max_states=1)["status"], "UNKNOWN")

    def test_dp_against_forward_enumeration(self) -> None:
        """Compare 6,528 DP funding decisions with independent economic reachability."""
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
