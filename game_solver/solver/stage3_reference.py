"""Independent raw-action Stage3 replay/oracle; conditional cardinal/five model.

No candidate import. Storage matching allows quarry STONE, mine ORE, smelter
ORE/IRON; unrestricted permits all. A shared activation set is safe because a
structure is either Extraction or Production, never both. Raw oracle retains
all integer transfer amounts and explicit optional mining/production.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from copy import deepcopy
from math import isfinite
from time import perf_counter
from typing import TypedDict

from . import stage2_reference as old
from .reference import (
    Action,
    OracleResult,
    OracleStatus,
    ParentMap,
    Plan,
    _State,
    _integer,
    _mapping,
    _neighbors,
    _road_path,
    _action,
    _winning_plan,
)
from .stage2_reference import Inventory

RESOURCES = ("STONE", "IRON_ORE", "IRON")
COSTS = dict(old.COSTS, SMELTER=20)


class ReplaySummary(TypedDict):
    """Final base resource vector and the smallest prefix construction budget."""

    turns: int
    base_inventory: dict[str, int]
    min_prefix_cash: int


def inventory(value: object, name: str) -> Inventory:
    """Parse stone, ore and iron amounts in fixed order, defaulting to zero."""
    value = _mapping(value, name)
    if set(value) - set(RESOURCES):
        raise ValueError(f"{name}: unsupported resource")
    return tuple(_integer(value.get(r, 0), f"{name} {r}") for r in RESOURCES)


def read_level(level: object) -> old._Level:
    """Validate geometry through Stage 2, then restore the full resource vectors."""
    data = deepcopy(_mapping(level, "level"))
    structures = data.get("structures")
    if not isinstance(structures, list) or len(structures) != 1:
        raise ValueError("conditional model requires exactly one initial BASE")
    base = _mapping(structures[0], "initial structure")
    storage = base.get("storage")
    initial = inventory({} if storage is None else storage, "initial")
    goal_data = _mapping(data.get("level_goal"), "level_goal")
    goal = inventory(goal_data.get("target_resources"), "goal")
    base["storage"] = dict(zip(RESOURCES[:2], initial[:2]))
    goal_data["target_resources"] = dict(zip(RESOURCES[:2], goal[:2]))
    model = old.read_level(data)
    model.initial, model.goal = initial, goal
    return model


def accepts(kind: str, resource: str, mode: str) -> bool:
    """Check resource acceptance for a base, extractor or smelter endpoint."""
    return kind == "BASE" or (
        kind in ("STONE_QUARRY", "IRON_MINE", "SMELTER")
        and (
            mode == "unrestricted"
            or resource
            in {
                "STONE_QUARRY": ("STONE",),
                "IRON_MINE": ("IRON_ORE",),
                "SMELTER": ("IRON_ORE", "IRON"),
            }[kind]
        )
    )


def initial(model: old._Level) -> _State[Inventory]:
    """Create the first-turn state with all three resources at the base."""
    return _State(1, {model.base: "BASE"}, {model.base: model.initial}, set())


def won(model: old._Level, state: _State[Inventory]) -> bool:
    """Check that the base meets every resource requirement simultaneously."""
    return all(h >= g for h, g in zip(state.inventory[model.base], model.goal))


def apply(
    model: old._Level, state: _State[Inventory], action: object, relay_mode: str = "matching"
) -> bool:
    """Apply one checked action, including smelter activation and ore consumption."""
    old._relay_mode(relay_mode)
    action = _mapping(action, "action")
    args = _mapping(action.get("args"), "args")
    name = action.get("action")
    if name == "TRANSFER":
        raw = args.get("path")
        if not isinstance(raw, list) or len(raw) < 3:
            raise ValueError("TRANSFER needs at least three coordinates")
        points = []
        for pair in raw:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError("path requires coordinate pairs")
            points.append(model.position(*pair))
        source, target = points[0], points[-1]
        if source == target or source not in state.inventory or target not in state.inventory:
            raise ValueError("TRANSFER needs distinct storage endpoints")
        if any(abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1 for a, b in zip(points, points[1:])):
            raise ValueError("TRANSFER must be cardinal")
        if any(state.buildings.get(p) != "ROAD" for p in points[1:-1]):
            raise ValueError("TRANSFER interiors must be ROAD only")
        resource = args.get("resource")
        if resource not in RESOURCES or not all(
            accepts(state.buildings[p], resource, relay_mode) for p in (source, target)
        ):
            raise ValueError("TRANSFER resource/endpoint unsupported")
        r = RESOURCES.index(resource)
        amount = _integer(args.get("amount"), "amount", 1)
        if amount > state.inventory[source][r]:
            raise ValueError("TRANSFER exceeds inventory")
        state.inventory[source] = old._add(state.inventory[source], r, -amount)
        state.inventory[target] = old._add(state.inventory[target], r, amount)
        return False
    if name == "PRODUCE":
        p = model.position(args.get("x"), args.get("y"))
        if state.buildings.get(p) != "SMELTER" or p in state.mined:
            raise ValueError("PRODUCE needs unactivated SMELTER")
        cycles = min(2, state.inventory[p][1])
        if not cycles:
            raise ValueError("PRODUCE needs ore in the SMELTER")
        state.inventory[p] = old._add(old._add(state.inventory[p], 1, -cycles), 2, cycles)
        state.mined.add(p)
        return False
    if name == "BUILD" and args.get("type") == "SMELTER":
        p = model.position(args.get("x"), args.get("y"))
        if (
            p in state.buildings
            or p in model.nodes
            or not any(q in state.buildings for q in _neighbors(p))
        ):
            raise ValueError("SMELTER needs empty adjacent ordinary terrain")
        if state.inventory[model.base][0] < 20:
            raise ValueError("SMELTER needs20 BASE STONE")
        state.inventory[model.base] = old._add(state.inventory[model.base], 0, -20)
        state.buildings[p], state.inventory[p] = "SMELTER", (0, 0, 0)
        return False
    # Existing checked BUILD/MINE/CLAIM transitions are resource-vector agnostic
    # except initializing a new extractor inventory with two entries.
    claimed = old._apply(model, state, action, relay_mode)
    if name == "BUILD":
        p = (args["x"], args["y"])
        if p in state.inventory and len(state.inventory[p]) == 2:
            state.inventory[p] += (0,)
    return claimed


def validate_plan(
    level: object, plan: object, relay_mode: str = "matching"
) -> ReplaySummary:
    """Replay every ordered action and require a legal, explicit winning claim."""
    old._relay_mode(relay_mode)
    model = read_level(level)
    if not isinstance(plan, list) or len(plan) > model.max_turns:
        raise ValueError("plan must be a list within max_turns")
    state = initial(model)
    minimum, claimed = model.initial[0], False
    for t, actions in enumerate(plan, 1):
        if not isinstance(actions, list):
            raise ValueError("turn must be a list")
        state.turn = t
        state.mined.clear()
        for i, action in enumerate(actions):
            if claimed:
                raise ValueError("actions after CLAIM_WIN")
            try:
                claimed = apply(model, state, action, relay_mode)
            except ValueError as error:
                raise ValueError(f"turn{t} action{i}: {error}") from error
            minimum = min(minimum, state.inventory[model.base][0])
    if not claimed:
        raise ValueError("no successful CLAIM_WIN")
    return dict(
        turns=len(plan),
        base_inventory=dict(zip(RESOURCES, state.inventory[model.base])),
        min_prefix_cash=minimum,
    )


def successors(
    model: old._Level, state: _State[Inventory], relay_mode: str
) -> Iterator[tuple[_State[Inventory], Action | None]]:
    """Enumerate all legal builds, activations, partial transfers and turn advances."""
    for y in range(model.height):
        for x in range(model.width):
            p = x, y
            if p in state.buildings or not any(q in state.buildings for q in _neighbors(p)):
                continue
            kinds = (old.EXTRACTORS[model.nodes[p]],) if p in model.nodes else ("ROAD", "SMELTER")
            for kind in kinds:
                if state.inventory[model.base][0] >= COSTS[kind]:
                    a = _action("BUILD", x=x, y=y, type=kind)
                    child = state.copy()
                    apply(model, child, a, relay_mode)
                    yield child, a
    for p, kind in state.buildings.items():
        if p in state.mined:
            continue
        name = (
            "MINE"
            if kind in old.PRODUCES
            else "PRODUCE"
            if kind == "SMELTER" and state.inventory[p][1]
            else None
        )
        if name:
            a = _action(name, x=p[0], y=p[1])
            child = state.copy()
            apply(model, child, a, relay_mode)
            yield child, a
    for source, stock in state.inventory.items():
        for target in state.inventory:
            if source == target:
                continue
            path = _road_path(state, source, target)
            if path is None:
                continue
            for r, resource in enumerate(RESOURCES):
                if not all(
                    accepts(state.buildings[p], resource, relay_mode) for p in (source, target)
                ):
                    continue
                for amount in range(1, stock[r] + 1):
                    a = _action("TRANSFER", path=path, resource=resource, amount=amount)
                    child = state.copy()
                    apply(model, child, a, relay_mode)
                    yield child, a
    if state.turn < model.max_turns:
        child = state.copy()
        child.turn += 1
        child.mined.clear()
        yield child, None


def oracle(
    level: object, seconds: float = 5, relay_mode: str = "matching"
) -> OracleResult:
    """Exhaust tiny raw-action states; return UNKNOWN when the time limit expires."""
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not isfinite(seconds)
        or seconds < 0
    ):
        raise ValueError("seconds must be finite nonnegative")
    old._relay_mode(relay_mode)
    start = perf_counter()
    model = read_level(level)
    expanded = 0

    def result(status: OracleStatus, plan: Plan | None = None) -> OracleResult:
        """Capture the current effort counters and optional feasibility witness."""
        return dict(status=status, expanded=expanded, seconds=perf_counter() - start, plan=plan)

    if not model.max_turns:
        return result("INFEASIBLE")
    root = initial(model)
    parents: ParentMap[Inventory] = {root.key(): None}
    queue = deque([root])
    if won(model, root):
        return result("FEASIBLE", _winning_plan(root.key(), parents, model.base))
    while queue:
        if perf_counter() - start >= seconds:
            return result("UNKNOWN")
        state = queue.popleft()
        key = state.key()
        expanded += 1
        for child, action in successors(model, state, relay_mode):
            if perf_counter() - start >= seconds:
                return result("UNKNOWN")
            ck = child.key()
            if ck in parents:
                continue
            parents[ck] = (key, action)
            if won(model, child):
                return result("FEASIBLE", _winning_plan(ck, parents, model.base))
            queue.append(child)
    return result("INFEASIBLE")
