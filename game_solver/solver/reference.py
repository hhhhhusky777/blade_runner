"""Independent, offline Stage 1 replay and tiny atomic-state reference search.

CONDITIONAL model, not server equivalence: cardinal adjacency; one initial
BASE and no other structures; GRASS/PLANNED_ROAD terrain; unlimited STONE
nodes yielding exactly five per quarry once per turn; free, unbounded transfers
through ROAD interiors; construction paid from BASE. No candidate solver or
starter action implementation is imported.

The oracle enumerates atomic actions, including every integer transfer amount,
without mining/transfer normalization or road pruning. With K nodes and T turns,
stone is bounded by initial stone + 5*K*T, making the state space finite.
If M states are expanded, A successors per state and C successor-copy/check
cost, time is O(M*A*C), plus road BFS work; reached states and parent links use
O(M*sigma) space for state size sigma. These bounds can be enormous; limits
return UNKNOWN, and INFEASIBLE means this conditional finite model exhausted.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from math import isfinite
from time import perf_counter
from typing import Any, Literal, NotRequired, TypedDict, cast

type Coord = tuple[int, int]
type Grid = list[list[str]]
type Action = dict[str, Any]
type Plan = list[list[Action]]
type OracleStatus = Literal["FEASIBLE", "INFEASIBLE", "UNKNOWN"]
type StateKey[StockT] = tuple[
    int, tuple[tuple[Coord, str], ...], tuple[tuple[Coord, StockT], ...], tuple[Coord, ...]
]
type ParentLink[StockT] = tuple[StateKey[StockT], Action | None]
type ParentMap[StockT] = dict[StateKey[StockT], ParentLink[StockT] | None]


class OracleResult(TypedDict):
    """Feasibility verdict, search effort and optional checked plan witness."""

    status: OracleStatus
    expanded: int
    seconds: float
    plan: NotRequired[Plan | None]


def _integer(value: object, name: str, minimum: int = 0) -> int:
    """Validate a bounded integer, rejecting booleans and numeric coercion."""
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _mapping(value: object, name: str) -> dict[str, Any]:
    """Require a JSON object while leaving its fields for specific validators."""
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a dictionary")
    return value


def _neighbors(p: Coord) -> Iterator[Coord]:
    """Yield the four cardinal neighbors without applying board bounds."""
    x, y = p
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yield x + dx, y + dy


@dataclass
class _Level:
    """Validated Stage 1 geometry, starting budget and target horizon."""

    width: int
    height: int
    grid: Grid
    nodes: set[Coord]
    base: Coord
    initial: int
    goal: int
    max_turns: int

    def position(self, x: object, y: object) -> Coord:
        """Validate coordinates and require a position inside this board."""
        p = (_integer(x, "x"), _integer(y, "y"))
        if p[0] >= self.width or p[1] >= self.height:
            raise ValueError(f"coordinate out of bounds: {p}")
        return p


@dataclass
class _State[StockT: int | tuple[int, ...]]:
    """Raw replay state with independent structures, stock and turn activations."""

    turn: int
    buildings: dict[Coord, str]
    inventory: dict[Coord, StockT]
    mined: set[Coord]

    def copy(self) -> _State[StockT]:
        """Copy mutable containers so one successor cannot alter its parent."""
        return _State(self.turn, self.buildings.copy(), self.inventory.copy(), self.mined.copy())

    def key(self) -> StateKey[StockT]:
        """Return a canonical key including per-turn activation history."""
        return (
            self.turn,
            tuple(sorted(self.buildings.items())),
            tuple(sorted(self.inventory.items())),
            tuple(sorted(self.mined)),
        )


def _read_level(level: object) -> _Level:
    """Parse and validate the conditional single-resource task model."""
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
        raise ValueError("unsupported terrain in conditional Stage 1 model")
    turns = _integer(data.get("max_turns"), "max_turns")
    goal = _mapping(data.get("level_goal"), "level_goal")
    resources = _mapping(goal.get("target_resources"), "target_resources")
    if goal.get("target_structure_type") != "BASE" or set(resources) != {"STONE"}:
        raise ValueError("goal must require only STONE at BASE")
    model = _Level(
        width,
        height,
        cast(Grid, grid),
        set(),
        (0, 0),
        0,
        _integer(resources["STONE"], "goal STONE"),
        turns,
    )
    nodes = board.get("resource_nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("resource_nodes must be a list")
    for node in nodes:
        node = _mapping(node, "resource node")
        p = model.position(node.get("x"), node.get("y"))
        if node.get("resource") != "STONE" or p in model.nodes:
            raise ValueError("resource nodes must be unique STONE coordinates")
        model.nodes.add(p)
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
    if storage is None:
        storage = {}
    storage = _mapping(storage, "BASE storage")
    if set(storage) - {"STONE"}:
        raise ValueError("conditional model supports only STONE inventory")
    model.initial = _integer(storage.get("STONE", 0), "initial STONE")
    return model


def _initial(model: _Level) -> _State[int]:
    """Create the first-turn state with all starting stone at the base."""
    return _State(1, {model.base: "BASE"}, {model.base: model.initial}, set())


def _action(name: str, **args: Any) -> Action:
    """Construct a raw JSON action for replay or an oracle witness."""
    return {"action": name, "args": args}


def _apply(model: _Level, state: _State[int], action: object) -> bool:
    """Apply one checked atomic action; return True only for a valid claim."""
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
        for first, second in zip(points, points[1:]):
            if abs(first[0] - second[0]) + abs(first[1] - second[1]) != 1:
                raise ValueError("TRANSFER path must be cardinally adjacent")
        if any(state.buildings.get(p) != "ROAD" for p in points[1:-1]):
            raise ValueError("TRANSFER interiors must be ROAD only")
        if args.get("resource") != "STONE":
            raise ValueError("TRANSFER supports only STONE")
        amount = _integer(args.get("amount"), "TRANSFER amount", 1)
        if amount > state.inventory[source]:
            raise ValueError("TRANSFER exceeds source inventory")
        state.inventory[source] -= amount
        state.inventory[target] += amount
        return False
    if name not in ("BUILD", "MINE", "CLAIM_WIN"):
        raise ValueError(f"unsupported action: {name!r}")
    p = model.position(args.get("x"), args.get("y"))
    if name == "BUILD":
        kind = args.get("type")
        if kind not in ("ROAD", "STONE_QUARRY"):
            raise ValueError("BUILD type must be ROAD or STONE_QUARRY")
        if p in state.buildings:
            raise ValueError("BUILD coordinate is occupied")
        if not any(q in state.buildings for q in _neighbors(p)):
            raise ValueError("BUILD must adjoin a built structure")
        if (kind == "STONE_QUARRY") != (p in model.nodes):
            raise ValueError("only STONE_QUARRY may occupy a STONE node")
        cost = 10 if kind == "STONE_QUARRY" else 1
        if state.inventory[model.base] < cost:
            raise ValueError("BUILD has insufficient prefix BASE funds")
        state.inventory[model.base] -= cost
        state.buildings[p] = kind
        if kind == "STONE_QUARRY":
            state.inventory[p] = 0
    elif name == "MINE":
        if state.buildings.get(p) != "STONE_QUARRY" or p in state.mined:
            raise ValueError("MINE requires an unmined quarry this turn")
        state.inventory[p] += 5
        state.mined.add(p)
    else:
        if p != model.base or state.inventory[p] < model.goal:
            raise ValueError("CLAIM_WIN requires the BASE goal inventory")
        return True
    return False


def validate_plan(level: object, plan: object) -> dict[str, int]:
    """Strict replay under the conditional model; raise ValueError if illegal.

    The summary counts supplied turns and reports final BASE stone and minimum
    BASE cash over every action prefix, including the initial inventory.
    A successful explicit CLAIM_WIN is required; subsequent actions are illegal.
    """
    model = _read_level(level)
    if not isinstance(plan, list) or len(plan) > model.max_turns:
        raise ValueError("plan must be a list within max_turns")
    state = _initial(model)
    minimum = model.initial
    claimed = False
    for turn_index, actions in enumerate(plan, 1):
        if not isinstance(actions, list):
            raise ValueError("each turn must be a list of actions")
        state.turn = turn_index
        state.mined.clear()
        for action_index, action in enumerate(actions):
            if claimed:
                raise ValueError("actions after CLAIM_WIN are illegal")
            try:
                claimed = _apply(model, state, action)
            except ValueError as error:
                raise ValueError(f"turn {turn_index}, action {action_index}: {error}") from error
            minimum = min(minimum, state.inventory[model.base])
    if not claimed:
        raise ValueError("plan has no successful CLAIM_WIN")
    return {
        "turns": len(plan),
        "base_stone": state.inventory[model.base],
        "min_prefix_cash": minimum,
    }


def _road_path[StockT: int | tuple[int, ...]](
    state: _State[StockT], source: Coord, target: Coord
) -> list[list[int]] | None:
    """One simple valid route, ignoring a direct endpoint edge (length < 3)."""
    queue = deque([source])
    previous: dict[Coord, Coord | None] = {source: None}
    while queue:
        current = queue.popleft()
        for neighbor in _neighbors(current):
            if neighbor == target and current != source:
                path = [target]
                cursor: Coord | None = current
                while cursor is not None:
                    path.append(cursor)
                    cursor = previous[cursor]
                return [list(p) for p in reversed(path)]
            if state.buildings.get(neighbor) == "ROAD" and neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)
    return None


def _successors(
    model: _Level, state: _State[int]
) -> Iterator[tuple[_State[int], Action | None]]:
    """Enumerate every legal build, mine, partial transfer and turn advance."""
    # All board cells are considered: even roads of no apparent use are legal.
    for y in range(model.height):
        for x in range(model.width):
            p = (x, y)
            if p in state.buildings or not any(q in state.buildings for q in _neighbors(p)):
                continue
            kind = "STONE_QUARRY" if p in model.nodes else "ROAD"
            cost = 10 if kind == "STONE_QUARRY" else 1
            if state.inventory[model.base] >= cost:
                action = _action("BUILD", x=x, y=y, type=kind)
                successor = state.copy()
                _apply(model, successor, action)
                yield successor, action
    for p, kind in state.buildings.items():
        if kind == "STONE_QUARRY" and p not in state.mined:
            action = _action("MINE", x=p[0], y=p[1])
            successor = state.copy()
            _apply(model, successor, action)
            yield successor, action
    for source, inventory in state.inventory.items():
        if not inventory:
            continue
        for target in state.inventory:
            if source == target:
                continue
            path = _road_path(state, source, target)
            if path is None:
                continue
            # Every positive amount: no flush-to-BASE or other normalization.
            for amount in range(1, inventory + 1):
                action = _action("TRANSFER", path=path, resource="STONE", amount=amount)
                successor = state.copy()
                _apply(model, successor, action)
                yield successor, action
    if state.turn < model.max_turns:
        successor = state.copy()
        successor.turn += 1
        successor.mined.clear()
        yield successor, None  # Explicit end-turn transition, including empty turns.


def _winning_plan[StockT](
    key: StateKey[StockT], parents: ParentMap[StockT], base: Coord
) -> Plan:
    """Reconstruct atomic actions and turn boundaries, then append the claim."""
    actions: list[Action | None] = []
    while parents[key] is not None:
        key, action = cast(ParentLink[StockT], parents[key])
        actions.append(action)
    plan: Plan = [[]]
    for action in reversed(actions):
        if action is None:
            plan.append([])
        else:
            plan[-1].append(action)
    plan[-1].append(_action("CLAIM_WIN", x=base[0], y=base[1]))
    return plan


def oracle(level: object, seconds: float = 2.0, max_states: int = 50000) -> OracleResult:
    """Breadth-first atomic feasibility oracle for tiny offline fixtures only.

    max_states caps all discovered states, including the initial state. Time and
    state caps yield UNKNOWN. Only queue exhaustion yields INFEASIBLE; a plan
    reaching the BASE goal yields FEASIBLE with an explicit CLAIM_WIN witness.
    """
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not isfinite(seconds)
        or seconds < 0
    ):
        raise ValueError("seconds must be a finite nonnegative number")
    _integer(max_states, "max_states", 1)
    start = perf_counter()
    model = _read_level(level)
    expanded = 0

    def result(status: OracleStatus, plan: Plan | None = None) -> OracleResult:
        """Capture the current effort counters and optional feasibility witness."""
        answer: OracleResult = {
            "status": status, "expanded": expanded, "seconds": perf_counter() - start
        }
        if plan is not None:
            answer["plan"] = plan
        return answer

    if model.max_turns == 0:
        return result("INFEASIBLE")  # No turn is available for the required claim.
    initial = _initial(model)
    parents: ParentMap[int] = {initial.key(): None}
    queue = deque([initial])
    if initial.inventory[model.base] >= model.goal:
        return result("FEASIBLE", _winning_plan(initial.key(), parents, model.base))
    while queue:
        if perf_counter() - start >= seconds:
            return result("UNKNOWN")
        state = queue.popleft()
        key = state.key()
        expanded += 1
        for successor, action in _successors(model, state):
            if perf_counter() - start >= seconds:
                return result("UNKNOWN")
            successor_key = successor.key()
            if successor_key in parents:
                continue
            if successor.inventory[model.base] >= model.goal:
                parents[successor_key] = (key, action)
                return result("FEASIBLE", _winning_plan(successor_key, parents, model.base))
            if len(parents) >= max_states:
                return result("UNKNOWN")
            parents[successor_key] = (key, action)
            queue.append(successor)
    return result("INFEASIBLE")
