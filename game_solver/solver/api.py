"""Public offline boundary: one application dispatches to the three stage engines."""

from . import stage1_preset, stage2, stage3
from .reference import validate_plan as validate_stone
from .stage2_reference import validate_plan as validate_ore
from .stage3_reference import validate_plan as validate_iron


def validate_plan(level: dict, plan: list[list[dict]], stage: int = 1) -> dict:
    """Strict raw-action replay on the original task; raise ValueError if illegal."""
    if stage == 1:
        return validate_stone(level, plan)
    if stage == 2:
        return validate_ore(level, plan, relay_mode="matching")
    if stage == 3:
        return validate_iron(level, plan, relay_mode="matching")
    raise ValueError("only Stage1, Stage2 and Stage3 are supported")


def solve(level: dict, stage: int = 1, seconds: float = 24.0) -> dict:
    """Generate an action plan using the adopted preset, without network access.

    FEASIBLE includes an independently replayed plan; INFEASIBLE is conditional
    model exhaustion or a safe bound; UNKNOWN means the budget was insufficient.
    No stage uses a search-state cap. The caller owns request-to-submit timing.
    """
    if stage == 1:
        result = stage1_preset.solve(level, seconds)
        if result["plan"] is not None:
            validate_stone(level, result["plan"])
        return result
    if stage == 2:
        return stage2.solve(
            level, seconds=seconds, relay_mode="matching", guidance="both", max_states=None
        )
    if stage == 3:
        return stage3.solve(level, seconds=seconds)
    raise ValueError("only Stage1, Stage2 and Stage3 are supported")
