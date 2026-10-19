"""Optimistic investment thresholds shared by the stage engines.

F[d][q] is minimum spendable wealth needed with d future income collections
and q existing quarries. Roads/access are free in this relaxation, so failure
can reject a real state; success does not prove a real solution exists.
"""


from __future__ import annotations


def investment_thresholds(goal: int, sites: int, turns: int) -> tuple[tuple[int, ...], ...]:
    """F[d,q]: cash needed in the free-road, immediate-access relaxation.

    Existing quarries have already mined this turn. BUILD costs 10 stone and immediately returns 5;
    END returns 5*q stone. Rows cover d=0..turns-1. See whiteboard's exact derivation.
    """
    rows = [(goal,) * (sites + 1)]
    for _ in range(1, turns):
        previous = rows[-1]
        row = [goal] * (sites + 1)
        for q in range(sites, -1, -1):
            required = min(goal, max(0, previous[q] - 5 * q))
            if q < sites:
                required = min(required, max(10, row[q + 1] + 5))
            row[q] = required
        rows.append(tuple(row))
    return tuple(rows)
