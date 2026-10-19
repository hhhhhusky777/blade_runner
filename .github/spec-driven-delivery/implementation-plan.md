# Implementation Plan — Recruitment solver delivery

<!-- sdd: implementation-plan -->

This file owns execution state. The concluded whiteboard owns design; the recruiter
report is an implementation deliverable, not a prerequisite for concluding design.

## Delivery status

| Field | Value |
| --- | --- |
| State | `LOCAL_DELIVERY_READY` — visual report reviewed and refreshed package verified |
| Active tasks | `None` |
| Next ready task | `None` for the authorized local delivery |
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
| T03 | DONE / T02 | Official runner and `submit.sh`, fixed packaged smoke example, portable corpus and task-to-input inventory. Add all93task records, including18fresh Stage3 maps, preserve92distinct inputs and stopped observations. Preserve the existing one-submission/reconciliation/deadline/progression behavior. | Fake-client recovery, ambiguous creation and no submission retry; child network denial/token removal; strict replay in both retained relay modes; targeted saved-map solves. |
| T04 | DONE / T03 | Complete the recruiter report, three-stage chapters, diagrams/tables, sanitized time audit and issue links. Update review README and build an allowlisted local source ZIP with inventory/checksums. Retain historical source/timing attribution; no private conversation or credentials. | Report number/hash/link and visual checks; archive inventory and exclusion checks; preliminary clean-copy/offline CLI smoke. Final full corpus and ZIP validation remain the final gate below. |

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

## Task-boundary evidence (historical snapshots)

Owner accepted the implementation plan on 2026-10-18. Both retained reviewers
approved plan SHA256 `7b0081f7405bbbf71e4b69bb59ac314d911632d97d27d5fc6c0689308ff3524f`.
Normal mode remains in effect; no explicit Autopilot opt-in was given. Both
retained reviewers approved T01 commit `0a89627ed7c41c4033674213f11fa9fc8d0dea2b`
with findings None. T01 passed its review boundary; subsequent task status is in the ledger above. Focused T01 evidence: six tests passed;
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

The owner approved this four-task implementation plan on2026-10-18. Mode remained
**human review before merge**, with automatic progression through dependency-ready
local tasks after required reviewer checks. There is one final review unit and no
intermediate PR merge, so Autopilot provides no extra merge authority. The mode question was presented; no explicit Autopilot opt-in was given. The local package is the authorized deliverable; no remote action is
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
with findings None. T02 passed its review boundary.


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

Both retained reviewers approved T03 commit `f982fc6bef6aecd3ea0c9e93a16b681dc45dd231`
with findings None. T03 passed its review boundary.


T04 focused evidence: official review README, recruiter narrative/tables/graphs,
three historical chapters, issue links and sanitized per-turn audit are prepared.
The refreshed audit independently reconciles164ended turns to25:07:39.349;
current open turn is excluded. Reported time includes tools/tests/waits, not human
labor. Both report charts were visually inspected. A fixed69-file allowlist builds
an approximately1.2MBZIP with no research directory, credentials, Git/venv/cache
or raw conversation. Current guide/report links resolve in the exported copy;
historical chapter exports rebind lab links to compact metrics/source hashes,
without rewriting the original chapters or frozen whiteboard. Preliminary ZIP
checksums, executable helper and extracted Stage3smoke passed; full installation,
complete corpus comparison and final readiness remain pending the implementation
audit. See [preliminary package evidence](../../docs/reports/evidence/package-focused.json).
No report/README pending result is represented as passed.


## Final implementation audit

Both retained reviewers approved T04 commit `571dd9b04c6d36116d72bb0aa31abc1ae139b2f3`
with findings None. All four implementation tasks are DONE with their focused
checks; full corpus, fresh dependency install and final archive checks remain
explicit final-gate obligations, not implied passes.

Author self-review of that exact implementation: every runtime/test/package
addition maps to C1-01..13; existing algorithms, client/models, validators,
fixtures and Python conventions were reused. No new planner framework,
unauthorized game/remote action, research import in runtime, socket mutation on
library import, redundant search implementation or speculative runtime rejection
was introduced. Historical sources and the frozen whiteboard remain unchanged.
The code is organized/documented for human review; report comparisons remain
source-bound and conditional correctness/complexity limits are explicit.

