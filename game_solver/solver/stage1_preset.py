"""Adopted Stage1 preset: one-topology connectivity reuse plus capital DP.

Every solve owns its cache and threshold table. No monkeypatching, shared mutable
configuration, benchmark imports or networking is needed.
"""

from types import MappingProxyType

from .capital import investment_thresholds
from .stage1 import Model, road_investment_upper, solve as search
from .reference import _read_level


class InvestmentModel(Model):
    """Cache topology only; inventory/turn changes cannot change connectivity."""

    def __init__(self, level):
        super().__init__(level)
        self._last_key = self._last_tree = None

    def tree(self, state):
        key = (state.roads, state.quarries)
        if key != self._last_key:
            self._last_key = key
            self._last_tree = MappingProxyType(super().tree(state))
        return self._last_tree

    def road_bound(self, state, parameters):
        upper = road_investment_upper(self, state, parameters)
        if upper < self.goal:
            return upper
        wealth = state.cash + sum(state.stocks)
        if wealth >= self.goal:
            return upper
        table = getattr(self, "_investment_thresholds", None)
        if table is None:
            table = investment_thresholds(self.goal, self.k, self.turns)
            self._investment_thresholds = table
        required = table[self.turns - state.turn][state.quarries.bit_count()]
        # Relaxed failure proves impossibility. Passing is only inconclusive.
        return self.goal - 1 if wealth < required else upper


def solve(level: dict, seconds: float = 24.0, max_states=float("inf")) -> dict:
    """Return the selected Stage1 verdict and optional JSON plan; no state cap."""
    _read_level(level)
    result = search(level, seconds, max_states, model_factory=InvestmentModel)
    if result["reason"] == "road_bound":
        result["reason"] = "combined_bound"
    return result
