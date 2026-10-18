# Implementation Plan — Recruitment solver delivery

<!-- sdd: implementation-plan -->

This file owns execution state. The concluded whiteboard owns design; the recruiter
report is an implementation deliverable, not a prerequisite for concluding design.

## Delivery status

| Field | Value |
| --- | --- |
| State | `IMPLEMENTING` — plan accepted by the owner on 2026-10-18 |
| Active tasks | `T03` |
| Next ready task | `T04` after T03 review |
| Active blocker | `None` |
| Implementation mode | Human review before merge; Autopilot is not enabled |
| Delivery branch | `codex/stage1-solver-design` in the existing managed worktree |
| Integration model / required PR target | One final review unit; prospective single PR to `main`; no intermediate task PRs |
| Implementation baseline | `52e793ce1f71dd09f2013c7b020eebbd6a5ad06c` plus preserved, source-bound research inputs |
| Accepted design | [Whiteboard C1](solution-whiteboard.md), concluded in `c9589dfb115341abe40552ffc845213db03cccc8` |
| Candidate and freeze | Reviewed candidate `cb929ff0a5ca0569069920890b181b469487ab64`; both retained reviewers approved the exact state-only freeze |
| Required reviewers | Retained conclusion reviewers A and B through task, audit and final review |
| Owner | Project owner; C1 explicitly accepted on 2026-10-18 |
| Publication / merge authority | None. Prepare a local package; no push, remote PR creation, email, game requests or merge |

No branch-protection policy is inferred. The manifest records no additional
project branch policy. If remote delivery is later authorized, every task remains
on the named branch and the single PR targets `main`; changing that model requires
reconciliation before publication. Autopilot would authorize no intermediate
merges in this single-PR model and never authorizes a `main` merge.

## Governing inputs and boundaries

Follow the [manifest](project-adoption-manifest.md), accepted C1 and its explicitly
consumed contracts. Preserve all pre-existing dirty files, the research tree,
original runner/script and historical source hashes. Stage1/2/3 algorithms and
adopted settings stay unchanged. Contract-equivalent organization, naming,
formatting and dependency injection are implementation choices.

The official application uses Python3.13, the starter client/models and existing
dependencies. Its solver must import without modifying sockets/environment or
loading `experiments/`. Network blocking belongs only to the explicit solver child.
The original research path remains available for differential comparison, but is
not a release dependency. No new planner framework or tuning experiment is needed.

The supported rules and proof conditions remain C1-05: matching typed relays,
cardinal adjacency, renewable exact-five extraction, BASE-funded builds, ordered
transfers and unlimited storage. A timeout stays UNKNOWN. Local validation cannot
establish universal server equivalence or a universal30-second guarantee.

## Tasks and review boundaries

Every row uses branch `codex/stage1-solver-design`, prospective final PR target
`main`, current PR `None`. Tasks are review boundaries within one delivery;
no task is merged separately. Before marking a task DONE, run its focused checks
and obtain both retained reviews. Stop and consult the owner if a task reaches
90minutes of active implementation before that boundary; tools/tests/review waits
are not active implementation time.

| ID | State / dependencies | Observable outcome and owned scope | Focused evidence before task review |
| --- | --- | --- | --- |
| T01 | DONE / None | Pure `game_solver/solver/` foundation: Stage1 geometry/search, selected last-topology cache and investment DP, independent raw validators. Remove benchmark imports and temporary global configuration from the official path; keep Stage1 probe/bound semantics. | Stage1 fixed inputs and tiny raw-oracle/bound checks; selected-preset differential plans/work; import leaves sockets/environment unchanged. |
| T02 | DONE / T01 | Package Stage2 typed search/guidance and Stage3 production/project ordering/on-demand DP. Preserve original-input replay, delegation preconditions and512/512/32 defaults. Add public solve boundary and readable state/function contracts; no algorithm changes. | Stage2/3 partial-production, impossible-bound, forced-DFS and projection controls; focused old/new outcome/plan comparisons. |
| T03 | IN_REVIEW / T02 | Official runner and `submit.sh`, fixed packaged smoke example, portable corpus and task-to-input inventory. Add all93task records, including18fresh Stage3 maps, preserve92distinct inputs and stopped observations. Preserve the existing one-submission/reconciliation/deadline/progression behavior. | Fake-client recovery, ambiguous creation and no submission retry; child network denial/token removal; strict replay in both retained relay modes; targeted saved-map solves. |
| T04 | PLANNED / T03 | Complete the recruiter report, three-stage chapters, diagrams/tables, sanitized time audit and issue links. Update review README and build an allowlisted local source ZIP with inventory/checksums. Retain historical source/timing attribution; no private conversation or credentials. | Report number/hash/link and visual checks; archive inventory and exclusion checks; preliminary clean-copy/offline CLI smoke. Final full corpus and ZIP validation remain the final gate below. |

