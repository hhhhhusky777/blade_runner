# Blade Runner recruitment solver

One Python 3.13 application solves all three stages of a deterministic logistics
game. It generates an ordered JSON action plan; the server receives the answer,
not Python code. The adopted solver completed 31 levels and 81 required series
positions: 93 submitted plans passed, 88 on time and five late.

**Delivery candidate:** official code and portable regressions are implemented;
final corpus/ZIP validation is pending. Historical game results refer to the
research versions that actually ran, not a new server run of the packaged code.

Start with the [recruiter report](docs/reports/recruitment-delivery-report.md) for
the problem, conditional proofs, measured progression, all three stage chapters,
work-time accounting and remaining issues. The
[concluded whiteboard](.github/spec-driven-delivery/solution-whiteboard.md#final-adopted-solution)
contains the detailed adopted design and retained research history.

## Review the code

The solver tries validated shortcuts, then memoized DFS. Whole production
projects order choices. Optimistic bounds and DP reject proven dead branches;
failed greedy probes never reject a state. Time exhaustion returns UNKNOWN.

| Responsibility | Read first |
| --- | --- |
| Public solve/replay contract | [api.py](game_solver/solver/api.py) |
| Stage 1 geometry, search, selected cache and DP | [stage1.py](game_solver/solver/stage1.py), [stage1_preset.py](game_solver/solver/stage1_preset.py), [capital.py](game_solver/solver/capital.py) |
| Stage 2 typed resources and additional probes | [stage2.py](game_solver/solver/stage2.py), [resource_guidance.py](game_solver/solver/resource_guidance.py) |
| Stage 3 manufacturing, project ordering and on-demand DP | [stage3.py](game_solver/solver/stage3.py) |
| Independent raw-action legality | [reference.py](game_solver/solver/reference.py), [stage2_reference.py](game_solver/solver/stage2_reference.py), [stage3_reference.py](game_solver/solver/stage3_reference.py) |
| Single submission, recovery and verified progression | [runner.py](game_solver/solver/runner.py), [child.py](game_solver/solver/child.py) |
| Regressions and old/new comparison | [tests](game_solver/tests), [run_regressions.py](game_solver/tests/run_regressions.py) |

Stage 3's adopted probe settings are 512 initial decisions per policy, 512 DFS-state
interval and 32 later decisions per policy. These limit optional rollouts, not the
full search. Earlier stage presets retain their own measured settings.

## What you are building

Your program reads a map, starting resources, goal, and turn limit, then generates a plan to build, mine, deliver resources, and claim victory. Like LeetCode, tasks test a general solution. Here, your code runs locally and you submit its **action plan**, rather than code for the server to execute.

| Term | Meaning |
| --- | --- |
| Stage | One of three groups of levels; later stages add capabilities. |
| Level | A step in the fixed progression. Stage 1 has 17 levels. |
| Series | Tasks required to complete a level; they may have different types. |
| Task | One input: map, starting resources, goal, and turn limit. |
| Plan | A JSON list of turns, each containing ordered actions. |
| Capabilities | Available resources, terrain, structures, actions, costs, and restrictions. |

Finish every level to unlock the next stage. After Stage 3, the organizers email information about next steps.

## Timing and progression

There are **two separate limits**:

- **Game turns:** achieve `level_goal` within `max_turns`. Each task starts with one `BASE`, no other structures, and a goal requiring an amount of one resource at that base.
- **30 seconds:** each task in a series must succeed on its **first submission within 30 seconds of creation** to count toward advancement.

Creating a task starts the clock. Viewing stages, listing existing tasks, or fetching an existing task does not create one or restart its clock. Only one unfinished task is allowed at a time.

If you fail or miss the deadline, you must still finish that task with a correct submission. The current level's series resets; the next request starts the series again. Completed levels stay completed. Reuse your solver, but do not assume new tasks have identical maps.

```text
Required series: A passes → B passes → C passes → level complete
If C fails:     finish C → restart at A → pass the whole series again
```

**You do not write the solver in 30 seconds.** Develop and test on local examples or known tasks beforehand. A fresh task's exact input is revealed after creation. If it exposes a missing strategy, take time to debug, finish it, and retry the series with improved code.

```mermaid
flowchart TD
    A[Develop and test solver] --> B[Request task: clock starts]
    B --> C[Read input, generate plan, simulate]
    C --> D[Submit within 30 seconds]
    D --> E{First attempt succeeds on time?}
    E -->|Yes| F[Counts toward series]
    E -->|No| G[Debug, finish active task, restart series]
    F --> H[Continue to next task or level]
    H --> B
    G --> A
```

## Stage 1 rules

| Structure | Cost | Purpose |
| --- | --- | --- |
| `BASE` | Already present | Stores resources; its inventory pays for construction. |
| `ROAD` | 1 stone | Carries transfers between storage structures. |
| `STONE_QUARRY` | 10 stone | Stores output; mines up to 5 stone per turn on a stone node. |

Capability **interfaces** describe abilities: `Buildable` permits construction; `Storage` holds resources; `Transport` forms routes; `Extraction` permits mining; `BaseOnly` makes inventory spendable for building. Action fields specify required inputs and types.

| Action | Inputs | Rule |
| --- | --- | --- |
| `BUILD` | `x`, `y`, `type` | Pay from base; build adjacent to an existing structure. |
| `MINE` | `x`, `y` | Mine each extractor at most once per turn; output stays there. |
| `TRANSFER` | `path`, `resource`, `amount` | Positive amount; storage endpoints, transport-only intermediate tiles, at least three coordinates. |
| `CLAIM_WIN` | `x`, `y` | Claim at the base after its inventory meets the goal. |

Extractors must match the node's `resource_allow`; other structures cannot occupy resource nodes. Transfers require a connected route. Mining income must reach the base before it can fund construction.

A turn can contain many actions **executed in order**; each sees earlier results. Actions may repeat unless restricted. Storage is unbounded. Every submission starts from the original task state: previous submissions leave no buildings or resources behind.

Maps are at most 25×25 with at most 24 resource nodes. `PLANNED_ROAD` tiles suggest routes; they are not built roads. Alternative routes are allowed. Building everything can waste resources and turns; practical heuristics usually suffice. Turn limits are usually single or low double digits.

### A three-turn example

Assume a base with 11 stone, a stone node two tiles away, and a goal of 15 stone within three turns. This is an illustration, not a fetched task.

```text
[BASE (0,0)] — [build ROAD (1,0)] — [build QUARRY on stone (2,0)]
```

| Turn | Ordered actions | Base stone afterward |
| --- | --- | --- |
| 1 | Build road (−1), build quarry (−10), mine 5, transfer 5. | 5 |
| 2 | Mine 5, transfer 5. | 10 |
| 3 | Mine 5, transfer 5, `CLAIM_WIN` at `(0,0)`. | 15 |

All transfers use `[(2,0), (1,0), (0,0)]`. Four actions in turn 1 still use only one game turn.

## Setup and commands

Install [uv](https://docs.astral.sh/uv/) and Python 3.13. From the project root:

```bash
cd game_solver
uv sync --frozen
```

No credentials are needed for offline work. From the project root, run a fixed
sample through the real isolated child and strict replay:

```bash
./submit.sh --stage 3 --offline-smoke
```

To solve a task JSON locally or import the API:

```bash
cd game_solver
uv run --frozen python -m solver --stage 3 task.json > answer.json
uv run --frozen python -m unittest discover -s tests -t .
uv run --frozen python -m tests.run_regressions --suite all --output regression-results.json
```

```python
from solver import solve
result = solve(level, stage=3, seconds=24.0)
# result["plan"] is present only for a validated FEASIBLE answer.
```

The full portable corpus has 93 task records / 92 distinct inputs, plus 108 Stage 1,
150 Stage 2 and 307 Stage 3 control configurations. Those include impossible cases,
relay-premise differences and forced-search controls. Tests carry truth/witnesses;
the runtime solver receives only the task and its budget.

### Explicit live commands

Copy `game_solver/.env.example` to `game_solver/.env` and configure privately:

```dotenv
GAME_SERVER_BASE_URL=https://bladerunner.reef.pl/
GAME_SERVER_TOKEN=<your token from the game webpage>
```

Install dependencies before timed attempts. From the project root:

```bash
./submit.sh --stage 3 --check             # GET-only readiness check
./submit.sh --stage 3 --verify TASK_ID    # GET-only result verification
./submit.sh --stage 3 --submit-one        # create/solve/submit one fresh task
./submit.sh --stage 3 --loop              # recover pending task, then verified loop
```

Choose stage 1, 2 or 3 explicitly; the loop never enters another stage. Use one loop
at a time. Startup recovery keeps the pending task's original clock, submits at
most one validated answer, verifies the resulting series/reset, then continues.
New failure, lateness, ambiguous credit or inconsistent progression stops it.
Creation retries/reconciliation are bounded; submissions are never retried.
A completed stage makes no writes. Private temporary receipts retain original
inputs, plans, timing and GET verification. An accepted POST alone proves no credit.

## Later-stage rules

| Stage | Added structure | Cost | Output |
| --- | --- | --- | --- |
| 2 | IRON_MINE on ore | 15 STONE | 5 IRON_ORE per turn |
| 3 | SMELTER on ordinary terrain | 20 STONE | Up to 2 IRON_ORE converted to IRON per turn |

Stone pays for construction in every stage and can itself be a goal. Ore can be
a goal or manufacturing input; iron is produced by smelters. Typed storage,
ordered transfers and partial production matter when goals compete for resources.
The solver reuses earlier engines when the existing projection proof applies.

## Code limits and delivery

The proofs assume the documented local model: cardinal adjacency, renewable
exact-five extraction, unlimited storage, ordered free legal transfers and
BASE-funded construction. Independent raw replay checks plans; neither local
replay nor observed server acceptance proves every unseen contract variant.
Finite search is complete without limits, but worst-case time/space are
exponential. No minimum-turn optimum or universal 30-second guarantee is claimed.

The original starter simulator is permissive and remains separate; it is not the
legality oracle. The official runtime imports no research/benchmark modules and
changes no sockets/environment on import. Only the explicit offline child denies
networking. Original research sources, receipts and prior reports stay preserved
in the owner-held workspace; they are not required to run the release.

The local source ZIP contains the official application, tests/fixtures, reports,
graphs, concluded design, compact evidence and checksums. It excludes credentials,
Git data, virtual environments, caches, raw conversation and bulk research. The
three exported historical chapters identify original source hashes and portable
evidence locations; some historical whiteboard links refer to the unbundled lab.
Nothing is published, emailed or merged by building the package.
