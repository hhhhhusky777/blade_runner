"""Optional project ordering using the existing typed investment relaxation.

CapitalDP.required is a proven optimistic funding threshold: all held stocks
are spendable and future roads are free. Here we also charge one project's
current route and estimate the waits needed to pay for it from BASE. Those
project-specific scores are guidance, not admissible bounds: alternative builds
may share roads or make a chosen route cheaper. Nothing here rejects a state
or removes a legal choice. The caller owns probe limits and witness replay.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import inf
from time import perf_counter
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .stage2 import CapitalDP, Cell, Model, State

from .stage1 import route_cells


class GuidanceCounters(TypedDict):
    """Per-solve work counters for evaluating the optional ordering heuristic."""

    calls: int
    projects: int
    dp_queries: int
    waits_promoted: int
    deadline_fallbacks: int
    weakened_dp_fallbacks: int
    seconds: float


class ResourceGuidance:
    """Promote one economically promising project in a stable choice permutation.

    ``choices`` is the caller's existing fallback order. Each call computes two
    resource-compatible route maps, retaining currently unaffordable targets.
    The existing per-solve CapitalDP owns all threshold caching. No extra state
    cache, dependency, model, pruning rule or search limit is introduced.
    """

    def __init__(self, model: Model, dp: CapitalDP, deadline: float = inf) -> None:
        """Reuse the exact model and its per-solve relaxed funding cache."""
        self.model, self.dp, self.deadline = model, dp, deadline
        self.metrics: GuidanceCounters = dict(
            calls=0,
            projects=0,
            dp_queries=0,
            waits_promoted=0,
            deadline_fallbacks=0,
            weakened_dp_fallbacks=0,
            seconds=0.0,
        )

    def ordered(self, state: State, choices: Iterable[Cell]) -> list[Cell]:
        """Return every input choice once, promoting a route prefix or END.

        For each project, wait until its current full cost is fundable from
        connected STONE income, charge that cost, and credit its immediate
        extraction. Existing native stocks and future production are granted
        immediate access for the subsequent DP estimate. Binary search finds
        the first feasible horizon because exact DP thresholds cannot increase
        when more ENDs are allowed. If DP has weakened any value on its budget
        or deadline, keep the original order rather than assume monotonicity.
        """
        begin = perf_counter()
        self.metrics["calls"] += 1
        choices = list(choices)
        try:
            if self._expired():
                return choices
            if self.dp.skipped:
                self.metrics["weakened_dp_fallbacks"] += 1
                return choices
            model = self.model
            remaining = model.turns - state.turn
            total, built = model.totals(state)
            stone_income = model.income(state)[0]
            paths = {resource: model.routes(state, resource) for resource in (0, 1)}
            occupied = model.occupied(state)
            candidates = []
            for i, target in enumerate(model.nodes):
                if self._expired():
                    return choices
                resource = model.resources[i]
                distance, parents = paths[resource]
                existing = bool(state.quarries >> target & 1)
                if target not in distance or (existing and not state.stocks[i]):
                    continue
                cost = distance[target] + (0 if existing else model.costs[i])
                shortfall = max(0, cost - state.cash)
                if shortfall and (not stone_income or None not in choices):
                    continue
                waits = (shortfall + stone_income - 1) // stone_income if shortfall else 0
                if waits > remaining:
                    continue
                path = route_cells(parents, target)
                first = next((p for p in path if not occupied >> p & 1), None)
                hint = None if waits else first
                if (not waits and first is None) or hint not in choices:
                    continue
                # Current-turn production is already credited in state; ENDs
                # add output only from existing extractors. New extraction is
                # credited once, after the delayed project's construction.
                wealth = [total[r] + 5 * built[r] * waits for r in (0, 1)]
                counts = list(built)
                wealth[0] -= cost
                if not existing:
                    wealth[resource] += 5
                    counts[resource] += 1
                missing = (max(0, model.goals[1] - wealth[1]) + 4) // 5
                self.metrics["projects"] += 1
                horizon, slack = self._horizon(remaining - waits, counts, missing, wealth[0])
                if self._expired():
                    return choices
                if self.dp.skipped:
                    self.metrics["weakened_dp_fallbacks"] += 1
                    return choices
                if horizon is not None:
                    # Restore already-produced stranded stock first on equal
                    # economic predictions, then prefer greater funding slack.
                    # _horizon returns either two numbers or two None sentinels.
                    score = (waits + horizon, not existing, -slack, waits, cost, target)  # type: ignore[operator]
                    candidates.append((score, hint))
            if not candidates:
                return choices
            _, hint = min(candidates, key=lambda entry: entry[0])
            if hint is None:
                self.metrics["waits_promoted"] += 1
            return [hint] + [cell for cell in choices if cell != hint]
        finally:
            self.metrics["seconds"] += perf_counter() - begin

    def _expired(self) -> bool:
        """Count a deadline fallback without making an impossibility claim."""
        if perf_counter() >= self.deadline:
            self.metrics["deadline_fallbacks"] += 1
            return True
        return False

    def _horizon(
        self, remaining: int, counts: Sequence[int], missing: int, wealth: int
    ) -> tuple[int, float] | tuple[None, None]:
        """First feasible exact relaxed horizon, or no finite prediction."""

        def required(d: int) -> float:
            """Query relaxed funding for this horizon and account for the work."""
            self.metrics["dp_queries"] += 1
            # counts always contains exactly the STONE and ORE producer counts.
            return self.dp.required(d, *counts, missing)  # type: ignore[call-arg]

        required_last = required(remaining)
        if self.dp.skipped or wealth < required_last:
            return None, None
        low, high = 0, remaining
        while low < high:
            if self._expired():
                return None, None
            middle = (low + high) // 2
            threshold = required(middle)
            if self.dp.skipped:
                return None, None
            if wealth >= threshold:
                high = middle
            else:
                low = middle + 1
        threshold = required(low)
        return low, wealth - threshold
