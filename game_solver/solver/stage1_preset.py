"""Adopted Stage1 preset: one-topology connectivity reuse plus capital DP.

Every solve owns its cache and threshold table. No monkeypatching, shared mutable
configuration, benchmark imports or networking is needed.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

from .capital import investment_thresholds
from .stage1 import Model, ParentTree, RoadParameters, State, road_investment_upper, solve as search
from .reference import _read_level

if TYPE_CHECKING:
    from .stage1 import StateView


class InvestmentModel(Model):
    """Cache topology only; inventory/turn changes cannot change connectivity."""

    def __init__(self, level: dict[str, Any]) -> None:
        """Start a solve-owned one-topology cache with no cross-task state."""
        super().__init__(level)
        self._last_key: tuple[int, int] | None
        self._last_tree: ParentTree | None
        self._investment_thresholds: tuple[tuple[int, ...], ...]
        self._last_key = self._last_tree = None

    def tree(self, state: StateView) -> ParentTree:
        """Reuse connectivity only while both topology masks are unchanged."""
        key = (state.roads, state.quarries)
        if key != self._last_key:
            self._last_key = key
            self._last_tree = MappingProxyType(super().tree(state))
        return cast(ParentTree, self._last_tree)

    def road_bound(self, state: State, parameters: RoadParameters) -> int:
        """Reject only when the free-access capital relaxation cannot afford a win."""
        upper = road_investment_upper(self, state, parameters)
        if upper < self.goal:
            return upper
        wealth = state.cash + sum(state.stocks)
        if wealth >= self.goal:
            return upper
        table = cast(
            tuple[tuple[int, ...], ...] | None, getattr(self, "_investment_thresholds", None)
        )
        if table is None:
            table = investment_thresholds(self.goal, self.k, self.turns)
            self._investment_thresholds = table
        required = table[self.turns - state.turn][state.quarries.bit_count()]
        # Relaxed failure proves impossibility. Passing is only inconclusive.
        return self.goal - 1 if wealth < required else upper


def solve(
    level: dict[str, Any], seconds: float = 24.0, max_states: float = float("inf")
) -> dict[str, Any]:
    """Return the selected Stage1 verdict and optional JSON plan; no state cap."""
    _read_level(level)
    result = search(level, seconds, max_states, model_factory=InvestmentModel)
    if result["reason"] == "road_bound":
        result["reason"] = "combined_bound"
    return result