Implementation-code content digest (sorted path/SHA256 rows, compact JSON):
`c65363bde5f03484b0f21fc9d477b3de0e426b62107b78871e0284754c205f95` across 32 Python source/test/build files.
Both retained reviewers approved the exact implementation audit at
`00e402b0ffeafb7fff8d2b885c01805e1484ba36`, findings None, before final tests.
Full final validation then passed as recorded below. Later outcome-only report/ledger/evidence reconciliation must not
alter this implementation content; any code change repeats the audit.


## Actual final outcome and cleanup boundary

| Accepted outcome | Actual evidence / remaining obligation |
| --- | --- |
| C1 delivered / T01–T04 | All four tasks DONE after both retained reviews, findings None. Runtime code digest above unchanged. |
| Complete regression migration | 658/658 matching verdicts/plans/non-time counters:93server records,108Stage1,150Stage2,307Stage3controls; zero UNKNOWN. Winning plans strictly replayed under applicable modes. |
| Applicable suites | 115portable tests pass;367historical tests across42isolated modules pass. These overlapping suites are reported separately. |
| Portable installation | Fresh extracted ZIP installs locked dependencies, runs115portable tests and allthreeoffline smokes, with research/.env absent and imports resolving inside the copy. |
| Report/evidence | Recruiter report, three historical chapters, graphs,26:17:20.657ended-turn stage audit, issue links and full per-record migration results reconciled. Current report revision is excluded; human labor remains unavailable. The earlier25:07:39.349audit remains a labeled historical snapshot. |
| Source preservation | All bound research/runtime and immutable receipt/control hashes checked unchanged;
portable input/task/witness/stop data unchanged (derived-document snapshot metadata clarified); frozen whiteboard SHA256 remains446eaa688657df6497ad6e922ce93f3cf22a5c9284db1d973ccb913dac391aa4. |
| Final package | PASS:77allowlisted files,79ZIP entries,1,874,035bytes; manifest/checksum/CRC entries valid; same tested runtime/client/tests, builder allowlist-only change reviewed; no research/credentials/Git/caches; helper executable. |
| Remote lifecycle | No publication, PR creation, email, merge, target verification or post-merge cleanup is authorized/performed. This does not block the requested local package. |

Actual checks are bound in [migration-full.json](../../docs/reports/evidence/migration-full.json).
No missing test, failed check or material deviation remains. Outcome-only final
report/evidence reconciliation was approved by both retained reviewers at
`d0151301d1de1ee7d0b35ede2060ad581c2edb01`, B-P2 resolved; any code
change would invalidate the implementation audit and repeat it.

Keep official code, portable tests/evidence and reports. Keep the owner-held
research, dirty authority/experience changes, historical script and credentials
untouched. Retain this branch/worktree because it contains preserved unmerged
research. No archive/reset/removal is performed: combined lifecycle archival and
worktree retirement belong to an explicitly authorized PR/merge close, not this
local handoff. The existing plan remains the active state authority until then.


Final reviewer finding B-P2 (blocking attribution, now fixed): the extraction
inventory listed the mutable delivery-evidence.json draft hash among immutable
sources. A reviewer checking all hashes would see a failure after legitimate
report metadata updates. The original hash is retained as a labeled historical
snapshot, current document hash/task-inventory binding recorded, and the
unchanged receipt/runtime sources verified separately. The same clarification
is applied inside the portable server corpus; its input/task/witness/stop
subtrees are asserted identical. Corpus checksum updated for this metadata-only
change. This is a necessary C1-11 attribution correction, not an algorithm change;
no solver test is rerun or represented as newly executed. Both retained reviewers
receive the exact corrected candidate. Remaining finding disposition: fixed.


Final handoff verification passed after both final reconciliation approvals.
ZIP SHA256: `102d3813194b648d5775ecc647a7567316142447353a52a2de5b6a18d1d0cf4d`.
The archive includes the complete658-record evidence and corrected provenance;
its31runtime/client/test files are identical to the fresh-install tested copy.
The later report refinement changes only the builder file allowlist; its new
implementation digest and audit are recorded below.
See [local verification proof](../../artifacts/final-verification.json).
Final reviewer dispositions: A — APPROVE corrected final reconciliation,
findings None; B — APPROVE final reconciliation, B-P2 resolved, remaining
findings None. No authorized local task or validation remains open. Remote
publication/merge remains outside this delivery authority.