T01 consumes the adopted `search.py`, selected `cache_benchmark.py` and
`memory_benchmark.py` helpers plus `reference.py`/typed raw validators. T02 consumes
`stage2.py`, `stage2_resource_guidance.py` and `stage3.py`. T03 consumes
`live_attempt.py`, starter client/models, saved cases/receipts and existing runner
tests. T04 consumes the factual report draft and saved comparison/time evidence.
Pin consumed files in migration evidence before altering official copies. Never
rewrite the originals merely to make a comparison pass.

## Design-to-task mapping

| Frozen design | Owning task / obligation |
| --- | --- |
| C1-01/02 normalized search, Stage1 selected preset | T01; retain all legal alternatives and success-only probes |
| C1-03/04 typed investment, manufacturing, scheduling and probe defaults | T02 |
| C1-05 conditional correctness and independent replay | T01–T03 implementation; T04 explanation; final original-input replay |
| C1-06 deadline/outcome and recovery semantics | T02 preserves search outcomes; T03 preserves runner behavior |
| C1-07/08 official package and compatibility | T01–T03; original research runner and script retained |
| C1-09 readable code | T01–T03 state/unit/proof-direction contracts and formatting; T04 review entry point |
| C1-10 retained regressions and configuration controls | T03 corpus/tests; final complete migration run |
| C1-11 comparative evidence and all-stage report | T04; distinguish historical performance from new migration checks |
| C1-12 audited time accounting | T04; refresh available ended-turn cutoff, exclude current open turn and overlapping child durations |
| C1-13 portable allowlisted package | T04; final extracted-copy verification |

## Single test inventory

These are planned evidence under the existing task/final gates, not new acceptance
checkpoints or runtime rejection behavior. Actual results remain unrun until
recorded against the exact candidate. Do not relabel an unavailable or failed
check as passed.

| Owner | Material risk / required evidence | Coverage now | Work boundary |
| --- | --- | --- | --- |
| T01 | Geometry, prefix funds, investment optimism and memoization preserve Stage1 behavior | Historical tests exist; official-package equivalents pending | Focused T01 |
| T02 | Typed stocks, manufacturing1/2 choices, DP optimism, delegation and order/probe settings preserve semantics | Historical tests exist; official-package equivalents pending | Focused T02 |
| T03 | All93task IDs remain bound to original inputs/truth;18new maps become automated solves | Saved cases/receipts exist; portable inventory and18new regressions pending | Corpus construction and focused integration; all93 differential solves final |
| T03 | Imported library has no research/socket/env side effects; child alone denies network and strips token variables | Known research-side import defect; official implementation pending | Focused T01/T03 and extracted-copy final |
| T03 | No duplicate submission after ambiguity; reset recovery and task/progression cursor are exact | Existing fake-client tests; official equivalents pending | Focused T03 |
| T03 | Keep307Stage3 historical configurations, earlier stage corpora and forced-DFS/impossible controls | Historical expected outcomes exist; portable mapping pending | Focused changed paths; full applicable isolated suite and historical controls final |
| T04 | Report counts, cohorts, repeats, timing definitions, source hashes, UNKNOWNs and regressions stay accurate | Factual draft reviewed; final migration sections pending | Focused document checks, rendered graphs and final reconciliation |
| T04 | Time means assistant-turn elapsed including waits, not human labor or CPU | Sanitized160-ended-turn audit exists; final available cutoff pending | Focused audit/ledger reconciliation |
| T04 | ZIP runs with research absent and contains no secrets/raw conversation/bulk research | Allowlist and clean-copy checks pending | Preliminary focused smoke; final archive verification |

## Final readiness and Definition of Done

1. Finish T01–T04 and both task reviews. Reconcile the actual implementation with
   C1 and this inventory. Preserve original research source hashes.
2. Author and both retained reviewers audit the exact implementation content for
   conformance, suitable reuse, unauthorized additions and redundant code before
   adding missing tests or running any final-gate test. A later implementation
   change repeats that audit; test-only additions do not invalidate it.
3. Reconcile missing tests, add required coverage, obtain final candidate reviews,
   then run full applicable validation on that exact candidate: all93task records
   under their actual-stage presets against the adopted versions, strict replay
   of returned plans on original inputs, all307Stage3 configuration controls and
   applicable earlier stage corpora. Compare deterministic plans/work where
   applicable; timing equality is not required. Preserve UNKNOWN/failure evidence.
4. Verify a clean extracted ZIP without `experiments/`: install only included
   declared dependencies, run offline sample/tests and validate file inventory,
   checksums, credentials exclusion and documented commands. No live request is
   required for this behavior-preserving migration.
