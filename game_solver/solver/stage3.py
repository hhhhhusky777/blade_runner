"""Offline Stage3 search: exact transfer-component quotient, optional safe bounds.

Conditional rules are owned by stage3_reference. No API/environment/network.
Earlier stages are reused through pure package imports. Probe budgets limit only optional attempts;
full search has only the wall deadline. See whiteboard for projection proofs.
"""

from collections import deque
from dataclasses import dataclass, replace
from functools import lru_cache
from math import isfinite
from time import perf_counter

from .stage2 import CapitalDP, solve as solve_stage2
from .stage3_reference import RESOURCES, COSTS, accepts, read_level, validate_plan


# Work limits apply to optional probes, never to exact-search state count.
INITIAL_PROBE_DECISIONS = 512
FOLLOWUP_PROBE_DECISIONS = 32
PROBE_INTERVAL = 512


@dataclass(frozen=True, slots=True)
class State:
    """Exact normalized key: topology, one-based turn, activation mask and stock.

    Cell sets are bitmasks. produced marks factories already used this turn.
    Each stock entry is (canonical storage cell, resource index, positive units).
    """

    turn: int
    roads: int
    extractors: int
    smelters: int
    produced: int
    stock: tuple[tuple[int, int, int], ...]


def bits(mask):
    while mask:
        bit = mask & -mask
        mask -= bit
        yield bit.bit_length() - 1