Owner-requested README completion (C1-09 / C1-11): the review guide now gives the
full three-stage game picture, cumulative structures/costs, resource-chain graph,
shared actions and ordered examples for stone, ore and iron. All three examples
pass independent raw replay. README SHA256:
`d585c5f2365170ef3272c72642ba004388fe9e735c2c0ef29127b6739bdb5e0c`.
Reviewer A: APPROVE README update. Findings: None.
Reviewer B: APPROVE README SHA256 above. Findings: None.
The rebuilt package's manifest/checksums/CRC and exclusions pass; its code digest
and frozen whiteboard remain identical to the tested delivery. Existing solver
validation remains applicable; no full suite or server operation was repeated.
The current archive size/hash above and local verification proof are refreshed.


## Owner-requested visual report refinement

2026-10-19: owner requests fewer words, more design/performance graphs, three
stage stories with existing stage reports included, evidence-led candidate
selection, accurate classification of the two live solver stops, and time
reconstruction because TiMaS records are inaccurate. This extends T04's accepted
report/readability outcome (C1-09 / C1-11), without changing the frozen design.
The assignment email was read with owner authorization; only its non-sensitive
requirements summary enters the evidence. No email is sent.

Reuses historical metrics, incident receipts and source-bound comparisons.
Adds three stage comparison figures and one stage-time figure; old evidence,
chapters and raw measurements stay unchanged. The package builder changes only
its file allowlist to carry the seven new report assets/evidence files. No solver,
client, test, dependency or submission behavior changes. The previous 32-file
implementation digest includes the builder, so it is a historical validation
binding; current runtime/test identity and the new builder digest will be checked
separately. Proportional checks cover plotted values, source hashes, sanitized
stage-time sum/classification, links, rendered images and the final ZIP. No new
benchmark or server request is required. Both retained reviewers assess this
exact implementation/report candidate before final archive validation.


Visual report final outcome: PASS. Main report reduced from3243to1766words
(about46%); four static figures plus four Mermaid diagrams explain stage
progression, shared search, observability, live diagnosis, candidate choices and
stage-time estimates. All original stage reports remain included. Plot values,
source hashes,166paired turn durations, conservative/primary allocation ledgers,
links and rendered PNGs were checked. The same runtime/test bytes retain their
prior658/658migration,115portable and367historical test evidence; these suites
were not unnecessarily rerun for presentation changes.

Both retained reviewers approved before final archive verification:
A — APPROVE revised report and packaging audit; remaining findings None.
B — APPROVE this report/archive candidate; remaining findings None.
Report SHA256: `f2d5fa5d3c06f38ddd41d57cf0815234affdd6f10cf2ae177872917bd8fbd695`.
Builder SHA256: `baff4e6f177677fd6a4d1d4c9b138eaf6b42626581c445fdbef678378787d5b7`.
Current32-file content digest: `95735ab4acc2ca1e49a379b793c14fc875c524863c5664f62dc5b6b28eb0f023`.
Unchanged31-file runtime/client/test digest: `5bcec5accbe8479e7f0ad79b97d5fc4a747f93616ec98d8a85c40e9b1ce82d42`.
Final77-file archive,79entries,1,874,035bytes passed manifest/source/checksum/CRC,
all new figures/audit inclusion, unchanged runtime/fixtures/design and exclusions.
Current ZIP SHA256: `102d3813194b648d5775ecc647a7567316142447353a52a2de5b6a18d1d0cf4d`.
See updated [handoff proof](../../artifacts/final-verification.json).

| Finding | Concrete example | Solution | Disposition |
| --- | --- | --- | --- |
| A-P2: valid plans conflated with accepted progression | S1 task8596b928passed validation but its late submission hadaccepted=false;93accepted plans would misstate credit. | Report says93valid plans,88timely; evidence key ispassed_submitted_plans. | fixed; both reviewers approve |

| Assumption | Dangerous-assumption category | Evidence / validation state | Impact if false | Handling |
| --- | --- | --- | --- | --- |
| Whole-turn main context approximates stage effort | Uncertain attribution |166recorded durations reconciled; mixed ledger/ranges retained; TiMaS inaccurate per owner | Per-stage attribution can shift; human labor remains unknown | DISCLOSE; label estimates, preserve mixed/shared work and cutoff |

No new runtime rejection, game task, submission, email, publication or merge.
No authorized local task remains open. Prior user-owned changes are preserved.