5. Complete the report with actual passed/failed/unrun migration evidence and
   time cutoff; final readability/number/link/graph review. Candidate-changing
   corrections return to the same reviewers and affected checks.
6. Deliver the reviewed local package and report. Remote publication, a closing
   PR, target merge/verification and post-merge cleanup remain unauthorized and
   must not be reported complete. At an authorized normal-delivery close, create
   the combined complete whiteboard/plan archive before resetting live sources,
   following the installed workflow; preserve reusable authority and research.

## Risks, recovery and actual outcomes

| Risk | Handling / accepted limit |
| --- | --- |
| Extraction changes probe/bound behavior through hidden globals | Use explicit dependencies covering both DFS and probes; compare with source-bound originals and independent replay. Investigate a mismatch rather than weakening assertions. |
| Existing research test imports disable sockets globally | Keep runtime pure; use isolated historical test processes where necessary and explicitly test clean imports. |
| Solver deadline noise obscures migration comparison | Keep identical inputs/settings and distinguish semantic differences from elapsed-time variability. A genuine timeout remains UNKNOWN. |
| Broad testing is mistaken for exhaustive input coverage | Report tested corpora and conditional proof limits; no universal30s or full coverage claim. |
| Staging5.5GB of research or credentials accidentally | Stage explicit owned paths only; package by allowlist; inspect archive before delivery. |

Owner accepted the implementation plan on 2026-10-18. Both retained reviewers
approved plan SHA256 `7b0081f7405bbbf71e4b69bb59ac314d911632d97d27d5fc6c0689308ff3524f`.
Normal mode remains in effect; no explicit Autopilot opt-in was given. Both
retained reviewers approved T01 commit `0a89627ed7c41c4033674213f11fa9fc8d0dea2b`
with findings None. T01 is DONE; T02 is in progress; T03/T04 remain PLANNED. Focused T01 evidence: six tests passed;
24fixed-case differential solves produced identical verdicts, plans and semantic
counters (10FEASIBLE/14INFEASIBLE). The20925independent threshold comparisons
passed; consumed original source hashes are unchanged. See
[Stage1 migration evidence](../../docs/reports/evidence/migration-stage1.json).
Two test invocations used the repository root instead of the application root;
both failed at import before running tests. The working directory was corrected
and the complete focused run passed after the final documentation-only edit. Full migration
validation remains pending under T03/final. No new runtime fail-closed behavior is designed. Algorithmic
improvements remain outside this migration; existing issues retain future work.

## Human review brief

Approve this four-task local implementation plan. Recommended mode: **human
review before merge**, with automatic progression through dependency-ready local
tasks after required reviewer checks. There is one final review unit and no
intermediate PR merge, so Autopilot provides no extra merge authority. Ask the
owner whether to enable it as required by the installed skill; silence does not
enable it. The local package is the authorized deliverable; no remote action is
needed to complete its preparation.


T02 focused evidence:23tests passed, including the retained raw-action/oracle,
partial-feed, typed funding and on-demand production checks. The67matching-preset
basic cases plus38explicit unrestricted-premise configurations (105comparisons)
produced identical old/new plans, verdicts and non-time counters:66FEASIBLE and
39INFEASIBLE. Matching-preset wins replayed under both retained relay modes;
unrestricted controls replayed under their declared premise. The initial harness
applied an unrestricted fixture label to matching mode; this harness error was
corrected without changing solver behavior. Unused copied imports/local setup
were removed; the focused undefined-name/unused-import check passes. Original
source hashes remain unchanged. See [typed migration evidence](../../docs/reports/evidence/migration-typed.json).
Full93-task and307-configuration validation remains pending under T03/final.

Both retained reviewers approved T02 commit `5375367e220e9a545f3d1980d6c0917c810cdd84`
with findings None. T02 is DONE and T03 is in progress.


T03 focused evidence:88retained fake-client runner tests passed; four package
boundary tests passed, including all93saved witnesses (typed witnesses under
both modes), stage/task/input identity, explicit-child network denial, token
stripping and offline CLI input. The three official offline stage smokes passed.
The portable comparison driver passed one retained task per stage, including the
previous stopped Stage3 map, with identical old/new plans and semantic counters.
The corpus retains93records/92inputs,19/36/38stage counts,88timely flags, three
stopped observations and108/150/307local controls. See the
[portable inventory](../../docs/reports/evidence/regression-inventory.json) and
[focused runner comparison](../../docs/reports/evidence/migration-runner-focused.json).
Existing client timeout/model-recipe changes are consumed unchanged from the
pre-existing worktree, now bound in migration-sources.json. A corpus extraction
script initially expected a Stage3 counted boolean; it was corrected to the
actual Counted/Late schema before writing the corpus. Full solver validation
remains pending the final implementation audit; these focused checks did not
create server tasks or call live endpoints.
