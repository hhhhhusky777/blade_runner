"""Offline conditional Stage 1 algorithms; no API/client/environment imports.

This module contains the shared grid geometry and the adopted Stage1 DFS.
All affordable adjacent cell builds remain in exact search. Improved DFS omits
only proved unnecessary zero-income waits; route distances only order successors. The independent reference module owns strict replay.
"""

from collections import deque
from dataclasses import dataclass
from time import perf_counter


@dataclass(frozen=True, slots=True)
class State:
    """Normalized state: one-based turn, cell bitmasks, BASE cash and site stocks.

    Existing quarries have mined this turn; connected stock is pooled at BASE.
    Exact keys retain topology and disconnected inventories, not producer counts.
    """

    turn: int
    roads: int
    quarries: int
    cash: int
    stocks: tuple[int, ...]


class Model:
    """Grid/action owner; construction and income normalize before memoization."""

    def __init__(self, level):
        self.level = level
        b = level["board"]
        self.w, self.h = b["width"], b["height"]
        self.v = self.w * self.h
        self.nodes = tuple(n["y"] * self.w + n["x"] for n in b["resource_nodes"])
        self.node_index = {p: i for i, p in enumerate(self.nodes)}
        self.k = len(self.nodes)
        base = level["structures"][0]
        self.base = base["y"] * self.w + base["x"]
        self.initial_cash = (base.get("storage") or {}).get("STONE", 0)
        self.goal = level["level_goal"]["target_resources"]["STONE"]
        self.turns = level["max_turns"]
        self.neighbors = tuple(
            tuple(
                q
                for q in (
                    p - self.w if p >= self.w else -1,
                    p + self.w if p + self.w < self.v else -1,
                    p - 1 if p % self.w else -1,
                    p + 1 if p % self.w + 1 < self.w else -1,
                )
                if q >= 0
            )
            for p in range(self.v)
        )
        self.node_bits = sum(1 << p for p in self.nodes)

    def road_bound(self, state, parameters):
        """Optimistic final stone; selected models may strengthen this safe bound."""
        return road_investment_upper(self, state, parameters)

    def initial(self):
        return State(1, 0, 0, self.initial_cash, (0,) * self.k)

    def occupied(self, s):
        return s.roads | s.quarries | (1 << self.base)

    def tree(self, s):
        """Base transfer component, with all storage-storage edges removed."""
        occupied = self.occupied(s)
        parent = {self.base: None}
        queue = deque([self.base])
        while queue:
            p = queue.popleft()
            for q in self.neighbors[p]:
                if q in parent or not (occupied >> q & 1):
                    continue
                if not ((s.roads >> p & 1) or (s.roads >> q & 1)):
                    continue
                parent[q] = p
                queue.append(q)
        return parent

    def settle(self, s):
        """Pool every base-connected site stock; disconnected stock stays local."""
        parent = self.tree(s)
        stocks = list(s.stocks)
        cash = s.cash
        for i, p in enumerate(self.nodes):
            if p in parent:
                cash += stocks[i]
                stocks[i] = 0
        return State(s.turn, s.roads, s.quarries, cash, tuple(stocks))

    def step(self, s, cell):
        """cell=None ends a turn; caller supplies a legal affordable build."""
        stocks = list(s.stocks)
        if cell is None:
            for i, p in enumerate(self.nodes):
                if s.quarries >> p & 1:
                    stocks[i] += 5
            return self.settle(State(s.turn + 1, s.roads, s.quarries, s.cash, tuple(stocks)))
        if cell in self.node_index:
            stocks[self.node_index[cell]] = 5
            return self.settle(
                State(s.turn, s.roads, s.quarries | (1 << cell), s.cash - 10, tuple(stocks))
            )
        return self.settle(State(s.turn, s.roads | (1 << cell), s.quarries, s.cash - 1, s.stocks))

    def choices(self, s):
        """Enumerate all affordable adjacent builds and the legal turn advance."""
        occupied = self.occupied(s)
        cells = set()
        for p in range(self.v):
            if occupied >> p & 1:
                cells.update(q for q in self.neighbors[p] if not occupied >> q & 1)
        cells = [p for p in cells if s.cash >= (10 if p in self.node_index else 1)]
        remaining = [p for p in self.nodes if not s.quarries >> p & 1]

        # An ordering hint only. Every affordable cell and legal END remains.
        def priority(p):
            if p in self.node_index:
                return (0, 0, p)
            distance = min(
                (abs(p % self.w - q % self.w) + abs(p // self.w - q // self.w) for q in remaining),
                default=self.v,
            )
            return (1, distance, p)

        cells.sort(key=priority)
        if s.turn < self.turns:
            # Prefer collecting profitable existing production to irrelevant roads.
            if s.quarries:
                cells.insert(0, None)
            else:
                cells.append(None)
        return cells

    def plan(self, steps):
        """Expand normalized decisions into ordered BUILD/MINE/TRANSFER/CLAIM actions."""
        s = self.initial()
        turns = [[]]
        action = lambda name, **args: {"action": name, "args": args}
        coord = lambda p: (p % self.w, p // self.w)
        for cell in steps:
            if cell is None:
                turns.append([])
                raw = State(
                    s.turn + 1,
                    s.roads,
                    s.quarries,
                    s.cash,
                    tuple(
                        x + (5 if s.quarries >> p & 1 else 0) for x, p in zip(s.stocks, self.nodes)
                    ),
                )
                mined = [p for p in self.nodes if s.quarries >> p & 1]
            else:
                quarry = cell in self.node_index
                turns[-1].append(
                    action(
                        "BUILD",
                        type="STONE_QUARRY" if quarry else "ROAD",
                        x=coord(cell)[0],
                        y=coord(cell)[1],
                    )
                )
                stocks = list(s.stocks)
                if quarry:
                    stocks[self.node_index[cell]] = 5
                raw = State(
                    s.turn,
                    s.roads | (0 if quarry else 1 << cell),
                    s.quarries | (1 << cell if quarry else 0),
                    s.cash - (10 if quarry else 1),
                    tuple(stocks),
                )
                mined = [cell] if quarry else []
            for p in mined:
                turns[-1].append(action("MINE", x=coord(p)[0], y=coord(p)[1]))
            tree = self.tree(raw)
            inventory = {
                p: raw.stocks[i] for i, p in enumerate(self.nodes) if raw.quarries >> p & 1
            }
            inventory[self.base] = raw.cash
            for source in self.nodes:
                if source not in tree or not inventory.get(source):
                    continue
                current = source
                while current != self.base:
                    path = [current]
                    p = tree[current]
                    while p not in inventory:
                        path.append(p)
                        p = tree[p]
                    path.append(p)
                    amount = inventory[current]
                    turns[-1].append(
                        action(
                            "TRANSFER",
                            path=[list(coord(x)) for x in path],
                            resource="STONE",
                            amount=amount,
                        )
                    )
                    inventory[current] = 0
                    inventory[p] += amount
                    current = p
            s = self.settle(raw)
        turns[-1].append(action("CLAIM_WIN", x=coord(self.base)[0], y=coord(self.base)[1]))
        return turns


def investment_upper(model, s):
    """Safe total-inventory bound; see whiteboard for the last-three-turn proof."""
    remaining = model.turns - s.turn
    q = s.quarries.bit_count()
    total = s.cash + sum(s.stocks)
    unbuilt = model.k - q
    if remaining == 2:
        # Only quarries built NOW have positive net return before the deadline.
        # Relax all inventory into spendable cash, but still require 10 up front.
        unbuilt = min(unbuilt, max(0, (total - 5) // 5))
    return total + 5 * q * remaining + unbuilt * max(0, 5 * (remaining + 1) - 10)


def road_parameters(model):
    """Static road contacts; ordinary cells exclude BASE and all stone nodes."""
    contacts = tuple(
        sum(1 << p for p in model.neighbors[node] if p != model.base and p not in model.node_index)
        for node in model.nodes
    )
    touches = tuple(
        sum(1 << node for node in model.neighbors[p] if node in model.node_index)
        if p != model.base and p not in model.node_index
        else 0
        for p in range(model.v)
    )
    return contacts, touches, max((mask.bit_count() for mask in touches), default=0)


def road_investment_upper(model, s, parameters):
    """Admissible inventory bound charging a lower bound on FUTURE roads.

    Existing stocks/production get free base access. Each positively contributing
    new quarry not already beside a road needs a new road; each road covers at
    most static A nodes. With <=2 turns left the best relaxed choice is m=0.
    """
    remaining = model.turns - s.turn
    q = s.quarries.bit_count()
    total = s.cash + sum(s.stocks)
    gain = 5 * (remaining + 1) - 10
    if gain <= 0:
        return total + 5 * q * remaining
    contacts, _, cover = parameters
    if not cover:
        return total + 5 * q * remaining
    count = model.k - q
    if remaining == 2:
        count = min(count, max(0, (total - 5) // 5))
    free = sum(
        bool(mask & s.roads)
        for node, mask in zip(model.nodes, contacts)
        if not s.quarries >> node & 1
    )
    extra = max(0, count - free)
    roads = (extra + cover - 1) // cover
    return total + 5 * q * remaining + count * gain - roads


def base_income(model, s):
    """Return per-turn stone deliverable to BASE with the current topology."""
    connected = model.tree(s)
    return 5 * sum(bool(s.quarries >> p & 1) and p in connected for p in model.nodes)


def connection_routes(model, s, affordable_only=False, resource=None):
    """0-1 BFS; optionally retain only routes passing the gross-cash filter."""
    occupied = model.occupied(s)
    roots = model.tree(s) if resource is None else model.tree(s, resource)
    distance = {p: 0 for p in roots}
    parent = {p: None for p in roots}
    # New endpoints require ten cash; pending built endpoints require roads only.
    # Nonnegative edge costs make every affordable route prefix affordable too.
    unseen = model.v + 20
    if affordable_only:
        pending = any(s.quarries >> p & 1 and p not in roots for p in model.nodes)
        budget = s.cash if pending else s.cash - 10
        if budget < 0:
            return distance, parent
        unseen = budget + 1
    queue = deque(roots)
    done = set()
    while queue:
        p = queue.popleft()
        if p in done:
            continue
        done.add(p)
        if p in model.node_index and not s.quarries >> p & 1:
            continue
        p_storage = p == model.base or p in model.node_index
        for q in model.neighbors[p]:
            if (
                resource is not None
                and model.relay_mode == "matching"
                and q in model.node_index
                and model.resources[model.node_index[q]] != resource
            ):
                continue
            q_storage = q == model.base or q in model.node_index
            if p_storage and q_storage:
                continue
            cost = 0 if occupied >> q & 1 or q_storage else 1
            nd = distance[p] + cost
            if nd < distance.get(q, unseen):
                distance[q], parent[q] = nd, p
                if cost:
                    queue.append(q)
                else:
                    queue.appendleft(q)
    return distance, parent


def route_cells(parent, target):
    path = []
    while parent[target] is not None:
        path.append(target)
        target = parent[target]
    return list(reversed(path))


def productive_choices(model, s, choices, affordable_only=False):
    """Route hints change order only: no build or END is discarded here."""
    distance, parent = connection_routes(model, s, affordable_only)
    routes = []
    for i, p in enumerate(model.nodes):
        built = bool(s.quarries >> p & 1)
        if p not in distance or (built and not s.stocks[i]):
            continue
        cost = distance[p] + (0 if built else 10)
        if cost <= s.cash:
            routes.append((not built, cost, p))
    hint = None
    if routes:
        path = route_cells(parent, min(routes)[-1])
        hint = next((x for x in path if not model.occupied(s) >> x & 1), None)
    position = {p: i for i, p in enumerate(choices)}
    # Invest in exposed quarries before waiting; keep every other choice.
    return sorted(
        choices,
        key=lambda p: (
            0
            if p == hint and p is not None
            else 1
            if p in model.node_index
            else 2
            if p is None
            else 3,
            position[p],
        ),
    )


def one_quarry_completion(model, initial, affordable_only=False):
    """Exact for the initial one-quarry plan family, success shortcut only."""
    distance, parent = connection_routes(model, initial, affordable_only)
    for p in model.nodes:
        if p not in distance:
            continue
        cost = distance[p] + 10
        if cost > initial.cash or initial.cash - cost + 5 * model.turns < model.goal:
            continue
        turns = max(1, (model.goal - initial.cash + cost + 4) // 5)
        return route_cells(parent, p) + [None] * (turns - 1)
    return None


def greedy_probe(
    model, start, parameters, deadline, max_actions=128, max_work=512, diagnostics=None
):
    """Two work-bounded legal rollouts under the shared solve deadline.

    Rejected children count too. The caller owns the per-solve trial allowance;
    a miss never certifies impossibility or removes exact-search choices.
    """
    contacts, touches, _ = parameters
    work = scored = action_cap_hits = dead_ends = 0
    steps, quarry_first = [], True

    def done(termination, suffix=None):
        if diagnostics is not None:
            diagnostics.update(
                termination=termination,
                policy="quarry_first" if quarry_first else "connected_first",
                selected_steps_last_policy=len(steps),
                suffix_steps=len(suffix) if suffix is not None else None,
                trials=work,
                scored_candidates=scored,
                action_cap_hits=action_cap_hits,
                dead_ends=dead_ends,
            )
        return suffix, work

    for quarry_first in (True, False):
        s, steps = start, []
        for action_index in range(max_actions + 1):
            if perf_counter() >= deadline:
                return done("global_deadline")
            if s.cash >= model.goal:
                return done("success", steps)
            connected = model.tree(s)
            income = 5 * sum(
                bool(s.quarries >> node & 1) and node in connected for node in model.nodes
            )
            if income and s.cash + income * (model.turns - s.turn) >= model.goal:
                waits = (model.goal - s.cash + income - 1) // income
                if len(steps) + waits <= max_actions:
                    return done("success", steps + [None] * waits)
            if work >= max_work:
                return done("work_limit")
            if action_index == max_actions:
                action_cap_hits += 1
                break
            covered = sum(1 << node for node, mask in zip(model.nodes, contacts) if mask & s.roads)
            uncovered = model.node_bits & ~covered
            occupied = model.occupied(s)
            ranked = []
            for position, cell in enumerate(model.choices(s)):
                if perf_counter() >= deadline:
                    return done("global_deadline")
                scored += 1
                if cell is None:
                    score = (3, 0, 0, position)
                elif cell in model.node_index:
                    joins = any(s.roads >> n & 1 and n in connected for n in model.neighbors[cell])
                    score = (0 if quarry_first or joins else 2, 0, 0, position)
                else:
                    cover = (touches[cell] & uncovered).bit_count()
                    expansion = max(
                        (
                            (touches[n] & uncovered).bit_count()
                            for n in model.neighbors[cell]
                            if not occupied >> n & 1
                        ),
                        default=0,
                    )
                    score = (1, -cover, -expansion, position)
                ranked.append((score, cell))
            chosen = None
            # Rank before copying/settling child states. Quarry connectivity is
            # known from an adjacent ROAD in the current base component.
            for _, cell in sorted(ranked):
                if perf_counter() >= deadline:
                    return done("global_deadline")
                if work >= max_work:
                    return done("work_limit")
                child = model.step(s, cell)
                work += 1
                if model.road_bound(child, parameters) >= model.goal:
                    chosen = cell, child
                    break
            if chosen is None:
                dead_ends += 1
                break
            cell, s = chosen
            steps.append(cell)
    return done("action_limit" if action_cap_hits else "dead_end")


def prefix_steps(parents, state):
    """Recover decisions from the exact initial-state predecessor chain."""
    steps = []
    while parents[state] is not None:
        state, cell = parents[state]
        steps.append(cell)
    steps.reverse()
    return steps


def solve(
    level: dict, seconds: float = 24.0, max_states=float("inf"), *, model_factory=Model
) -> dict:
    """Run the adopted serial DFS; a deadline yields UNKNOWN, never INFEASIBLE.

    The caller selects a per-solve model explicitly. Successful probe suffixes
    are independently replayed with the full path from the original input.
    State caps exist only as test controls; the official preset has no cap.
    """
    begin = perf_counter()
    model = model_factory(level)
    deadline = begin + seconds
    if model.turns == 0:
        return {
            "status": "INFEASIBLE",
            "reason": "no_claim_turn",
            "expanded": 0,
            "plan": None,
            "search_seconds": perf_counter() - begin,
        }
    parameters = road_parameters(model)
    metrics = {
        "bound_prunes": 0,
        "no_income_waits_removed": 0,
        "duplicate_attempts": 0,
        "ordered_states": 0,
    }
    metrics.update(
        probe_calls=0, probe_steps=0, probe_invalid=0, probe_seconds=0.0, probe_events=[]
    )
    initial = model.initial()
    if perf_counter() < deadline and model.road_bound(initial, parameters) < model.goal:
        return {
            "status": "INFEASIBLE",
            "reason": "road_bound",
            "expanded": 0,
            "reached": 1,
            **metrics,
            "plan": None,
            "search_seconds": perf_counter() - begin,
        }
    if initial.cash < model.goal and perf_counter() < deadline:
        steps = one_quarry_completion(model, initial, True)
        if steps is not None:
            return {
                "status": "FEASIBLE",
                "reason": "one_quarry_completion",
                "expanded": 0,
                "reached": 1,
                **metrics,
                "plan": model.plan(steps),
                "search_seconds": perf_counter() - begin,
            }
    parents = {initial: None}
    expanded = 0
    inserts = 1
    stack = [(initial, None)]
    goal = None
    reason = "exhausted"
    completion_waits = 0
    # One deterministic allowance across all calls, not reset by a new origin.
    # A trial includes rejected children; scoring/actions remain bounded too.
    probe_work_limit = 512
    while stack:
        if perf_counter() >= deadline:
            reason = "time_limit"
            break
        if len(parents) >= max_states:
            reason = "state_limit"
            break
        s, iterator = stack[-1]
        if iterator is not None:
            try:
                cell = next(iterator)
            except StopIteration:
                stack.pop()
                continue
            child = model.step(s, cell)
            if child not in parents:
                parents[child] = (s, cell)
                stack.append((child, None))
                inserts += 1
            else:
                metrics["duplicate_attempts"] += 1
            continue
        expanded += 1
        if s.cash >= model.goal:
            goal = s
            break
        income = base_income(model, s)
        if income and s.cash + income * (model.turns - s.turn) >= model.goal:
            completion_waits = (model.goal - s.cash + income - 1) // income
            goal = s
            break
        upper = model.road_bound(s, parameters)
        if upper < model.goal:
            metrics["bound_prunes"] += 1
            stack.pop()
            continue
        if (
            metrics["probe_calls"] < 4
            and (expanded == 1 or expanded % 64 == 0)
            and metrics["probe_steps"] < probe_work_limit
        ):
            probe_start = perf_counter()
            event = {"origin_expanded": expanded, "origin_turn": s.turn}
            suffix, work = greedy_probe(
                model,
                s,
                parameters,
                deadline,
                max_work=probe_work_limit - metrics["probe_steps"],
                diagnostics=event,
            )
            metrics["probe_calls"] += 1
            metrics["probe_steps"] += work
            proposed = None
            if suffix is not None and perf_counter() < deadline:
                # Model construction is not a legality oracle. Verify the FULL
                # original-input plan, including prefix, through strict replay.
                from .reference import validate_plan

                try:
                    proposed = model.plan(prefix_steps(parents, s) + suffix)
                    validate_plan(level, proposed)
                except (ValueError, IndexError, KeyError, TypeError):
                    proposed = None
                    metrics["probe_invalid"] += 1
                    event["verification"] = "invalid_plan"
            probe_end = perf_counter()
            event.setdefault(
                "verification",
                "valid"
                if proposed is not None
                else "deadline_before_replay"
                if suffix is not None
                else "no_plan",
            )
            event["acceptance"] = (
                "accepted"
                if proposed is not None and probe_end < deadline
                else "deadline_after_replay"
                if proposed is not None
                else "invalid_plan"
                if event["verification"] == "invalid_plan"
                else "deadline_before_replay"
                if suffix is not None
                else "deadline_during_probe"
                if event.get("termination") == "global_deadline"
                else "no_candidate"
            )
            event["deadline_remaining_seconds"] = deadline - probe_end
            event["elapsed_seconds"] = probe_end - probe_start
            metrics["probe_events"].append(event)
            metrics["probe_seconds"] += event["elapsed_seconds"]
            if event["acceptance"] == "accepted":
                return {
                    "status": "FEASIBLE",
                    "reason": "greedy_probe",
                    "expanded": expanded,
                    "reached": len(parents),
                    "insertions": inserts,
                    **metrics,
                    "plan": proposed,
                    "search_seconds": perf_counter() - begin,
                }
            if probe_end >= deadline:
                reason = "time_limit"
                break
        choices = model.choices(s)
        if not income and None in choices:
            choices.remove(None)
            metrics["no_income_waits_removed"] += 1
        choices = productive_choices(model, s, choices, True)
        metrics["ordered_states"] += 1
        stack[-1] = (s, iter(choices))
    steps = None
    if goal is not None:
        steps = prefix_steps(parents, goal)
        steps.extend([None] * completion_waits)
    status = (
        "FEASIBLE" if steps is not None else ("INFEASIBLE" if reason == "exhausted" else "UNKNOWN")
    )
    return {
        "status": status,
        "reason": ("wait_completion" if completion_waits else "goal")
        if steps is not None
        else reason,
        "expanded": expanded,
        "reached": len(parents),
        "insertions": inserts,
        **metrics,
        "plan": model.plan(steps) if steps is not None else None,
        "search_seconds": perf_counter() - begin,
    }
