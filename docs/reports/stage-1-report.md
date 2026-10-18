# Stage 1 delivery report

Stage 1 is complete: all 17 levels counted toward advancement. Across 19 tasks,
all 19 submitted plans passed the game on their only submission; two missed the
30-second submission window after creation and required fresh qualifying tasks. No unfinished Stage 1
tasks remain. This is an interim client evaluation of Stage 1; the combined
report will be reconciled after all stages are completed.

## Delivered behavior

Roads cost 1 stone. Stone quarries cost 10 stone and mine up to 5 stone per turn.
Resources must be transferred back to BASE before they can fund construction
or satisfy the goal.

The Python solver reads each task's map, initial inventory, goal and turn limit,
then returns an ordered JSON action plan. It first tries a simple plan using one quarry. If that fails, it tries a short
greedy search, then searches remaining choices while skipping branches whose
optimistic result cannot meet the goal.
Independent replay checks the original input before the runner submits once and
verifies the task flags and series progress. Ten of the 17 counted tasks used the
single-quarry shortcut, six finished through search / waiting, and one through
the greedy probe.

```mermaid
flowchart LR
    A[Read task input] --> B[Generate a winning plan]
    B --> C[Replay and validate]
    C --> D[Submit once]
    D --> E[Verify task and progress]
    E --> F[Continue after a counted pass]
```

The reusable runner saves inputs / plans / receipts, stops on failed or uncertain
advancement, and never retries an ambiguous POST. Creation reads now allow 10 s;
other request phases retain 3 s. A 26 s local submission guard reduces solver time
as earlier work consumes the budget. These are cooperative limits rather than
a universal wall-time guarantee.

## Measured results

| Measure | Observed result |
| --- | --- |
| Level completion | 17/17 counted; 100% |
| Game-plan passes | 19/19; 100%, one submission per task |
| Tasks counting toward progression | 17/19; 89.5%; two workflow timing failures |
| Counted server time | Median 1.481 s; mean 1.691 s; range 1.318–2.815 s |
| Counted solver time | Median 0.648 ms; maximum 14.181 ms; total 55.882 ms |
| All 19 solver runs | Total 73.433 ms; maximum 17.375 ms |
| Counted client runs | Sum 64.696 s; median 3.564 s; range 2.604–5.438 s |
| Validation | 81 local tests passed; all 19 saved plans independently replayed |

Summed client windows are not project elapsed time. Server and client clocks
cover different portions of a run; their difference is not a measurement of
network overhead. Overall throughput / development time and a pure server
processing duration were not measured.

The live inputs cover widths / heights up to 25, a largest map of 600 cells
(25×24), 1–23 stone sites, 12–19 starting stone, goals of 15–300 stone and 4–14
allowed turns. Larger maps were not necessarily harder: some still needed only
one quarry. These are observations from the generated tasks, not a proof for
all seeds or a minimum-turn optimizer.

## Every task input and timing

Amounts are stone at BASE. Map dimensions are width × height.

