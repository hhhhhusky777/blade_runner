"""Independent typed Stage 2 replay and tiny raw-action feasibility oracle.

Conditional offline model: cardinal adjacency, one initial BASE, no other
structures, renewable five-unit extractors, free ordered transfers through ROAD
interiors and STONE-only construction payment. ``unrestricted`` permits every
Storage to relay either resource; ``matching`` restricts extractor inventories
to their own output. These are explicit alternative premises, not server proof.
The candidate Stage 2 solver is never imported. Geometry, integer checks and the
copyable state container come from the independent Stage 1 reference.

The oracle enumerates all adjacent builds, mining flags, every integer partial
transfer and END. One road-only route per ordered storage pair suffices because
routes have identical inventory effects. Total inventory is bounded by initial
inventory + 5*K*T, so the raw finite search is exhaustive without caps. Its
state/time cost is exponential; reaching either cap returns UNKNOWN.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from math import isfinite
from time import perf_counter
from typing import TypedDict, cast

from .reference import (
    Action,
    Coord,
    Grid,
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

RESOURCES = ("STONE", "IRON_ORE")
RESOURCE = RESOURCES
EXTRACTORS = {"STONE": "STONE_QUARRY", "IRON_ORE": "IRON_MINE"}
PRODUCES = {kind: resource for resource, kind in EXTRACTORS.items()}
COSTS = {"ROAD": 1, "STONE_QUARRY": 10, "IRON_MINE": 15}
RELAY_MODES = ("unrestricted", "matching")
# Variable length permits Stage 3 to reuse checked vector operations with iron.
type Inventory = tuple[int, ...]


class ReplaySummary(TypedDict):
    """Final base inventories and the smallest prefix construction budget."""

    turns: int
    base_stone: int
    base_iron_ore: int
    base_inventory: dict[str, int]
    min_prefix_cash: int


@dataclass
class _Level:
    """Validated geometry and ordered resource vectors shared by typed stages."""

    width: int
    height: int
    grid: Grid
    nodes: dict[Coord, str]
    base: Coord
    initial: Inventory
    goal: Inventory
    max_turns: int

    def position(self, x: object, y: object) -> Coord:
        """Validate coordinates and require a position inside this board."""
        p = (_integer(x, "x"), _integer(y, "y"))
        if p[0] >= self.width or p[1] >= self.height:
            raise ValueError(f"coordinate out of bounds: {p}")
        return p


def _inventory(value: object, name: str) -> Inventory:
    """Parse stone and ore amounts in fixed resource order, defaulting to zero."""
    value = _mapping(value, name)
    if set(value) - set(RESOURCES):
        raise ValueError(f"{name} supports only STONE and IRON_ORE")
    return tuple(_integer(value.get(resource, 0), f"{name} {resource}") for resource in RESOURCES)


def _relay_mode(mode: str) -> str:
    """Validate the explicit storage-relay premise used by replay and search."""
    if mode not in RELAY_MODES:
        raise ValueError(f"relay_mode must be one of {RELAY_MODES}")
    return mode


def read_level(level: object) -> _Level:
    """Parse the supported input strictly; missing supported inventories are zero."""
    data = _mapping(level, "level")
    board = _mapping(data.get("board"), "board")
    width = _integer(board.get("width"), "width", 1)
    height = _integer(board.get("height"), "height", 1)
    grid = board.get("grid")
    if (
        not isinstance(grid, list)
        or len(grid) != height
        or any(not isinstance(row, list) or len(row) != width for row in grid)
    ):
        raise ValueError("grid dimensions do not match width/height")
    if any(tile not in ("GRASS", "PLANNED_ROAD") for row in grid for tile in row):
        raise ValueError("unsupported terrain in conditional Stage 2 model")
    turns = _integer(data.get("max_turns"), "max_turns")
    goal = _mapping(data.get("level_goal"), "level_goal")
    if goal.get("target_structure_type") != "BASE":
        raise ValueError("goal must require resources at BASE")
    target = _inventory(goal.get("target_resources"), "goal")
    model = _Level(width, height, cast(Grid, grid), {}, (0, 0), (0, 0), target, turns)
    nodes = board.get("resource_nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("resource_nodes must be a list")
    for node in nodes:
        node = _mapping(node, "resource node")
        p = model.position(node.get("x"), node.get("y"))
        if node.get("resource") not in RESOURCES or p in model.nodes:
            raise ValueError("resource nodes must have unique coordinates and supported resources")
        model.nodes[p] = node["resource"]
    structures = data.get("structures", [])
    if not isinstance(structures, list) or len(structures) != 1:
        raise ValueError("conditional model requires exactly one initial BASE")
    base = _mapping(structures[0], "initial structure")
    if base.get("type") != "BASE":
        raise ValueError("initial structure must be BASE")
    model.base = model.position(base.get("x"), base.get("y"))
    if model.base in model.nodes:
        raise ValueError("initial BASE cannot occupy a resource node")
    storage = base.get("storage")
    model.initial = _inventory({} if storage is None else storage, "BASE storage")
    return model


_read_level = read_level


def _initial(model: _Level) -> _State[Inventory]:
    """Create the first-turn state with both resources stored at the base."""
    # _State.copy/key are resource-agnostic: tuple inventories remain immutable.
    return _State(1, {model.base: "BASE"}, {model.base: model.initial}, set())


def _accepts(
    state: _State[Inventory], p: Coord, resource: str, relay_mode: str
) -> bool:
    """Check whether a storage endpoint accepts a resource under the relay premise."""
    kind = state.buildings.get(p)
    return kind == "BASE" or (
        kind in PRODUCES and (relay_mode == "unrestricted" or PRODUCES[kind] == resource)
    )


def _add(inventory: Inventory, index: int, amount: int) -> Inventory:
    """Return a new resource vector with one signed inventory adjustment."""
    values = list(inventory)
    values[index] += amount
    return tuple(values)


def _won(model: _Level, state: _State[Inventory]) -> bool:
    """Check all required resources against their current base inventories."""
    return all(have >= need for have, need in zip(state.inventory[model.base], model.goal))


def _apply(
    model: _Level, state: _State[Inventory], action: object, relay_mode: str = "unrestricted"
) -> bool:
    """Apply one checked raw action; return True only for a successful claim."""
    action = _mapping(action, "action")
    args = _mapping(action.get("args"), "action args")
    name = action.get("action")
    if name == "TRANSFER":
        path = args.get("path")
        if not isinstance(path, list) or len(path) < 3:
            raise ValueError("TRANSFER needs at least three coordinates")
        points = []
        for pair in path:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError("path coordinates must be [x, y] pairs")
            points.append(model.position(*pair))
        source, target = points[0], points[-1]
        if source == target or source not in state.inventory or target not in state.inventory:
            raise ValueError("TRANSFER needs distinct storage endpoints")
        if any(abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1 for a, b in zip(points, points[1:])):
            raise ValueError("TRANSFER path must be cardinally adjacent")
        if any(state.buildings.get(p) != "ROAD" for p in points[1:-1]):
            raise ValueError("TRANSFER interiors must be ROAD only")
        resource = args.get("resource")
        if resource not in RESOURCES:
            raise ValueError("TRANSFER resource must be STONE or IRON_ORE")
        if not _accepts(state, source, resource, relay_mode) or not _accepts(
            state, target, resource, relay_mode
        ):
            raise ValueError("TRANSFER endpoint rejects this resource in matching relay mode")
        index = RESOURCES.index(resource)
        amount = _integer(args.get("amount"), "TRANSFER amount", 1)
        if amount > state.inventory[source][index]:
            raise ValueError("TRANSFER exceeds source inventory")
        state.inventory[source] = _add(state.inventory[source], index, -amount)
        state.inventory[target] = _add(state.inventory[target], index, amount)
        return False
    if name not in ("BUILD", "MINE", "CLAIM_WIN"):
        raise ValueError(f"unsupported action: {name!r}")
    p = model.position(args.get("x"), args.get("y"))
    if name == "BUILD":
        kind = args.get("type")
        if not isinstance(kind, str) or kind not in COSTS:
            raise ValueError("BUILD type must be ROAD, STONE_QUARRY or IRON_MINE")
        if p in state.buildings:
            raise ValueError("BUILD coordinate is occupied")
        if not any(q in state.buildings for q in _neighbors(p)):
            raise ValueError("BUILD must adjoin a built structure")
        resource = model.nodes.get(p)
        if (resource is None and kind != "ROAD") or (
            resource is not None and kind != EXTRACTORS[resource]
        ):
            raise ValueError("BUILD type must match resource node, or ROAD on ordinary terrain")
        cost = COSTS[kind]
        if state.inventory[model.base][0] < cost:
            raise ValueError("BUILD has insufficient prefix BASE STONE funds")
        state.inventory[model.base] = _add(state.inventory[model.base], 0, -cost)
        state.buildings[p] = kind
        if kind in PRODUCES:
            state.inventory[p] = (0, 0)
    elif name == "MINE":
        kind = state.buildings.get(p)
        if kind not in PRODUCES or p in state.mined:
            raise ValueError("MINE requires an extractor not mined this turn")
        state.inventory[p] = _add(state.inventory[p], RESOURCES.index(PRODUCES[kind]), 5)
        state.mined.add(p)
    else:
        if p != model.base or not _won(model, state):
            raise ValueError("CLAIM_WIN requires every BASE goal inventory")
        return True
    return False


def validate_plan(
    level: object, plan: object, relay_mode: str = "unrestricted"
) -> ReplaySummary:
    """Replay original input with explicit successful CLAIM_WIN, or raise ValueError."""
    _relay_mode(relay_mode)
    model = read_level(level)
    if not isinstance(plan, list) or len(plan) > model.max_turns:
        raise ValueError("plan must be a list within max_turns")
    state = _initial(model)
    minimum, claimed = model.initial[0], False
    for turn_index, actions in enumerate(plan, 1):
        if not isinstance(actions, list):
            raise ValueError("each turn must be a list of actions")
        state.turn = turn_index
        state.mined.clear()
        for action_index, action in enumerate(actions):
            if claimed:
                raise ValueError("actions after CLAIM_WIN are illegal")
            try:
                claimed = _apply(model, state, action, relay_mode)
            except ValueError as error:
                raise ValueError(f"turn {turn_index}, action {action_index}: {error}") from error
            minimum = min(minimum, state.inventory[model.base][0])
    if not claimed:
        raise ValueError("plan has no successful CLAIM_WIN")
    stone, ore = state.inventory[model.base]
    return {
        "turns": len(plan),
        "base_stone": stone,
        "base_iron_ore": ore,
        "base_inventory": dict(zip(RESOURCES, (stone, ore))),
        "min_prefix_cash": minimum,
    }


def _successors(
    model: _Level, state: _State[Inventory], relay_mode: str
) -> Iterator[tuple[_State[Inventory], Action | None]]:
    """Enumerate raw legal actions, every partial transfer and the end of a turn."""
    for y in range(model.height):
        for x in range(model.width):
            p = (x, y)
            if p in state.buildings or not any(q in state.buildings for q in _neighbors(p)):
                continue
            kind = EXTRACTORS[model.nodes[p]] if p in model.nodes else "ROAD"
            if state.inventory[model.base][0] >= COSTS[kind]:
                action = _action("BUILD", x=x, y=y, type=kind)
                successor = state.copy()
                _apply(model, successor, action, relay_mode)
                yield successor, action
    for p, kind in state.buildings.items():
        if kind in PRODUCES and p not in state.mined:
            action = _action("MINE", x=p[0], y=p[1])
            successor = state.copy()
            _apply(model, successor, action, relay_mode)
            yield successor, action
    for source, inventory in state.inventory.items():
        if not any(inventory):
            continue
        for target in state.inventory:
            if source == target:
                continue
            path = _road_path(state, source, target)
            if path is None:
                continue
            for index, resource in enumerate(RESOURCES):
                if not _accepts(state, source, resource, relay_mode) or not _accepts(
                    state, target, resource, relay_mode
                ):
                    continue
                for amount in range(1, inventory[index] + 1):
                    action = _action("TRANSFER", path=path, resource=resource, amount=amount)
                    successor = state.copy()
                    _apply(model, successor, action, relay_mode)
                    yield successor, action
    if state.turn < model.max_turns:
        successor = state.copy()
        successor.turn += 1
        successor.mined.clear()
        yield successor, None


def oracle(
    level: object,
    seconds: float = 2.0,
    max_states: int | None = None,
    relay_mode: str = "unrestricted",
) -> OracleResult:
    """Tiny independent raw BFS. Only exhaustion proves INFEASIBLE; caps UNKNOWN."""
    _relay_mode(relay_mode)
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not isfinite(seconds)
        or seconds < 0
    ):
        raise ValueError("seconds must be a finite nonnegative number")
    if max_states is not None:
        _integer(max_states, "max_states", 1)
    start, expanded = perf_counter(), 0
    model = read_level(level)

    def result(status: OracleStatus, plan: Plan | None = None) -> OracleResult:
        """Capture the current effort counters and optional feasibility witness."""
        answer: OracleResult = {
            "status": status, "expanded": expanded, "seconds": perf_counter() - start
        }
        if plan is not None:
            answer["plan"] = plan
        return answer

    if model.max_turns == 0:
        return result("INFEASIBLE")
    initial = _initial(model)
    parents: ParentMap[Inventory] = {initial.key(): None}
    queue = deque([initial])
    if _won(model, initial):
        return result("FEASIBLE", _winning_plan(initial.key(), parents, model.base))
    while queue:
        if perf_counter() - start >= seconds:
            return result("UNKNOWN")
        state = queue.popleft()
        key = state.key()
        expanded += 1
        for successor, action in _successors(model, state, relay_mode):
            if perf_counter() - start >= seconds:
                return result("UNKNOWN")
            successor_key = successor.key()
            if successor_key in parents:
                continue
            if _won(model, successor):
                parents[successor_key] = (key, action)
                return result("FEASIBLE", _winning_plan(successor_key, parents, model.base))
            if max_states is not None and len(parents) >= max_states:
                return result("UNKNOWN")
            parents[successor_key] = (key, action)
            queue.append(successor)
    return result("INFEASIBLE")