class Model:
    """Own typed connectivity, stock normalization, transitions and project ordering."""

    def __init__(self, level, relay_mode="matching", distance_reuse=False):
        if relay_mode not in ("matching", "unrestricted"):
            raise ValueError("invalid relay_mode")
        parsed = read_level(level)
        self.level, self.mode = level, relay_mode
        self.distance_reuse = distance_reuse
        self.w, self.h = parsed.width, parsed.height
        self.v, self.turns = self.w * self.h, parsed.max_turns
        self.base = parsed.base[1] * self.w + parsed.base[0]
        self.nodes = {y * self.w + x: RESOURCES.index(r) for (x, y), r in parsed.nodes.items()}
        self.goals, self.start = parsed.goal, parsed.initial
        self.site_counts = tuple(sum(r == i for r in self.nodes.values()) for i in (0, 1))
        self.neighbors = tuple(
            tuple(
                q
                for q in (
                    p - 1 if p % self.w else -1,
                    p + 1 if p % self.w < self.w - 1 else -1,
                    p - self.w,
                    p + self.w,
                )
                if 0 <= q < self.v
            )
            for p in range(self.v)
        )
        self.planned = {
            y * self.w + x
            for y, row in enumerate(parsed.grid)
            for x, t in enumerate(row)
            if t == "PLANNED_ROAD"
        }
        self.layout = lru_cache(maxsize=64)(self._layout)
        self.routes = lru_cache(maxsize=64)(self._routes)
        self.road_distances = lru_cache(maxsize=64)(self._road_distances)

    def _road_distances(self, roads):
        # This priority key is Manhattan distance, not legal transport distance.
        # Ignore terrain/storage; every grid cell is traversable for this BFS.
        if not roads:
            return (1000,) * self.v
        distance = [-1] * self.v
        queue = deque(bits(roads))
        for p in queue:
            distance[p] = 0
        while queue:
            p = queue.popleft()
            for q in self.neighbors[p]:
                if distance[q] < 0:
                    distance[q] = distance[p] + 1
                    queue.append(q)
        return tuple(distance)

    def coord(self, p):
        return [p % self.w, p // self.w]

    def action(self, name, p, **args):
        return dict(action=name, args=dict(x=p % self.w, y=p // self.w, **args))

    def occupied(self, s):
        return s.roads | s.extractors | s.smelters | (1 << self.base)

    def _layout(self, roads, extractors, smelters):
        """Build a separate transfer graph and canonical storage root for each resource."""
        kinds = {self.base: "BASE"}
        kinds.update(
            (p, "STONE_QUARRY" if self.nodes[p] == 0 else "IRON_MINE") for p in bits(extractors)
        )
        kinds.update((p, "SMELTER") for p in bits(smelters))
        roots = []
        graphs = []
        for r in range(3):
            valid = set(bits(roads)) | {
                p for p, k in kinds.items() if accepts(k, RESOURCES[r], self.mode)
            }
            graph = {
                p: tuple(
                    q
                    for q in self.neighbors[p]
                    if q in valid and ((roads >> p & 1) or (roads >> q & 1))
                )
                for p in valid
            }
            rootmap = {}
            remaining = set(graph)
            while remaining:
                seed = min(remaining)
                component = {seed}
                queue = deque([seed])
                remaining.remove(seed)
                while queue:
                    for q in graph[queue.popleft()]:
                        if q in remaining:
                            remaining.remove(q)
                            component.add(q)
                            queue.append(q)
                stores = component & kinds.keys()
                if stores:
                    root = min(
                        stores,
                        key=lambda p: (p != self.base, not (r == 1 and kinds[p] == "IRON_MINE"), p),
                    )
                    rootmap.update((p, root) for p in stores)
            roots.append(rootmap)
            graphs.append(graph)
        return kinds, tuple(roots), tuple(graphs)

    def layout_for(self, s):
        return self.layout(s.roads, s.extractors, s.smelters)

    def normalize(self, s, stock, emit=False):
        """Pool fungible component stock; optionally emit the matching legal transfers."""
        _, roots, _ = self.layout_for(s)
        pooled = {}
        actions = []
        for (p, r), amount in sorted(stock.items()):
            if not amount:
                continue
            root = roots[r][p]
            pooled[root, r] = pooled.get((root, r), 0) + amount
            if emit and p != root:
                actions.extend(self.transfer(s, p, root, r, amount))
        return replace(s, stock=tuple((p, r, n) for (p, r), n in sorted(pooled.items()))), actions

    def transfer(self, s, source, target, r, amount):
        kinds, _, graphs = self.layout_for(s)
        graph = graphs[r]
        queue = deque([source])
        parent = {source: None}
        while queue and target not in parent:
            p = queue.popleft()
            for q in graph[p]:
                if q not in parent:
                    parent[q] = p
                    queue.append(q)
        if target not in parent:
            raise ValueError("disconnected transfer")
        path = [target]
        while path[-1] != source:
            path.append(parent[path[-1]])
        path.reverse()
        segment = [path[0]]
        actions = []
        for p in path[1:]:
            segment.append(p)
            if p in kinds:
                if len(segment) < 3:
                    raise AssertionError("invalid normalized edge")
                actions.append(
                    dict(
                        action="TRANSFER",
                        args=dict(
                            path=[self.coord(q) for q in segment],
                            resource=RESOURCES[r],
                            amount=amount,
                        ),
                    )
                )
                segment = [p]
        return actions

    def initial(self):
        return State(1, 0, 0, 0, 0, tuple((self.base, r, n) for r, n in enumerate(self.start) if n))

    def totals(self, s):
        values = [0, 0, 0]
        for _, r, n in s.stock:
            values[r] += n
        return values

    def counts(self, s):
        q = sum(self.nodes[p] == 0 for p in bits(s.extractors))
        m = s.extractors.bit_count() - q
        return q, m, s.smelters.bit_count()

    def cash(self, s):
        return sum(n for p, r, n in s.stock if p == self.base and r == 0)

    def won(self, s):
        base = [0, 0, 0]
        for p, r, n in s.stock:
            if p == self.base:
                base[r] += n
        return all(h >= g for h, g in zip(base, self.goals))

    def choices(self, s):
        occupied = self.occupied(s)
        front = set()
        for p in bits(occupied):
            front.update(q for q in self.neighbors[p] if not occupied >> q & 1)
        cash = self.cash(s)
        for p in sorted(front):
            kinds = (
                (("STONE_QUARRY" if self.nodes[p] == 0 else "IRON_MINE"),)
                if p in self.nodes
                else ("ROAD", "SMELTER")
            )
            for kind in kinds:
                if cash >= COSTS[kind]:
                    yield ("BUILD", p, kind)
        _, roots, _ = self.layout_for(s)
        stock = {(p, r): n for p, r, n in s.stock}
        for p in bits(s.smelters & ~s.produced):
            root = roots[1][p]
            available = stock.get((root, 1), 0)
            for n in range(1, min(2, available) + 1):
                # Positive ore originates at BASE/mine, hence canonical ORE
                # root is not a smelter. Feed exactly n, keeping surplus there.
                if root == p:
                    raise AssertionError("unsupported singleton ore origin")
                yield ("PRODUCE", p, n)
        if s.turn < self.turns:
            yield ("END",)

    def step(self, s, choice, emit=False, admit=None):
        """Apply build, optional production or turn advance; preserve activation in the key."""
        stock = {(p, r): n for p, r, n in s.stock}
        actions = []
        if choice[0] == "BUILD":
            _, p, kind = choice
            stock[self.base, 0] = stock.get((self.base, 0), 0) - COSTS[kind]
            if emit:
                actions.append(self.action("BUILD", p, type=kind))
            if kind == "ROAD":
                raw = replace(s, roads=s.roads | 1 << p)
            elif kind == "SMELTER":
                raw = replace(s, smelters=s.smelters | 1 << p)
            else:
                raw = replace(s, extractors=s.extractors | 1 << p)
                stock[p, self.nodes[p]] = 5
                if emit:
                    actions.append(self.action("MINE", p))
        elif choice[0] == "PRODUCE":
            _, p, n = choice
            _, roots, _ = self.layout_for(s)
            root = roots[1][p]
            stock[root, 1] -= n
            stock[p, 2] = stock.get((p, 2), 0) + n
            raw = replace(s, produced=s.produced | 1 << p)
            if emit:
                actions.extend(self.transfer(s, root, p, 1, n))
                actions.append(self.action("PRODUCE", p))
        else:
            raw = replace(s, turn=s.turn + 1, produced=0)
            for p in bits(s.extractors):
                stock[p, self.nodes[p]] = stock.get((p, self.nodes[p]), 0) + 5
                if emit:
                    actions.append(self.action("MINE", p))
        # Only search uses admit; it sees complete action updates, before pooling.
        if admit is not None and not admit(raw, stock):
            return None, []
        child, moves = self.normalize(raw, stock, emit)
        return child, actions + moves

    def plan(self, steps):
        s = self.initial()
        turns = [[]]
        for choice in steps:
            if choice[0] == "END":
                turns.append([])
            s, actions = self.step(s, choice, True)
            turns[-1].extend(actions)
        turns[-1].append(self.action("CLAIM_WIN", self.base))
        return turns

    def _routes(self, roads, extractors, smelters, r):
        kinds, _, _ = self.layout(roads, extractors, smelters)
        occupied = roads | extractors | smelters | (1 << self.base)
        distance = {self.base: 0}
        parent = {self.base: None}
        queue = deque([self.base])
        while queue:
            p = queue.popleft()
            for q in self.neighbors[p]:
                if q in kinds:
                    if not accepts(kinds[q], RESOURCES[r], self.mode) or (p in kinds):
                        continue
                    cost = 0
                elif occupied >> q & 1:
                    cost = 0
                elif q in self.nodes:
                    continue
                else:
                    cost = 1
                nd = distance[p] + cost
                if nd < distance.get(q, 10**9):
                    distance[q] = nd
                    parent[q] = p
                    (queue.appendleft if cost == 0 else queue.append)(q)
        return distance, parent

    def project(self, s, p, kind, r):
        distance, parent = self.routes(s.roads, s.extractors, s.smelters, r)
        kinds, _, _ = self.layout_for(s)
        # A storage endpoint needs a road predecessor, including a future road.
        near = [q for q in self.neighbors[p] if q in distance and q not in kinds]
        if not near:
            return None
        path = None
        for end in sorted(near, key=lambda q: (distance[q], q)):
            candidate = [end]
            while candidate[-1] != self.base:
                candidate.append(parent[candidate[-1]])
            if p not in candidate:
                path = list(reversed(candidate))
                break
        if path is None:
            return None
        steps = [("BUILD", q, "ROAD") for q in path if not self.occupied(s) >> q & 1]
        if not self.occupied(s) >> p & 1:
            steps.append(("BUILD", p, kind))
        return steps

    def completion(self, s, limit, deadline):
        """Try one funded factory schedule; a miss says nothing about feasibility.

        Only BASE stocks and BASE-connected quarry income fund this schedule.
        The final step check is required: these inequalities select a probe,
        never remove an exact-search branch.
        """
        if limit <= 0 or perf_counter() >= deadline:
            return None, 0
        stock = {(p, r): n for p, r, n in s.stock}
        missing = max(0, self.goals[2] - stock.get((self.base, 2), 0))
        if not missing or stock.get((self.base, 1), 0) < self.goals[1] + missing:
            return None, 0
        d = self.turns - s.turn
        if missing > 2 * (d + 1):
            return None, 0
        _, roots, _ = self.layout_for(s)
        income = 5 * sum(
            self.nodes[p] == 0 and roots[0].get(p) == self.base for p in bits(s.extractors)
        )
        best = None
        for p in range(self.v):
            if perf_counter() >= deadline:
                return None, 0
            if p in self.nodes or self.occupied(s) >> p & 1:
                continue
            project = self.project(s, p, "SMELTER", 2)
            if project:
                cost = sum(COSTS[c[2]] for c in project)
                if best is None or (cost, p) < best[:2]:
                    best = (cost, p, project)
        if best is None:
            return None, 0
        cost, p, project = best
        cash = self.cash(s)
        if cash < cost and not income:
            return None, 0
        wait = max(0, (cost - cash + income - 1) // income) if income else 0
        if wait > d or missing > 2 * (d - wait + 1) or cash - cost + income * d < self.goals[0]:
            return None, 0
        if wait + len(project) > limit:
            return None, 0
        state = s
        steps = []
        work = 0

        def take(choice):
            nonlocal state, work
            if len(steps) >= limit or perf_counter() >= deadline:
                return False
            if choice not in self.choices(state):
                return False
            state, _ = self.step(state, choice)
            steps.append(choice)
            work += 1
            return True

        for choice in [("END",)] * wait + project:
            if not take(choice):
                return None, work
        # Project uses an IRON connection; validate ORE supply in this layout.
        if self.layout_for(state)[1][1].get(p) != self.base:
            return None, work
        while not self.won(state):
            remaining = max(
                0, self.goals[2] - sum(n for q, r, n in state.stock if q == self.base and r == 2)
            )
            choice = (
                ("PRODUCE", p, min(2, remaining))
                if remaining and not state.produced >> p & 1
                else ("END",)
            )
            if not take(choice):
                return None, work
        return steps, work

    def funded_ore_project(self, s):
        """An optional committed connection, including all its road costs."""
        stock = {(p, r): n for p, r, n in s.stock}
        need = self.goals[1] + max(0, self.goals[2] - stock.get((self.base, 2), 0))
        if stock.get((self.base, 1), 0) >= need:
            return []
        candidates = []
        for p, r in self.nodes.items():
            if r != 1:
                continue
            project = self.project(s, p, "IRON_MINE", 1)
            if project:
                cost = sum(COSTS[c[2]] for c in project)
                if cost <= self.cash(s):
                    candidates.append((cost, p, project))
        return min(candidates)[2] if candidates else []

    def ready_probes(self, s, limit, available, last=None, budget_aware=False):
        """Cheap applicability hints only; a skipped probe never cuts DFS."""
        base = [0, 0, 0]
        global_iron = 0
        global_stone = 0
        for p, r, n in s.stock:
            if p == self.base:
                base[r] += n
            if r == 2:
                global_iron += n
            if budget_aware and r == 0:
                global_stone += n
        # Even free roads/ore cannot fit more than limit PRODUCE actions.
        batches = (max(0, self.goals[2] - global_iron) + 1) // 2
        if batches > limit:
            return ()
        stone, ore, iron = base
        missing = max(0, self.goals[2] - iron)
        ends = self.turns - s.turn
        q, mines, factories = self.counts(s)
        if budget_aware and batches:
            # Optimistic funds within the non-PRODUCE part of this allowance.
            # New quarry profit includes its immediate five and build cost ten.
            horizon = min(ends, limit - batches)
            funds = (
                global_stone
                + 5 * q * horizon
                + (self.site_counts[0] - q) * max(0, 5 * (horizon + 1) - 10)
            )
            if funds < 20:
                # No new factory can be funded; use existing activation capacity.
                if not factories:
                    return ()
                unused = (s.smelters & ~s.produced).bit_count()
                required_ends = (max(0, batches - unused) + factories - 1) // factories
                if batches + required_ends > limit or required_ends > ends:
                    return ()
        capacity = 2 * ((s.smelters & ~s.produced).bit_count() + factories * ends)
        stone_ready = stone + 5 * q * ends >= self.goals[0]
        ore_ready = ore + 5 * mines * ends >= self.goals[1] + missing
        selected = []
        if missing and capacity >= missing and stone_ready and ore_ready:
            selected.append("production")
        if (
            "economic" in available
            and "production" not in selected
            and missing
            and ore >= self.goals[1] + missing
            and missing <= 2 * (ends + 1)
            and (stone >= 20 or (q and ends))
        ):
            selected.append("economic")
        if ends and q and (not stone_ready or (stone < 20 and missing > capacity)):
            selected.append("capital")
        if not ore_ready and mines < self.site_counts[1] and stone >= 10:
            selected.append("investment")
        if last and last[0] == "BUILD" and last[2] == "ROAD" and last[1] in self.planned:
            selected.append("planned")
        selected = [policy for policy in selected if policy in available]
        if stone_ready and ore_ready and not any(p in selected for p in ("production", "economic")):
            selected.append("balanced")
        return tuple(selected)

    def ordered(self, s, choices, policy="balanced"):
        """Rank whole production projects while retaining every legal choice."""
        totals = self.totals(s)
        q, m, f = self.counts(s)
        d = self.turns - s.turn + 1
        iron = max(0, self.goals[2] - totals[2])
        ore_need = self.goals[1] + iron
        targets = []
        urgent = None
        funded = []
        if policy in ("deadline", "projects"):
            cash = self.cash(s)
            base_ore = sum(n for p, r, n in s.stock if p == self.base and r == 1)
            _, income_roots, _ = self.layout_for(s)
            income = 5 * sum(
                self.nodes[p] == 0 and income_roots[0].get(p) == self.base
                for p in bits(s.extractors)
            )
            capacity = 2 * ((s.smelters & ~s.produced).bit_count() + f * (d - 1))
            extra = (max(0, iron - capacity) + 2 * d - 1) // (2 * d)
        for p, r in self.nodes.items():
            kind = "STONE_QUARRY" if r == 0 else "IRON_MINE"
            project = self.project(s, p, kind, r)
            if project:
                cost = sum(COSTS[c[2]] for c in project)
                # Saving prioritizes growth until it can fund the full chain.
                weight = (
                    (5 if iron and not f else 3)
                    if r == 0
                    else (5 if totals[1] + 5 * m * (d - 1) < ore_need else 0.1)
                )
                if policy == "capital" and r == 0:
                    weight *= 3
                if policy == "production" and r == 1:
                    weight *= 1.5
                targets.append((cost / max(weight, 0.1), project))
        for p in bits(s.smelters):
            project = self.project(s, p, "SMELTER", 2)
            if project:
                targets.append((sum(COSTS[c[2]] for c in project) / 10, project))
        if iron:
            occupied = self.occupied(s)
            candidates = [p for p in range(self.v) if p not in self.nodes and not occupied >> p & 1]
            nearest = self.road_distances(s.roads) if self.distance_reuse else None
            candidates.sort(
                key=lambda p: (
                    nearest[p]
                    if nearest is not None
                    else min(
                        (
                            abs(p % self.w - z % self.w) + abs(p // self.w - z // self.w)
                            for z in bits(s.roads)
                        ),
                        default=1000,
                    ),
                    abs(p % self.w - self.base % self.w) + abs(p // self.w - self.base // self.w),
                    p,
                )
            )
            for p in candidates[:16]:
                project = self.project(s, p, "SMELTER", 2)
                if project:
                    cost = sum(COSTS[c[2]] for c in project)
                    capacity = 2 * ((s.smelters & ~s.produced).bit_count() + f * (d - 1))
                    weight = 8 if capacity < iron else 0.15
                    if not totals[1] and not m:
                        weight *= 0.3
                    targets.append((cost / weight, project))
                    if (
                        policy in ("deadline", "projects")
                        and capacity < iron <= capacity + 2 * d
                        and iron > capacity + 2 * (d - 1)
                        and base_ore >= self.goals[1] + iron
                        and cost <= cash
                        and cash - cost + income * (d - 1) >= self.goals[0]
                    ):
                        if urgent is None or (cost, p) < urgent[:2]:
                            urgent = (cost, p, project)
                    if (
                        policy == "projects"
                        and extra > 0
                        and base_ore >= self.goals[1] + iron
                        and cash + income * (d - 1) >= self.goals[0] + cost + 20 * (extra - 1)
                    ):
                        # Optimistic remaining factory fees omit unknown future roads.
                        # This ranks choices only; production DP supplies the proof.
                        wait = (
                            0
                            if cash >= cost
                            else (cost - cash + income - 1) // income
                            if income
                            else d
                        )
                        action = project[0] if not wait else ("END",)
                        if wait < d and action in choices:
                            funded.append((wait, cost, p, action))
        priorities = {}
        for score, project in targets:
            if project:
                priorities[project[0]] = min(priorities.get(project[0], float("inf")), score)
        # Prefer available production, but protect enough ore for mixed goals.
        for c in choices:
            if c[0] == "PRODUCE":
                priorities[c] = -0.5 - 0.1 * c[2] if totals[1] - c[2] >= self.goals[1] else 20
        # One-new-factory completion preference, never an action cut.
        if urgent is not None and not funded:
            priorities[urgent[2][0]] = -0.25
        preferred = min(funded)[3] if funded else None
        if preferred is not None:
            priorities[preferred] = -0.25
        best = min(targets, key=lambda item: item[0])[1] if targets else []
        project_cost = sum(COSTS[c[2]] for c in best)
        _, roots, _ = self.layout_for(s)
        funded_income = any(
            self.nodes[p] == 0 and roots[0].get(p) == self.base for p in bits(s.extractors)
        )
        saving = policy == "capital" and funded_income and self.cash(s) < project_cost

        def key(c):
            if c[0] == "END":
                return (priorities.get(c, 0 if saving else 50), c)
            score = priorities.get(c, 100)
            if policy == "planned" and c[0] == "BUILD" and c[1] in self.planned:
                score *= 0.75
            return score, c

        ordered = sorted(choices, key=key)
        if policy == "investment" and not m and totals[1] < ore_need:
            # Probe preference only: fund ore supply before new production.
            # Keep every action, including factories, available to exact DFS.
            is_factory = lambda c: c[0] == "BUILD" and c[2] == "SMELTER"
            return [c for c in ordered if not is_factory(c)] + [c for c in ordered if is_factory(c)]
        return ordered


class _ProductionBudget(Exception):
    pass


class ProductionDP:
    """Minimum STONE in the free-road/infinite-ORE production relaxation.

    All existing available factories have already produced eagerly. b counts
    remaining two-IRON batches; f is used now but available after the next END.
    Only completed subproblems are cached. Budget skips are weak passes.
    """

    def __init__(self, stone_goal, quarry_sites, deadline=float("inf"), max_entries=20000):
        self.goal, self.sites = stone_goal, quarry_sites
        self.deadline, self.max_entries = deadline, max_entries
        self.cache = {}
        self.skipped = 0

    def required(self, d, q, f, b):
        if d > 128 or (d and b > 128):
            self.skipped += 1
            return 0
        try:
            return self._required(d, q, f, b)
        except (_ProductionBudget, RecursionError):
            self.skipped += 1
            return 0

    def _required(self, d, q, f, b):
        if not d:
            return self.goal + 20 * b  # No future income; new quarries only cost stone.
        f = min(f, b)
        key = d, q, f, b
        if key in self.cache:
            return self.cache[key]
        if perf_counter() >= self.deadline or len(self.cache) >= self.max_entries:
            raise _ProductionBudget
        answer = self.goal if not b else float("inf")
        answer = min(answer, max(0, self._required(d - 1, q, f, max(0, b - f)) - 5 * q))
        if answer and q < self.sites:
            answer = min(answer, max(10, self._required(d, q + 1, f, b) + 5))
        if answer and b:
            answer = min(answer, 20 + self._required(d, q, f + 1, b - 1))
        if len(self.cache) >= self.max_entries:
            raise _ProductionBudget
        self.cache[key] = answer
        return answer


class Bounds:
    """Optimistic feasibility filters; failure is a proof only under the stated model."""

    def __init__(self, model, deadline):
        self.model, self.deadline = model, deadline
        self.dps = {}
        self.dp_skipped = 0
        self.production_dp = None

    def demands(self, s, total=None):
        """Lower-bound missing ore mines/factories using optimistic remaining capacity."""
        m = self.model
        total = m.totals(s) if total is None else total
        q, o, f = m.counts(s)
        d = m.turns - s.turn
        h = max(0, m.goals[2] - total[2])
        a = (s.smelters & ~s.produced).bit_count()
        nf = max(0, (h - 2 * a - 2 * f * d + 2 * (d + 1) - 1) // (2 * (d + 1)))
        missing = max(0, m.goals[1] + h - total[1])
        nm = (max(0, missing - 5 * o * d) + 5 * (d + 1) - 1) // (5 * (d + 1))
        return total, q, o, f, d, h, nf, missing, nm

    def resource(self, s, summary=None):
        """Reject only if even free access and maximal production miss a goal."""
        m = self.model
        t, q, o, f, d, h, nf, missing, nm = self.demands(s) if summary is None else summary
        empty = m.v - self.occupied_count(s) - sum(1 for p in m.nodes if not s.extractors >> p & 1)
        if nf > empty or nm > m.site_counts[1] - o:
            return False
        uq = m.site_counts[0] - q
        stone_upper = t[0] + 5 * q * d + uq * max(0, 5 * (d + 1) - 10) - 15 * nm - 20 * nf
        return stone_upper >= m.goals[0]

    def occupied_count(self, s):
        return self.model.occupied(s).bit_count()

    def capital(self, s, summary=None):
        """Compare available stone with a free-road typed funding threshold."""
        m = self.model
        t, q, o, f, d, h, nf, missing, nm = self.demands(s) if summary is None else summary
        goal = m.goals[0] + 20 * nf
        if goal not in self.dps:
            # Optional DP cache budget, never a search state cap. Skipping
            # weakens this filter to zero; no impossibility follows.
            if len(self.dps) >= 16:
                self.dp_skipped += 1
                return True
            self.dps[goal] = CapitalDP(
                goal, *m.site_counts, deadline=self.deadline, max_entries=20000
            )
        threshold = self.dps[goal].required(d, q, o, (missing + 4) // 5)
        return t[0] >= threshold

    def production(self, s, summary=None):
        """Use the infinite-ore relaxation to reject impossible production schedules."""
        m = self.model
        if summary is None:
            total = m.totals(s)
            q, _, f = m.counts(s)
        else:
            total, q, _, f = summary[:4]
        h = max(0, m.goals[2] - total[2])
        a = (s.smelters & ~s.produced).bit_count()
        b = max(0, (h + 1) // 2 - a)
        if not b:
            return True
        if self.production_dp is None:
            self.production_dp = ProductionDP(m.goals[0], m.site_counts[0], self.deadline)
        return total[0] >= self.production_dp.required(m.turns - s.turn, q, f, b)


def solve(
    level,
    seconds=30,
    bounds="both",
    probes=True,
    relay_mode="matching",
    improvements="both",
    preparation="none",
    scheduling="projects_adaptive",
    probe_trigger="interval",
    probe_interval=PROBE_INTERVAL,
):
    """Search the finite normalized state graph with independently replayed wins.

    Defaults are the adopted project ordering and on-demand production DP.
    Optional controls exist for retained ablations/forced-search tests; public
    callers use the adopted preset. Probe misses never prune a search branch.
    """
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not isfinite(seconds)
        or seconds < 0
    ):
        raise ValueError("seconds must be finite nonnegative")
    if bounds not in ("none", "resource", "dp", "both"):
        raise ValueError("unknown bounds")
    if improvements not in ("none", "investment", "distance", "both"):
        raise ValueError("unknown improvements")
    if preparation not in ("none", "summary", "early"):
        raise ValueError("unknown preparation")
    if scheduling not in (
        "none",
        "ordering",
        "bound",
        "both",
        "projects",
        "projects_bound",
        "projects_adaptive",
    ):
        raise ValueError("unknown scheduling")
    if probe_trigger not in ("interval", "policy", "policy_budget"):
        raise ValueError("unknown probe trigger")
    if (
        isinstance(probe_interval, bool)
        or not isinstance(probe_interval, int)
        or probe_interval <= 0
    ):
        raise ValueError("probe_interval must be a positive integer")
    start = perf_counter()
    deadline = start + seconds
    m = Model(level, relay_mode, improvements in ("distance", "both"))
    filters = Bounds(m, deadline)
    # No IRON requirement: SMELTER can be replaced by cheaper ROAD in any
    # useful old-resource plan, and surplus initial IRON has no reverse recipe.
    # Keep the proven old path, then replay against the ORIGINAL Stage3 input.
    if m.goals[2] == 0:
        from copy import deepcopy

        projected = deepcopy(level)
        projected["structures"][0]["storage"] = dict(zip(RESOURCES[:2], m.start[:2]))
        projected["level_goal"]["target_resources"] = dict(zip(RESOURCES[:2], m.goals[:2]))
        remaining = max(0, deadline - perf_counter())
        old = solve_stage2(
            projected, seconds=remaining, guidance="both", max_states=None, relay_mode=relay_mode
        )
        if old.get("plan") is not None:
            validate_plan(level, old["plan"], relay_mode)
        if perf_counter() >= deadline:
            old.update(status="UNKNOWN", reason="time_limit", plan=None)
        old.update(engine="stage2-reuse", seconds=perf_counter() - start)
        return old
    production_active = scheduling in ("bound", "both", "projects_bound")
    metrics = dict(
        production_dp_queries=0,
        production_dp_root_probe_queries=0,
        production_dp_activations=int(production_active),
        production_dp_activation_reason="initial" if production_active else None,
        production_prunes=0,
        early_checks=0,
        early_prunes=0,
        expanded=0,
        duplicates=0,
        resource_prunes=0,
        dp_prunes=0,
        probe_work=0,
        probe_calls=0,
        investment_attempts=0,
        economic_attempts=0,
        completion_work=0,
        probe_policy=None,
        probe_state_checks=0,
        probe_state_skips=0,
        probe_policy_attempts={},
        root_probe_calls=0,
        later_probe_calls=0,
    )

    def possible(s, stock=None):
        summary = None
        if stock is not None:
            metrics["early_checks"] += 1
        if preparation != "none" and bounds != "none":
            total = None
            if stock is not None:
                # raw.stock is still the parent's tuple; use the UPDATED dict.
                total = [0, 0, 0]
                for (_, r), amount in stock.items():
                    total[r] += amount
            summary = filters.demands(s, total)
        if bounds in ("resource", "both") and not filters.resource(s, summary):
            metrics["resource_prunes"] += 1
            if stock is not None:
                metrics["early_prunes"] += 1
            return False
        if bounds in ("dp", "both") and not filters.capital(s, summary):
            metrics["dp_prunes"] += 1
            if stock is not None:
                metrics["early_prunes"] += 1
            return False
        if production_active:
            metrics["production_dp_queries"] += 1
            if not filters.production(s, summary):
                metrics["production_prunes"] += 1
                if stock is not None:
                    metrics["early_prunes"] += 1
                return False
        return True

    admit = possible if preparation == "early" and bounds != "none" else None

    def result(status, reason, steps=None):
        plan = None
        if steps is not None and perf_counter() < deadline:
            plan = m.plan(steps)
            validate_plan(level, plan, relay_mode)
        if perf_counter() >= deadline:
            status, reason, plan = "UNKNOWN", "time_limit", None
        return dict(
            status=status,
            reason=reason,
            plan=plan,
            seconds=perf_counter() - start,
            **metrics,
            production_dp_entries=len(filters.production_dp.cache)
            if filters.production_dp is not None
            else 0,
            production_dp_skipped=filters.production_dp.skipped
            if filters.production_dp is not None
            else 0,
            dp_entries=sum(len(x.cache) for x in filters.dps.values()),
            dp_skipped=filters.dp_skipped + sum(x.skipped for x in filters.dps.values()),
            geometry_cache=m.layout.cache_info()._asdict(),
            road_distance_cache=m.road_distances.cache_info()._asdict(),
        )

    if not m.turns:
        return result("INFEASIBLE", "no_claim_turn")
    if perf_counter() >= deadline:
        return result("UNKNOWN", "time_limit")
    root = m.initial()
    if not possible(root):
        return result("INFEASIBLE", "initial_bound")
    policies = (("planned",) if m.planned else ()) + ("balanced", "capital", "production")
    if improvements in ("investment", "both"):
        policies += ("investment", "economic")

    def probe(s, limit, selected=policies):
        metrics["probe_calls"] += 1
        metrics["root_probe_calls" if metrics["expanded"] == 1 else "later_probe_calls"] += 1
        for policy in selected:
            attempts = metrics["probe_policy_attempts"]
            attempts[policy] = attempts.get(policy, 0) + 1
            if policy == "investment":
                metrics["investment_attempts"] += 1
            if policy == "economic":
                metrics["economic_attempts"] += 1
            state = s
            steps = []
            seen = {state}
            committed = []
            completion_used = 0
            for _ in range(limit):
                if perf_counter() >= deadline:
                    return None
                if m.won(state):
                    metrics["probe_policy"] = policy
                    return steps
                if policy == "economic":
                    if len(steps) + completion_used >= limit:
                        break
                    suffix, work = m.completion(
                        state, max(0, limit - len(steps) - completion_used), deadline
                    )
                    completion_used += work
                    metrics["completion_work"] += work
                    metrics["probe_work"] += work
                    if suffix is not None:
                        metrics["probe_policy"] = policy
                        return steps + suffix
                    if len(steps) + completion_used >= limit:
                        break
                    if not committed:
                        committed = m.funded_ore_project(state)
                chosen = None
                choices = (
                    [committed[0]]
                    if committed
                    else m.ordered(state, list(m.choices(state)), policy)
                )
                for choice in choices:
                    child, _ = (
                        m.step(state, choice)
                        if admit is None
                        else m.step(state, choice, admit=admit)
                    )
                    metrics["probe_work"] += 1
                    if (
                        child is not None
                        and child not in seen
                        and (admit is not None or possible(child))
                    ):
                        chosen = choice, child
                        break
                    if perf_counter() >= deadline:
                        return None
                if chosen is None:
                    break
                choice, state = chosen
                steps.append(choice)
                seen.add(state)
                if committed:
                    committed.pop(0)
            # The last allowed transition may itself reach the goal.
            if perf_counter() >= deadline:
                return None
            if m.won(state):
                metrics["probe_policy"] = policy
                return steps
        return None

    parents = {root: None}
    stack = [(root, None)]
    found = None
    while stack:
        if perf_counter() >= deadline:
            return result("UNKNOWN", "time_limit")
        s, iterator = stack[-1]
        if iterator is None:
            metrics["expanded"] += 1
            if m.won(s):
                found = []
            elif probes:
                if metrics["expanded"] == 1:
                    before = metrics["production_dp_queries"]
                    found = probe(s, INITIAL_PROBE_DECISIONS)
                    metrics["production_dp_root_probe_queries"] = (
                        metrics["production_dp_queries"] - before
                    )
                elif probe_trigger == "interval":
                    if metrics["expanded"] % probe_interval == 0:
                        found = probe(s, FOLLOWUP_PROBE_DECISIONS)
                else:
                    metrics["probe_state_checks"] += 1
                    selected = (
                        m.ready_probes(s, FOLLOWUP_PROBE_DECISIONS, policies, parents[s][1], True)
                        if probe_trigger == "policy_budget"
                        else m.ready_probes(s, FOLLOWUP_PROBE_DECISIONS, policies, parents[s][1])
                    )
                    if selected:
                        found = probe(s, FOLLOWUP_PROBE_DECISIONS, selected)
                    else:
                        metrics["probe_state_skips"] += 1
            if found is not None:
                prefix = []
                p = s
                while parents[p] is not None:
                    p, choice = parents[p]
                    prefix.append(choice)
                return result(
                    "FEASIBLE", "probe" if found else "search", list(reversed(prefix)) + found
                )
            if scheduling == "projects_adaptive" and not production_active:
                # Initial probes have private states, so exact DFS still has only
                # its root here. A failed probe is not an impossibility proof.
                if perf_counter() >= deadline:
                    return result("UNKNOWN", "time_limit")
                production_active = True
                metrics["production_dp_activations"] += 1
                metrics["production_dp_activation_reason"] = (
                    "root_probe_miss" if probes else "exact_search_entry"
                )
                metrics["production_dp_queries"] += 1
                if not filters.production(s):
                    metrics["production_prunes"] += 1
                    return result("INFEASIBLE", "production_activation_bound")
            iterator = iter(
                m.ordered(
                    s,
                    list(m.choices(s)),
                    "projects"
                    if scheduling in ("projects", "projects_bound", "projects_adaptive")
                    else "deadline"
                    if scheduling in ("ordering", "both")
                    else "balanced",
                )
            )
            stack[-1] = (s, iterator)
        choice = next(iterator, None)
        if choice is None:
            stack.pop()
            continue
        child, _ = m.step(s, choice) if admit is None else m.step(s, choice, admit=admit)
        if child is None:
            continue
        if child in parents:
            metrics["duplicates"] += 1
            continue
        if admit is None and not possible(child):
            continue
        parents[child] = s, choice
        stack.append((child, None))
    return result("INFEASIBLE", "exhausted")
