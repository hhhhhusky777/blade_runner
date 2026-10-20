"""Offline two-resource extension of the Stage1 research solver.

Conditional model only; see stage2_reference. No client, credentials or network.
Shared geometry and Stage1 projection use pure package dependencies. All adjacent affordable
builds survive; probes/routes order search or supply independently replayed wins.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from math import inf, isfinite
from time import perf_counter
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from .resource_guidance import ResourceGuidance
    from .stage1 import StateView

    class StoneModel:
        """Only the geometry inherited at runtime; typed transitions are replaced.

        Stage 2 has its own inventory State, so the inherited Stage 1 transition
        signatures do not describe this subclass's existing runtime contract.
        """

        w: int
        v: int
        nodes: tuple[int, ...]
        node_index: dict[int, int]
        k: int
        base: int
        initial_cash: int
        turns: int
        neighbors: tuple[tuple[int, ...], ...]

        def __init__(self, level: dict[str, Any]) -> None:
            """Initialize the shared grid fields from a JSON level."""
            ...

        def occupied(self, state: StateView) -> int:
            """Return the bitmask of BASE, roads and extractor cells."""
            raise NotImplementedError
else:
    from .stage1 import Model as StoneModel

from .stage1 import prefix_steps, route_cells
from .capital import investment_thresholds
from .stage1_preset import search as stone_search
from .stage2_reference import RESOURCES, read_level, validate_plan

VARIANTS = ("baseline", "scalar", "typed", "both")

Cell = int | None  # A cell builds; None advances to the next turn.
Plan = list[list[dict[str, Any]]]
RouteTree = dict[int, int | None]
# Each source retains neighbor order: destination cell, bit and storage flag.
TransferEdges = tuple[tuple[tuple[int, int, bool], ...], ...]


class GuidanceMetrics(TypedDict):
    """Counters for optional root policies; none is a pruning certificate."""

    variant: str
    calls: int
    work: int
    saving_wait_promotions: int
    policies_attempted: list[str]
    successful_policy: str | None


@dataclass(frozen=True, slots=True)
class State:
    """Exact typed state: BASE stone/ore, topology and per-site disconnected stocks."""

    turn: int
    roads: int
    quarries: int  # Existing geometry helpers use this name for all extractors.
    cash: int
    ore: int
    stocks: tuple[int, ...]  # Each site holds only its own output after normalization.


class Model(StoneModel):
    """Two-resource transitions; quarry bits represent all extractor sites."""

    def __init__(self, level: dict[str, Any], relay_mode: str = "unrestricted") -> None:
        """Parse typed inventories and reuse Stage 1's fixed grid geometry."""
        parsed = read_level(level)
        if relay_mode not in ("unrestricted", "matching"):
            raise ValueError("relay_mode must be unrestricted or matching")
        # Reuse Stage1 grid/adjacency setup; that setup consumes only the scalar
        # goal and STONE storage, which the original Stage2 input may omit.
        geometry = dict(
            level, level_goal=dict(level["level_goal"], target_resources={"STONE": parsed.goal[0]})
        )
        super().__init__(geometry)
        self.initial_ore = parsed.initial[1]
        self.goals = parsed.goal
        self.resources = tuple(
            RESOURCES.index(parsed.nodes[(p % self.w, p // self.w)]) for p in self.nodes
        )
        self.costs = tuple(10 if resource == 0 else 15 for resource in self.resources)
        self.site_counts = tuple(self.resources.count(r) for r in range(2))
        self.relay_mode = relay_mode
        self._tree_key: tuple[int, int] | None = None
        self._trees: dict[int | None, RouteTree] = {}
        self._edge_views: dict[int | None, TransferEdges] = {}
        self._scalar: tuple[tuple[int, ...], ...] | None = None
        self.planned = {
            y * self.w + x
            for y, row in enumerate(parsed.grid)
            for x, tile in enumerate(row)
            if tile == "PLANNED_ROAD" and y * self.w + x not in self.node_index
        }

    def initial(self) -> State:
        """Return turn one with starting BASE inventories and no construction."""
        return State(1, 0, 0, self.initial_cash, self.initial_ore, (0,) * self.k)

    def transfer_edges(self, resource: int | None) -> TransferEdges:
        """Prepare fixed edge permissions once per resource view, preserving order.

        Resource cells and BASE are storage; every other occupied cell is a ROAD.
        Thus storage-to-storage edges are always unusable. Occupancy and unbuilt
        extractor checks remain dynamic in the traversals. Lazy preparation also
        leaves the stone-only projection free of unused geometry allocations.
        """
        resource = None if self.relay_mode == "unrestricted" else resource
        if resource not in self._edge_views:
            storages = set(self.node_index) | {self.base}
            bits = tuple(1 << p for p in range(self.v))
            self._edge_views[resource] = tuple(
                tuple(
                    (q, bits[q], q in storages)
                    for q in neighbors
                    if not (p in storages and q in storages)
                    and not (
                        resource is not None
                        and self.relay_mode == "matching"
                        and q in self.node_index
                        and self.resources[self.node_index[q]] != resource
                    )
                )
                for p, neighbors in enumerate(self.neighbors)
            )
        return self._edge_views[resource]

    def tree(self, state: State, resource: int | None = None) -> RouteTree:
        """Cache the BASE-connected transfer tree for this topology and resource."""
        key = state.roads, state.quarries
        if key != self._tree_key:
            self._tree_key, self._trees = key, {}
        # All resources have the same graph only under unrestricted Storage.
        resource = None if self.relay_mode == "unrestricted" else resource
        if resource not in self._trees:
            occupied = self.occupied(state)
            parent: RouteTree = {self.base: None}
            queue = deque([self.base])
            edges = self.transfer_edges(resource)
            while queue:
                p = queue.popleft()
                for q, bit, _ in edges[p]:
                    if q in parent or not occupied & bit:
                        continue
                    parent[q] = p
                    queue.append(q)
            self._trees[resource] = parent
        return self._trees[resource]

    def settle(self, state: State) -> State:
        """Move reachable native site stocks to BASE without spending a turn."""
        if not any(state.stocks):
            return state
        base = [state.cash, state.ore]
        stocks = list(state.stocks)
        for i, p in enumerate(self.nodes):
            resource = self.resources[i]
            if stocks[i] and p in self.tree(state, resource):
                base[resource] += stocks[i]
                stocks[i] = 0
        # The normalized inventory always has exactly STONE and ORE entries.
        return State(state.turn, state.roads, state.quarries, *base, tuple(stocks))  # type: ignore[call-arg, arg-type]

    def advance(self, state: State, cell: Cell) -> State:
        """Raw legal build/END before free collection; also used by plan output."""
        stocks = list(state.stocks)
        if cell is None:
            for i, p in enumerate(self.nodes):
                if state.quarries >> p & 1:
                    stocks[i] += 5
            return State(
                state.turn + 1, state.roads, state.quarries, state.cash, state.ore, tuple(stocks)
            )
        if cell in self.node_index:
            i = self.node_index[cell]
            stocks[i] = 5
            return State(
                state.turn,
                state.roads,
                state.quarries | (1 << cell),
                state.cash - self.costs[i],
                state.ore,
                tuple(stocks),
            )
        return State(
            state.turn,
            state.roads | (1 << cell),
            state.quarries,
            state.cash - 1,
            state.ore,
            state.stocks,
        )

    def step(self, state: State, cell: Cell) -> State:
        """Apply one build or turn advance, mine eagerly, then settle typed stocks."""
        return self.settle(self.advance(state, cell))

    def won(self, state: State) -> bool:
        """Check both resource goals against the inventories already at BASE."""
        return state.cash >= self.goals[0] and state.ore >= self.goals[1]

    def totals(self, state: State) -> tuple[list[int], list[int]]:
        """Return all held stock and built extractor counts, indexed by resource."""
        total = [state.cash, state.ore]
        counts = [0, 0]
        for i, p in enumerate(self.nodes):
            total[self.resources[i]] += state.stocks[i]
            counts[self.resources[i]] += bool(state.quarries >> p & 1)
        return total, counts

    def income(self, state: State) -> list[int]:
        """Return the STONE and ORE reaching BASE after one more END action."""
        income = [0, 0]
        for i, p in enumerate(self.nodes):
            r = self.resources[i]
            if state.quarries >> p & 1 and p in self.tree(state, r):
                income[r] += 5
        return income

    def completion(self, state: State) -> int | None:
        """Count waits for existing connected production, or return no completion."""
        waits = 0
        for current, goal, rate in zip((state.cash, state.ore), self.goals, self.income(state)):
            if current < goal:
                if not rate:
                    return None
                waits = max(waits, (goal - current + rate - 1) // rate)
        return waits if waits <= self.turns - state.turn else None

    def choices(self, state: State) -> list[Cell]:
        """Enumerate affordable adjacent builds and productive legal turn advances."""
        occupied = self.occupied(state)
        cells: set[int] | list[Cell]
        cells = set()
        bits = occupied
        while bits:
            bit = bits & -bits
            p = bit.bit_length() - 1
            bits -= bit
            cells.update(q for q in self.neighbors[p] if not occupied >> q & 1)
        cells = [
            p
            for p in cells
            if state.cash >= (self.costs[self.node_index[p]] if p in self.node_index else 1)
        ]
        cells.sort()
        # An empty production turn before the first extractor only loses time.
        if state.turn < self.turns and state.quarries:
            cells.append(None)
        return cells

    def routes(self, state: State, resource: int) -> tuple[dict[int, int], RouteTree]:
        """Run the same uncapped 0-1 BFS with precomputed fixed edge permissions."""
        occupied = self.occupied(state)
        roots = self.tree(state, resource)
        distance = {p: 0 for p in roots}
        parent: RouteTree = {p: None for p in roots}
        unseen = self.v + 20
        queue = deque(roots)
        done: set[int] = set()
        edges = self.transfer_edges(resource)
        while queue:
            p = queue.popleft()
            if p in done:
                continue
            done.add(p)
            if p in self.node_index and not state.quarries >> p & 1:
                continue
            for q, bit, storage in edges[p]:
                cost = 0 if occupied & bit or storage else 1
                nd = distance[p] + cost
                if nd < distance.get(q, unseen):
                    distance[q], parent[q] = nd, p
                    if cost:
                        queue.append(q)
                    else:
                        queue.appendleft(q)
        return distance, parent

    def ordered(
        self, state: State, choices: Iterable[Cell], policy: str = "balanced"
    ) -> list[Cell]:
        # Hints use the same resource permissions as settlement/replay. They
        # still order only: every affordable exact-search build survives.
        """Rank surviving legal choices; never remove an alternative."""
        paths = {r: self.routes(state, r) for r in range(2)}
        routes = []
        for i, p in enumerate(self.nodes):
            distance, parent = paths[self.resources[i]]
            built = bool(state.quarries >> p & 1)
            if p not in distance or (built and not state.stocks[i]):
                continue
            cost = distance[p] + (0 if built else self.costs[i])
            if cost > state.cash:
                continue
            r = self.resources[i]
            missing = (state.cash, state.ore)[r] < self.goals[r]
            # Stone is investment capital even when it is not a goal.
            kind_rank = (
                (0 if r == 0 else 1)
                if policy == "capital"
                else (0 if missing else 1 if r == 0 else 2)
            )
            routes.append((not built, kind_rank, cost, p))
        hint = None
        if routes:
            target = min(routes)[-1]
            parent = paths[self.resources[self.node_index[target]]][1]
            path = route_cells(parent, target)
            hint = next((p for p in path if not self.occupied(state) >> p & 1), None)

        def score(p: Cell) -> tuple[int, int, Cell]:
            """Rank each legal choice by the selected hint, then stable cell order."""
            if policy == "planned" and p in self.planned:
                return (-1, 0, p)
            if p == hint and p is not None:
                return (0, 0, p)
            if p in self.node_index:
                r = self.resources[self.node_index[p]]
                return (
                    1,
                    0
                    if (policy == "capital" and r == 0)
                    or (state.cash, state.ore)[r] < self.goals[r]
                    else 1,
                    p,
                )
            return (2, 0, -1) if p is None else (3, 0, p)

        return sorted(choices, key=score)

    def plan(self, steps: Iterable[Cell]) -> Plan:
        """Expand normalized decisions into strictly replayable raw actions."""
        state = self.initial()
        turns: Plan = [[]]

        def action(name: str, **args: Any) -> dict[str, Any]:
            """Build one raw JSON action with its command-specific arguments."""
            return {"action": name, "args": args}

        def coord(p: int) -> list[int]:
            """Convert a flattened cell index to the server's x/y coordinate pair."""
            return [p % self.w, p // self.w]

        for cell in steps:
            raw = self.advance(state, cell)
            if cell is None:
                turns.append([])
                mined = [p for p in self.nodes if state.quarries >> p & 1]
            else:
                node = cell in self.node_index
                kind = (
                    ("STONE_QUARRY" if self.resources[self.node_index[cell]] == 0 else "IRON_MINE")
                    if node
                    else "ROAD"
                )
                turns[-1].append(action("BUILD", type=kind, x=cell % self.w, y=cell // self.w))
                mined = [cell] if node else []
            for p in mined:
                turns[-1].append(action("MINE", x=p % self.w, y=p // self.w))
            for i, source in enumerate(self.nodes):
                resource, amount = self.resources[i], raw.stocks[i]
                tree = self.tree(raw, resource)
                if not amount or source not in tree:
                    continue
                current = source
                while current != self.base:
                    path = [current]
                    # A non-BASE cell in the transfer tree has an integer parent.
                    p = tree[current]  # type: ignore[assignment]
                    while p != self.base and p not in self.node_index:
                        path.append(p)
                        # Only BASE has a None parent; this loop stops at BASE.
                        p = tree[p]  # type: ignore[assignment]
                    path.append(p)
                    turns[-1].append(
                        action(
                            "TRANSFER",
                            path=[coord(x) for x in path],
                            resource=RESOURCES[resource],
                            amount=amount,
                        )
                    )
                    current = p
            state = self.settle(raw)
        turns[-1].append(action("CLAIM_WIN", x=self.base % self.w, y=self.base // self.w))
        return turns


def resource_possible(
    model: Model, state: State, summary: tuple[list[int], list[int]] | None = None
) -> bool:
    """Apply the production bound, optionally reusing this call's stock summary."""
    total, built = model.totals(state) if summary is None else summary
    remaining = model.turns - state.turn
    unbuilt = [k - q for k, q in zip(model.site_counts, built)]
    stone = total[0] + 5 * built[0] * remaining + unbuilt[0] * max(0, 5 * (remaining + 1) - 10)
    ore = total[1] + 5 * built[1] * remaining + 5 * unbuilt[1] * (remaining + 1)
    missing = max(0, model.goals[1] - total[1] - 5 * built[1] * remaining)
    mines = (missing + 5 * (remaining + 1) - 1) // (5 * (remaining + 1))
    return ore >= model.goals[1] and mines <= unbuilt[1] and stone - 15 * mines >= model.goals[0]


class CapitalDP:
    """Lazy, per-solve minimum STONE for the free-road typed investment game.

    Cache key: remaining ENDs, built quarry/mine counts, missing ore in units5.
    Every dependency decreases time or increases a bounded built count.
    Budget exhaustion skips this optional filter; it never proves failure.
    """

    def __init__(
        self,
        stone_goal: int,
        stone_sites: int,
        ore_sites: int,
        deadline: float = inf,
        max_entries: int = 100000,
    ) -> None:
        """Allocate one solve's relaxed funding cache and safe work limits."""
        self.goal, self.ks, self.ko = stone_goal, stone_sites, ore_sites
        self.deadline, self.max_entries = deadline, max_entries
        self.cache: dict[tuple[int, int, int, int], float] = {}
        self.skipped = 0

    def required(self, d: int, qs: int, qo: int, missing: int) -> float:
        """Return minimum relaxed STONE; missing ORE is measured in five-unit lots.

        END earns five stone per quarry; a quarry costs ten and immediately
        returns five; a mine costs fifteen and removes one missing ore lot.
        Infinity certifies relaxed impossibility. A work limit returns zero,
        weakening the filter so an unfinished DP cannot reject a real solution.
        """
        key = d, qs, qo, missing
        if key in self.cache:
            return self.cache[key]
        if d > 128 or len(self.cache) >= self.max_entries or perf_counter() >= self.deadline:
            self.skipped += 1
            return 0  # Weak lower bound, never a failure certificate.
        if missing > qo * d + (self.ko - qo) * (d + 1):
            answer = inf
        else:
            answer = self.goal if missing == 0 else inf
            if d:
                answer = min(
                    answer, max(0, self.required(d - 1, qs, qo, max(0, missing - qo)) - 5 * qs)
                )
            if qs < self.ks:
                answer = min(answer, max(10, self.required(d, qs + 1, qo, missing) + 5))
            if qo < self.ko and missing:
                answer = min(
                    answer, max(15, self.required(d, qs, qo + 1, max(0, missing - 1)) + 15)
                )
        self.cache[key] = answer
        return answer


def scalar_possible(
    model: Model, state: State, summary: tuple[list[int], list[int]] | None = None
) -> bool:
    """Apply the pooled bound, optionally reusing this call's stock summary."""
    total, built = model.totals(state) if summary is None else summary
    goal = sum(model.goals)
    if sum(total) >= goal:
        return True
    if model._scalar is None:
        model._scalar = investment_thresholds(goal, model.k, model.turns)
    return sum(total) >= model._scalar[model.turns - state.turn][sum(built)]


def probe(
    model: Model,
    start: State,
    possible: Callable[[State], bool],
    deadline: float,
    max_work: int,
    *,
    policies: Sequence[str] | None = None,
    ordered: Callable[[State, Iterable[Cell], str], list[Cell]] | None = None,
) -> tuple[list[Cell] | None, int]:
    """Try bounded policy rollouts; return a witness or an inconclusive miss."""
    work = 0
    if policies is None:
        policies = ("planned", "balanced", "capital") if model.planned else ("balanced", "capital")
    if ordered is None:
        ordered = model.ordered
    for index, policy in enumerate(policies):
        allowance = work + max(1, (max_work - work) // (len(policies) - index))
        steps: list[Cell]
        state, steps = start, []
        for _ in range(128):
            if perf_counter() >= deadline or work >= max_work:
                return None, work
            if work >= allowance:
                break
            waits = model.completion(state)
            if waits is not None:
                return steps + [None] * waits, work
            chosen = None
            for cell in ordered(state, model.choices(state), policy):
                if perf_counter() >= deadline or work >= max_work:
                    return None, work
                if work >= allowance:
                    break
                child = model.step(state, cell)
                work += 1
                if possible(child):
                    chosen = cell, child
                    break
            if chosen is None:
                break
            cell, state = chosen
            steps.append(cell)
    return None, work


def solve(
    level: dict[str, Any],
    variant: str = "typed",
    seconds: float = 24.0,
    max_states: int | None = None,
    relay_mode: str = "unrestricted",
    use_probe: bool = True,
    use_pruning: bool = True,
    memoize: bool = True,
    guidance: str = "none",
) -> dict[str, Any]:
    """Return FEASIBLE/replayed plan, conditional INFEASIBLE, or capped UNKNOWN.

    baseline/scalar/typed/both share cheap typed bounds, exact memoization,
    one-topology cache and success-only probes. Only optional capital DP differs.
    The live/default search is time-bounded only. Explicit state caps and switches
    disabling pruning/memo/probes are offline validation controls. Optional
    guidance adds success-only root probes, leaving exact search and all default policies intact.
    """
    if variant not in VARIANTS:
        raise ValueError("unknown capital-DP variant")
    if type(seconds) not in (int, float) or not isfinite(seconds) or seconds < 0:
        raise ValueError("seconds must be finite and nonnegative")
    if max_states is not None and (type(max_states) is not int or max_states < 1):
        raise ValueError("max_states must be None or a positive integer")
    begin = perf_counter()
    deadline = begin + seconds
    if guidance not in ("none", "saving", "relaxed", "both"):
        raise ValueError("unknown guidance variant")
    model = Model(level, relay_mode)
    if (
        not any(model.resources)
        and model.initial_ore == 0
        and model.goals[1] == 0
        and use_probe
        and use_pruning
        and memoize
    ):
        # Delegate only the proven stone-only projection; the preset owns
        # per-solve cache/DP state. Replay once below against the original Stage 2
        # task, rather than first replaying the temporary Stage 1 projection.
        base = dict(level["structures"][0], storage={"STONE": model.initial_cash})
        stone_level = dict(
            level,
            structures=[base],
            level_goal=dict(level["level_goal"], target_resources={"STONE": model.goals[0]}),
        )
        answer = stone_search(
            stone_level,
            seconds=max(0, deadline - perf_counter()),
            max_states=inf if max_states is None else max_states,
        )
        if answer.get("plan") is not None:
            validate_plan(level, answer["plan"], relay_mode=relay_mode)
            if perf_counter() >= deadline:
                answer.update(status="UNKNOWN", reason="time_limit", plan=None)
        answer.update(engine="stage1", search_seconds=perf_counter() - begin)
        return answer
    metrics = dict(
        expanded=0,
        reached=1,
        duplicate_attempts=0,
        bound_prunes=0,
        scalar_prunes=0,
        typed_prunes=0,
        probe_work=0,
        probe_calls=0,
        probe_invalid=0,
    )
    # site_counts has one entry for each of the two supported resources.
    dp = CapitalDP(model.goals[0], *model.site_counts, deadline=deadline)  # type: ignore[misc]
    guidance_metrics: GuidanceMetrics = dict(
        variant=guidance,
        calls=0,
        work=0,
        saving_wait_promotions=0,
        policies_attempted=[],
        successful_policy=None,
    )
    resource_guide: ResourceGuidance | None = None

    def result(
        status: str, reason: str, steps: Iterable[Cell] | None = None
    ) -> dict[str, Any]:
        """Package counters and replay any witness within the original deadline."""
        plan = None
        if steps is not None:
            if perf_counter() >= deadline:
                status, reason = "UNKNOWN", "time_limit"
            else:
                plan = model.plan(steps)
                validate_plan(level, plan, relay_mode=relay_mode)
                if perf_counter() >= deadline:
                    status, reason, plan = "UNKNOWN", "time_limit", None
        return dict(
            status=status,
            reason=reason,
            plan=plan,
            engine="typed",
            **metrics,
            dp_entries=len(dp.cache),
            dp_skipped=dp.skipped,
            search_seconds=perf_counter() - begin,
            **(
                dict(
                    guidance_metrics=dict(
                        guidance_metrics,
                        # No relaxed policy means no resource-guidance counters.
                        resource=resource_guide.metrics if resource_guide is not None else {},  # type: ignore[typeddict-item]
                    )
                )
                if guidance != "none"
                else {}
            ),
        )

    def possible(state: State) -> bool:
        """Apply only optimistic impossibility filters and count their rejections."""
        if not use_pruning:
            return True
        summary = model.totals(state)
        if not resource_possible(model, state, summary):
            metrics["bound_prunes"] += 1
            return False
        if variant in ("scalar", "both") and not scalar_possible(model, state, summary):
            metrics["scalar_prunes"] += 1
            return False
        if variant in ("typed", "both"):
            total, built = summary
            missing = (max(0, model.goals[1] - total[1]) + 4) // 5
            # totals() returns exactly the STONE and ORE producer counts.
            required = dp.required(model.turns - state.turn, *built, missing)  # type: ignore[call-arg]
            if total[0] < required:
                metrics["typed_prunes"] += 1
                return False
        return True

    if not model.turns:
        return result("INFEASIBLE", "no_claim_turn")
    initial = model.initial()
    if perf_counter() >= deadline:
        return result("UNKNOWN", "time_limit")
    if not possible(initial):
        return result("INFEASIBLE", "initial_bound")
    parents: dict[State, tuple[State, Cell] | None] = {initial: None}
    stack: list[tuple[State, Iterator[Cell] | None]] = [(initial, None)]
    # Parent links are path records when memoization is disabled: structurally
    # equal states then share a witness, which is still legal from that state.
    while stack:
        if perf_counter() >= deadline:
            return result("UNKNOWN", "time_limit")
        state, iterator = stack[-1]
        if iterator is not None:
            try:
                cell = next(iterator)
            except StopIteration:
                stack.pop()
                continue
            child = model.step(state, cell)
            if memoize and child in parents:
                metrics["duplicate_attempts"] += 1
                continue
            if max_states is not None and metrics["reached"] >= max_states:
                return result("UNKNOWN", "state_limit")
            metrics["reached"] += 1
            parents.setdefault(child, (state, cell))
            stack.append((child, None))
            continue
        metrics["expanded"] += 1
        if not model.won(state) and not possible(state):
            stack.pop()
            continue
        waits = model.completion(state)
        if waits is not None:
            return result(
                "FEASIBLE",
                "wait_completion" if waits else "goal",
                prefix_steps(parents, state) + [None] * waits,
            )
        if (
            use_probe
            and metrics["probe_calls"] < 4
            and metrics["probe_work"] < 512
            and (metrics["expanded"] == 1 or metrics["expanded"] % 64 == 0)
        ):
            suffix, work = probe(model, state, possible, deadline, 512 - metrics["probe_work"])
            metrics["probe_calls"] += 1
            metrics["probe_work"] += work
            if suffix is not None:
                try:
                    return result("FEASIBLE", "greedy_probe", prefix_steps(parents, state) + suffix)
                except ValueError:
                    # A heuristic witness is never authority to skip full search.
                    metrics["probe_invalid"] += 1
        if use_probe and guidance != "none" and metrics["expanded"] == 1:
            # Add independent strategies after the original root probes miss.
            # Each bounded rollout may find a witness; misses never remove states.
            policies = ("relaxed", "saving") if guidance == "both" else (guidance,)
            for policy in policies:
                if perf_counter() >= deadline:
                    return result("UNKNOWN", "time_limit")
                if policy == "relaxed":
                    from .resource_guidance import ResourceGuidance

                    resource_guide = ResourceGuidance(model, dp, deadline)

                def guidance_order(
                    current: State, legal: Iterable[Cell], selected_policy: str
                ) -> list[Cell]:
                    """Promote relaxed projects or productive saving without deleting choices."""
                    if selected_policy == "relaxed":
                        fallback = model.ordered(current, legal, "balanced")
                        # The relaxed branch constructs this guide immediately above.
                        return resource_guide.ordered(current, fallback)  # type: ignore[union-attr]
                    ordered = model.ordered(current, legal, "capital")
                    if None in legal and model.income(current)[0]:
                        distances, _ = model.routes(current, 0)
                        costs = [
                            distances[p] + 10
                            for i, p in enumerate(model.nodes)
                            if model.resources[i] == 0
                            and not current.quarries >> p & 1
                            and p in distances
                        ]
                        if costs and min(costs) > current.cash:
                            guidance_metrics["saving_wait_promotions"] += 1
                            return [None] + [p for p in ordered if p is not None]
                    return ordered

                guidance_metrics["calls"] += 1
                guidance_metrics["policies_attempted"].append(policy)
                suffix, work = probe(
                    model,
                    state,
                    possible,
                    deadline,
                    512,
                    policies=(policy,),
                    ordered=guidance_order,
                )
                guidance_metrics["work"] += work
                if suffix is not None:
                    try:
                        answer = result(
                            "FEASIBLE", "guidance_probe", prefix_steps(parents, state) + suffix
                        )
                        if answer["status"] == "FEASIBLE":
                            guidance_metrics["successful_policy"] = policy
                            answer["guidance_metrics"]["successful_policy"] = policy
                        return answer
                    except ValueError:
                        metrics["probe_invalid"] += 1
        choices = model.ordered(state, model.choices(state))
        stack[-1] = state, iter(choices)
    return result("INFEASIBLE", "exhausted")
