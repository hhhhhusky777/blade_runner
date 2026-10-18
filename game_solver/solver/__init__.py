"""Pure offline logistics solver; imports leave networking and environment untouched."""

from .api import solve, validate_plan

__all__ = ["solve", "validate_plan"]