| Level | Map | Stone sites | Starting → goal | Turns used / limit | Solver ms | Server s | Client s | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 2×2 | 1 | 12 → 15 | 3 / 4 | 0.18 | 48.676 | — | Late |
| 1 | 2×2 | 1 | 12 → 15 | 3 / 4 | 0.18 | 1.318 | 2.604 | Counted |
| 2 | 5×6 | 2 | 15 → 20 | 4 / 5 | 0.22 | 1.430 | 2.827 | Counted |
| 3 | 10×6 | 2 | 17 → 27 | 6 / 6 | 0.28 | 1.405 | 2.965 | Counted |
| 4 | 12×9 | 8 | 15 → 100 | 9 / 9 | 3.89 | 2.304 | 3.877 | Counted |
| 5 | 12×11 | 10 | 15 → 25 | 5 / 6 | 0.32 | 1.411 | 3.741 | Counted |
| 6 | 21×14 | 4 | 15 → 33 | 6 / 7 | 0.41 | 1.393 | 3.275 | Counted |
| 7 | 22×15 | 14 | 16 → 258 | 14 / 14 | 12.73 | 1.495 | 3.658 | Counted |
| 8 | 21×17 | 16 | 15 → 25 | 5 / 6 | 0.49 | 1.481 | 3.564 | Counted |
| 9 | 14×14 | 5 | 12 → 75 | 9 / 9 | 3.74 | 1.789 | 3.340 | Counted |
| 10 | 23×24 | 5 | 18 → 53 | 11 / 11 | 0.64 | 2.815 | 5.304 | Counted |
| 11 | 10×10 | 9 | 12 → 135 | 9 / 9 | 2.18 | 1.919 | 4.339 | Counted |
| 12 | 23×25 | 5 | 15 → 36 | 7 / 10 | 0.63 | 2.445 | 5.386 | Counted |
| 13 | 23×24 | 22 | 15 → 300 | 14 / 14 | 17.38 | 743.974 | — | Late |
| 13 | 23×23 | 22 | 15 → 300 | 13 / 13 | 14.18 | 1.608 | 5.438 | Counted |
| 14 | 17×17 | 8 | 12 → 120 | 11 / 11 | 8.02 | 1.464 | 2.936 | Counted |
| 15 | 25×23 | 6 | 19 → 29 | 6 / 9 | 0.65 | 1.481 | 3.514 | Counted |
| 16 | 25×24 | 23 | 17 → 27 | 6 / 6 | 0.69 | 1.449 | 4.716 | Counted |
| 17 | 15×15 | 14 | 12 → 210 | 11 / 11 | 6.63 | 1.532 | 3.213 | Counted |

- **Solver:** original in-process model / search / plan time. It excludes solver process startup, outer replay / encoding and network.
- **Server:** creation to successful submission, measured by the server; this owns the 30-second eligibility check. Late rows include human / debugging / recovery waiting, not server CPU time.
- **Client:** before task creation through task / progress verification, including solver process startup. It excludes earlier preflight checks, CLI startup and gaps between tasks. A dash means a comparable full-run duration was not recorded.

Creation-call wall time was recorded separately for fresh levels 13–17:
2.907, 0.602, 1.160, 2.402 and 0.729 s respectively. Earlier creation durations were
not separately measured. These calls were all below 3 s, so the live successes do
not establish the cause of the earlier timeout.

## Timing incidents and corrections

| Incident | Effect | Correction |
| --- | --- | --- |
| Level 1 create response did not expose a usable task ID through the supplied model. | Manual recovery passed at 48.676 s and did not count. | Identify exactly one new unsolved ID with a GET inside the original clock. |
| Level 13 creation response exceeded the 3 s client read wait. | Server had created the task; recovery passed at 743.974 s and did not count. | Allow 10 s only for creation reads; reconcile effects without repeating POSTs. |
| Late recovery exposed ready_for_gate. | Loop stopped before creating another task. | Accept that status only for the current level at series zero; retain all advancement checks. |

The solver produced valid plans in both late cases; operational handling missed
the deadline. The underlying server / network cause of the second delay remains
unknown. Fresh level 13 had a 23×23 map and 13 turn limit, compared with the old
23×24 /14 turn task; it received a newly generated plan.

## Evidence and evaluation scope

[Task metrics](../../experiments/stage1_poc/stage1-task-metrics.json) contain
machine-readable inputs and timing definitions. [Completion receipts](../../experiments/stage1_poc/stage1-completion-results.json)
retain all 19 original maps, plans, recorded solver statistics, replay summaries
and final server flags / progress. Original private receipt hashes bind the
copied solver statistics. Exact adapter source hashes are retained for the
resumed levels 13–17; earlier per-attempt adapter hashes were not recorded.
The [whiteboard](../../.github/spec-driven-delivery/solution-whiteboard.md)
retains design reasoning and the wider local PoC evidence.

Stage 1 meets the observed game progression requirement with substantial measured
time margin. Positive live cases do not prove every pruning rule, arbitrary-map
coverage, complete server-rule equivalence or general 30-second solvability. The
current solver is an experimental Stage 1 implementation; Stage 2 support is a
separate change. Keep these Stage 1 results intact and reconcile the combined
client assessment after the remaining stages are completed.
