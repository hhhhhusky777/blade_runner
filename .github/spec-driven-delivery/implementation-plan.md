# Implementation Plan — Recruitment solver delivery

<!-- sdd: implementation-plan -->

This file owns execution state. The concluded whiteboard owns design; the recruiter
report is an implementation deliverable, not a prerequisite for concluding design.

## Delivery status

| Field | Value |
| --- | --- |
| State | `COMPLETE` |
| Active tasks | None |
| Next ready task | None |
| Active blocker | `None` |
| Implementation mode | Human review before merge; Autopilot is not enabled |
| Delivery branch | `codex/stage1-solver-design` in the existing managed worktree |
| Integration model / required PR target | One final review unit; prospective single PR to `main`; no intermediate task PRs |
| Implementation baseline | `52e793ce1f71dd09f2013c7b020eebbd6a5ad06c` plus preserved, source-bound research inputs |
| Accepted design | [Whiteboard C1](solution-whiteboard.md), concluded in `c9589dfb115341abe40552ffc845213db03cccc8` |
| Candidate and freeze | Reviewed candidate `cb929ff0a5ca0569069920890b181b469487ab64`; both retained reviewers approved the exact state-only freeze |
| Required reviewers | Retained conclusion reviewers A and B through task, audit and final review |
| Owner | Project owner; C1 explicitly accepted on 2026-10-18 |
| Publication / merge authority | Owner explicitly authorized finalizing and pushing to main on 2026-10-20; publish through the agreed single closing PR. Update the unsent recruiter reply with charts and GitHub links. Email sending and new game requests remain unauthorized. |

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
`main`, current PR [#6](https://github.com/hhhhhusky777/blade_runner/pull/6). Tasks are review boundaries within one delivery;
no task is merged separately. Before marking a task DONE, run its focused checks
and obtain both retained reviews. Stop and consult the owner if a task reaches
90minutes of active implementation before that boundary; tools/tests/review waits
are not active implementation time.

| ID | State / dependencies | Observable outcome and owned scope | Focused evidence before task review |
| --- | --- | --- | --- |
| T01 | DONE / None | Pure `game_solver/solver/` foundation: Stage1 geometry/search, selected last-topology cache and investment DP, independent raw validators. Remove benchmark imports and temporary global configuration from the official path; keep Stage1 probe/bound semantics. | Stage1 fixed inputs and tiny raw-oracle/bound checks; selected-preset differential plans/work; import leaves sockets/environment unchanged. |
| T02 | DONE / T01 | Package Stage2 typed search/guidance and Stage3 production/project ordering/on-demand DP. Preserve original-input replay, delegation preconditions and512/512/32 defaults. Add public solve boundary and readable state/function contracts; no algorithm changes. | Stage2/3 partial-production, impossible-bound, forced-DFS and projection controls; focused old/new outcome/plan comparisons. |
| T03 | DONE / T02 | Official runner and `submit.sh`, fixed packaged smoke example, portable corpus and task-to-input inventory. Add all93task records, including18fresh Stage3 maps, preserve92distinct inputs and stopped observations. Preserve the existing one-submission/reconciliation/deadline/progression behavior. | Fake-client recovery, ambiguous creation and no submission retry; child network denial/token removal; strict replay in both retained relay modes; targeted saved-map solves. |
| T04 | DONE / T03 | Complete the consolidated client report with three-stage summaries, diagrams/tables, sanitized time audit and issue links. Update review README and build an allowlisted local source ZIP with inventory/checksums. Retain historical source/timing attribution; no private conversation or credentials. | Report number/hash/link and visual checks; archive inventory and exclusion checks; preliminary clean-copy/offline CLI smoke. Final full corpus and ZIP validation remain the final gate below. |
| T05 | DONE / T01–T04 | Owner-authorized correction after final CI: reduce repeated Stage 2 geometry, completion and inventory work while preserving search choices, ordering, pruning and the 30-second budget. No case-specific behavior or new live requests. | Both retained reviews approved; 125 unit tests, 31-file strict typing, all 658 regressions, three fixed deadline stress runs and extracted-package checks passed on `0e03c72`. |

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
6. Deliver the reviewed package and report. The owner authorized publication,
   a closing PR and main integration on 2026-10-20; verify the exact target before
   reporting completion. At this normal-delivery close, create
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
| C1 delivered / T01–T04 | All four tasks DONE; owner-requested function contracts and consolidated packaging also reviewed. Current source bindings are in readability-validation.json. |
| Complete regression migration | 658/658 matching verdicts/plans/non-time counters:93server records,108Stage1,150Stage2,307Stage3controls; zero UNKNOWN. Winning plans strictly replayed under applicable modes. |
| Applicable suites | Current115portable tests pass;31modules pass strict typing. The prior367historical tests across42isolated modules remain historical evidence, not a new run. |
| Portable installation | Fresh extracted ZIP installs locked dependencies, runs115portable tests and allthreeoffline smokes, with research/.env absent and imports resolving inside the copy. |
| Report/evidence | One consolidated client report with three stage summaries, graphs,26:17:20.657ended-turn stage audit, issue links and full per-record migration results reconciled. Current report revision is excluded; human labor remains unavailable. The earlier25:07:39.349audit remains a labeled historical snapshot. |
| Source preservation | Research, receipts and regression inputs remain unchanged. Authorized client/docs/configuration changes have current source bindings; old hashes are explicitly historical. Frozen whiteboard remains unchanged. |
| Final package | PASS:74allowlisted files,76ZIP entries,1,997,067bytes; all manifest/source/checksum/CRC entries valid; final runtime/test/configuration bytes equal the clean tested copy; no standalone stage reports, credentials, research, Git or caches; helper executable. |
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
Current ZIP SHA256: `4007855ab7612625395f8b2cce7caa520764ba5dd1e907ecfd61baa0ab060a51`.
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


## Embedded stage summaries and quality presentation

Owner asks to replace links to full stage reports with embedded summary tables,
make pre-submission local validation explicit, and graph first-submission quality.
This is T04/C1-09/C1-11 presentation work. Historical reports and measurements
remain preserved; no algorithm, task, benchmark or submission changes. One new
quality graphic is added to the existing package allowlist. All93first submitted
plans were valid,88were timely; two live solver stops and three other operational
late cases are kept distinct. The owner's recalled two operational cases omits
one historical incident; both Stage1 incidents and the Stage2 acquisition
incident remain visible. No91/93solver-first-attempt rate is inferred because
acquisition failures lack comparable first solver attempts. Final solver/test
identity, static values, chart rendering, source hashes, links and final archive
are the applicable checks. Both retained reviewers assess the exact candidate.


Quality-summary refinement: PASS. The main report embeds three stage summary tables and removes all full-stage report links. A quality graphic shows local controls,93/93valid first submitted plans,88/93timely submissions and2solver/3acquisition-recovery incidents. Historical chapters remain preserved. Both retained reviewers approved the exact corrected candidate with no remaining findings.

Report SHA256: `c072210594aba21216793c5c8c6f7a7d87e89ee0b0d2a009f73fd39a58312433`.
Builder SHA256: `bf19bf3f38baa67385b22d9cca8d57185495b0b866fe8e0ac06512b535f13b0a`.
Current32-file digest: `4af63628d63f6e29e4f3c24f14d02c17a1d3f5d98f5108720c6092ae31f6487c`.
Current ZIP SHA256: `373064c70bec513115e039d6881205cfc1ddfb4d222d1fab16a2b3262d795414`.

The31runtime/client/test files and all fixtures remain unchanged; prior full
validation applies. Builder AST comparison confirms only one PNG allowlist
addition in this refinement. The final78-file/80-entry archive is2,077,728bytes.
Manifest/source hashes, checksums, CRC, executable helper, figure hashes,
exclusions and frozen whiteboard identity pass. See the refreshed local
[verification proof](../../artifacts/final-verification.json). No new benchmark
or solver test is represented as executed.

| Finding | Concrete example | Solution | Disposition |
| --- | --- | --- | --- |
| B: replay timing wording ambiguous | Later-wrapper wording could imply the runner's outer validation is timed; it is excluded. | Distinguish internal and outer replay. | fixed; both reviewers approve |

| Assumption | Dangerous-assumption category | Evidence / validation state | Impact if false | Handling |
| --- | --- | --- | --- | --- |
| Whole-turn context approximates stage effort | Uncertain attribution | Existing166-turn audit; shared/mixed work retained | Stage split can shift; human labor unknown | DISCLOSE; estimates and cutoff explicit |

No local delivery work remains open. Preserved user changes are untouched.
No server task, submission, email, publication or merge occurred.


## Client-readable source delivery

The owner's 2026-10-19 request explicitly removes the three standalone stage
reports, superseding C1-11/C1-13's earlier appendix packaging choice. Their
summaries stay embedded in the main client report; compact metric sources and
historical Git provenance remain. The frozen whiteboard stays byte-identical as
the accepted historical design; this explicit owner instruction governs current
packaging. Remove the unused stage-report timing images and export-only chapter
rebinding code, not the source measurements or regression inputs.

C1-09 continuation: document every named function in the delivered Python runtime,
client, tests and package helper with a meaningful concise docstring and accurate
parameter/return annotations (self/cls implicit). Keep existing algorithms,
constants, action/HTTP order, defaults, timeout/failure and validation semantics.
Add a README directory tree and a concrete reading path. Standard Python3.13
annotations and PEP257 docstrings are sufficient; no planner abstraction,
runtime type enforcement, new dependency or algorithm tuning is needed.
[Python typing](https://docs.python.org/3.13/library/typing.html) describes static
hints; [PEP257](https://peps.python.org/pep-0257/) guides purpose, result, side-effect
and exception documentation where applicable.

Validation uses a function/signature coverage audit, static type checks, comparison
of executable syntax with the previous reviewed source, existing portable tests,
all658retained regression/control records and an extracted-package smoke. The
same retained reviewers audit implementation before final full checks. Preserve
historical validation files as snapshots; bind fresh results to current source.
No new game tasks, submissions, email, remote publication or merge is authorized.


Client-readable source refinement: COMPLETE. All396named function declarations
plus2embedded test functions have meaningful docstrings and parameter/return
annotations. Strictmypy passes all31runtime/client/test modules and the package
helper separately. The README includes the delivered directory tree, five-step
reading route, control-flow graph and reproducible type/test commands. Three
standalone stage reports and two unused charts are removed; their summaries,
compact metrics and historical Git provenance remain in the consolidated report.
The package helper no longer contains obsolete chapter-export logic.

Both retained reviewers approved implementation digest
`a93aebfd1a947e62c2a324b2c0fd5bf6b2597f64b8b86bc7c61eafbb7d97be1f`
before final validation. All658records pass (558FEASIBLE/100INFEASIBLE); inputs,
verdicts, reasons, exact plans, expanded counts and replay modes match the prior
delivery.115portable tests pass. A fresh locked offline install passes the same
115tests,31-module stricttyping and allthreeoffline stage smokes. Final74-fileZIP
has the same32Python sources, configuration, lock/helper and fixtures as that
clean tested copy. Final manifest/source/checksum/CRC/exclusion/link checks pass.
No new performance study or live game operation was performed. The historical
367-test suite was not rerun; original migration evidence stays labeled.

Final reviewer dispositions: A — APPROVE final reconciliation; provenanceP2
resolved, remaining findings None. B — APPROVE evidence correction; remaining
findings None. [Current validation](../../docs/reports/evidence/readability-validation.json)
and [archive proof](../../artifacts/final-verification.json) bind the results.
CurrentZIP SHA256: `373064c70bec513115e039d6881205cfc1ddfb4d222d1fab16a2b3262d795414`.

| Finding | Concrete example | Solution | Disposition |
| --- | --- | --- | --- |
| A-P2: historical source hashes implied current identity | Client/model docstrings and project description changed, so three original source hashes no longer match delivered files. | Label the source inventory at full12f4bc4baseline; preserve old hashes and bind current Python/configuration files separately. | fixed; both reviewers approve |

| Assumption | Dangerous-assumption category | Evidence / validation state | Impact if false | Handling |
| --- | --- | --- | --- | --- |
| None newly introduced by this readability change | None | Existing model/time limits remain explicit in README/report | None added | NONE |

All requested local work is complete. Pre-existing manifest/experience/research
changes remain untouched. No server task, submission, email, push or merge.


## Quality terminology refinement

T04/C1-11 continuation requested by the owner: use **product issues** for the
two solver gaps and **non-product issues** for the three task-acquisition/recovery
incidents. The report, quality chart and stage tables define the classification;
Stage3's contributing acquisition delay stays explicit. Incident measurements,
93valid first submitted plans and88timely submissions remain unchanged. Neutral
wording removes “our”, “we” and “us” from the report; README's single “our” is
also removed. Historical incident/source provenance is preserved.

Reviewer A: APPROVE focused update. Findings: None. New dangerous assumptions: None.
Reviewer B: APPROVE. Findings: None. Dangerous assumptions: None introduced.

Focused verification passes: rendered figure, source/count/asset hashes, neutral
voice, local links and the74-file/76-entry archive's manifest, checksums, CRC,
exclusions and executable helper. All32Python sources and the frozen whiteboard
remain identical; prior658regressions/115tests/type checks apply without reruns.
No new benchmark or game operation was performed.

Current ZIP SHA256: `2ce4295a48c4d768d4bc5da877b0ed5f4595e6270ad0d9579b58f933c5b26fab`. Size:1,995,726bytes.
Report SHA256: `026acec2d95dcb19b08c5050ef26ff4d7c85390032d8e3ac4b9e1d793ce3705a`.

| Finding | Concrete example | Solution | Disposition |
| --- | --- | --- | --- |
| None | — | — | NONE |

| Assumption | Dangerous-assumption category | Evidence / validation state | Impact if false | Handling |
| --- | --- | --- | --- | --- |
| None newly introduced | None | Issue classification is explicitly defined; evidence unchanged | None added | NONE |


## Self-contained report and research references

T04/C1-11 continuation requested by the owner: make the report understandable
when read with an email. Replace all project-document and issue links in its
body with short explanations of code responsibilities, correctness/model limits,
complexity, the time-allocation method and remaining work. Keep the existing
charts, stage summaries and neutral voice. A six-entry bibliography explains
the influence of build-order, numeric-relaxation, resource-flow, lazy-heuristic,
SCIP scheduling and SRE troubleshooting research. All sources were already used
in the frozen research; primary titles/authors/publication details were checked.
The text distinguishes research inspiration from project-specific proofs and
measured adoption, with no new algorithm or runtime dependency.

Reviewer A: APPROVE report refinement; no actionable findings; no new material assumptions.
Reviewer B: APPROVE — no findings for the exact report.

Focused checks pass: no document/issue links in the report body; six bibliography
links; five unchanged chart images; neutral voice; unchanged stage metrics,
32Python sources and frozen whiteboard. The74-file/76-entry ZIP passes current
source/manifest/checksum/CRC/exclusion checks. Prior code validation applies; no
solver tests or server operations were repeated.

Report SHA256: `a116193c0d19a561ea7c91e6430337626ee1852adcd1581fe70172ef46d209ce`.
Current ZIP SHA256: `db141c4410ad479a6747ddb4ab0bee5d2c60ce7f0d012764549cafe3629ad92f`. Size:1,996,976bytes.

| Finding | Concrete example | Solution | Disposition |
| --- | --- | --- | --- |
| None | — | — | NONE |

| Assumption | Dangerous-assumption category | Evidence / validation state | Impact if false | Handling |
| --- | --- | --- | --- | --- |
| None newly introduced | None | Existing model and timing limits remain explicit; research attribution verified | None added | NONE |


T04 remaining-work clarification: COMPLETE. Existing issue5 is now a prominent
bullet: test using partial greedy-probe results to guide fallback policy/order
and avoid duplicate calculation. A probe miss cannot prove impossibility or
remove legal choices. Compare time to a validated win and added overhead. This
is explicitly future work, not a solver change or an established speedup.
Both retained reviewers: APPROVE the exact report; no findings. No new material
assumption. Surrounding text, code, evidence, charts and references are unchanged.
The refreshed74-fileZIP passes current source/manifest/checksum/CRC checks.
Report SHA256: `890b36b9eada9f6730e889c1a076a01b3f55f9baa759339f2a3a9bd82b55ba78`.
Current ZIP SHA256: `a943e062f8a81623eeb094c7178fe50bf3f321962745addd6d808b83089e8179`. Size:1,997,108bytes.


T04 solver-only follow-ups: COMPLETE. Owner requested removal of non-product
improvement work from the report. Removed acquisition-budget and cross-phase
timing bullets; retained rule correctness, route-cache/guidance comparison and
greedy-probe feedback under “Remaining solver work.” Historical issues and
incident evidence remain unchanged. Both retained reviewers: APPROVE the exact
report; no findings. No new material assumptions. Exact diff scope and refreshed
archive/source/checksum/CRC checks pass; no code changes or test reruns.
Report SHA256: `a378e44758e9b139ebdac2bd8d3b661044e78ec42f66b825588d54eda60ee5c0`.
Current ZIP SHA256: `4007855ab7612625395f8b2cce7caa520764ba5dd1e907ecfd61baa0ab060a51`. Size:1,997,067bytes.

## API alignment and README walkthrough

T03/T04 continuation requested by the owner on 2026-10-20: make the three public
solve branches consistent and retain the step-by-step code explanation in the
README. This clarifies C1's stage entry points and independent replay ownership;
the frozen design, search algorithms, adopted settings and historical evidence
remain unchanged.

Stage 1's preset now owns final replay, so `api.solve()` delegates for all three
stages. The preset's `search()` retains the previous unchecked search body for
Stage 2's stone-only projection; Stage 2 still validates the original task.
This avoids adding a projection replay or changing public-path replay counts,
deadline handling, emitted plans or timing definitions. Direct preset `solve()`
now also rejects an invalid candidate, covered by one fault-injection test.
The README explains input/plan types, dispatch, the cache/DP preset, Stage 2
options, independent replay, outcomes and the separate server deadline.
This is a bounded relocation of responsibility, consistent with the existing
clarity guidance and [Move Statements into Function](https://refactoring.com/catalog/moveStatementsIntoFunction.html).

Both retained reviewers: APPROVE the exact candidate; findings None. The final
preset docstring clarification was checked by both. Focused checks: 28 passed;
strict mypy: 31 source files passed. Final checks: all 116 portable tests passed;
all 93 saved server-task regressions passed locally, with identical input hashes,
verdicts, reasons, expansion counts and plan hashes against the retained migration
record. Diagnostic replay counts also match the existing Stage 1/2/3 reuse paths.
The full 658-record comparison remains the earlier delivery snapshot, not a new
run. No live game requests, submissions or remote publication occurred.

The local 74-file review ZIP was refreshed from the reviewed source. ZIP SHA256:
`33221f8538353bb6e391ff4c06ec023dc98a15e62575358f5ab82631351c5180`;
size: 1,998,633 bytes.

| Finding | Concrete example | Solution | Disposition |
| --- | --- | --- | --- |
| None | — | — | NONE |

| Assumption | Dangerous-assumption category | Evidence / validation state | Impact if false | Handling |
| --- | --- | --- | --- | --- |
| None newly introduced | None | Existing conditional model and deadline limits remain explicit | None added | NONE |

## Work-purpose accounting and quality explanation

T04 continuation requested by the owner on 2026-10-20: review the recruitment
feedback and explain development, comparison and validation time in the report.
The feedback and original assignment were read in Gmail. No email was sent or
draft saved there; no raw email or credentials were added to the delivery.

The new purpose audit classifies all 166 frozen root work periods once, preserving
26:17:20.657 total elapsed and every prior stage allocation. Comparison-led work
is 9:11:55.430; standalone coverage/validation is 2:14:46.056. Together they are
11:26:41.486 (43.5%). Coding and associated checks remain in their work packages;
mixed periods remain unsplit. This is assistant-turn elapsed including tools and
waits, not human effort or a correction to the recruiter's reported tracker time.
The report makes no estimate of a pass-only alternative's development time.

The report now identifies five delivered areas, explains the chosen live
acceptance standard, and includes a purpose table/chart plus two rejected
experiment examples. Existing stage results and limitations remain explicit.
The broader comparison program is described as chosen scope; necessity, other
candidates' quality and future maintenance savings are not inferred.

Both retained reviewers independently APPROVE the exact report/evidence/figure
and three packaging allowlist additions, with no findings. Both checked the
audit bindings and sampled source requests/outcomes; no claim is made of two
independent full semantic recodings. Root checks reconcile all ledger/CSV rows,
category totals, figure/source hashes and report image links. The chart was
visually inspected. Builder syntax and diff checks pass. Solver code was not
changed in this continuation, so the prior 116-test/93-record API validation
remains the latest code check; no solver tests or live tasks were repeated.

The refreshed local ZIP contains 77 source files / 79 entries and passes CRC,
current-source equality, manifest and checksum checks. Report SHA256:
`8255eb41acb4bf50dc742b7fa7dad26e09948d70f1acb2f13be2f698a3314e16`.
ZIP SHA256: `8dd1aa437a2c96c923d23cfdc7dc860194ae748b246da68b495745a208915ab4`;
size: 2,219,324 bytes. No remote publication, submission or merge occurred.

| Finding | Concrete example | Solution | Disposition |
| --- | --- | --- | --- |
| None | — | — | NONE |

| Assumption | Dangerous-assumption category | Evidence / validation state | Impact if false | Handling |
| --- | --- | --- | --- | --- |
| Whole-period purpose reflects its main deliverable | Measurement allocation | Source-bound classifications reviewed; ambiguity retained | Category mix may differ from actual coding/test time | Do not interpret as exclusive activity timers |
| Recruiter and conversation time are directly comparable | Measurement scope | Not established | Misleading claim about development speed | No reconciliation or counterfactual claimed |

### Owner-requested time regrouping

T04 refinement: COMPLETE. Solver requirements, design, implementation, review
and diagnosis share one row (7:24:18.234). Dedicated submission-script design,
implementation and checks are separated as non-product support (1:07:23.603),
with live execution/recovery separate (2:20:02.032). Comparisons total
10:13:15.183 and standalone validation 2:14:46.056. Documentation/delivery and
environment work retain their own rows.

The report/chart no longer contain an unattributed row. A derived presentation
mapping assigns mixed periods wholly to their supported main deliverable while
preserving original classifications and uncertainty. The original audit/CSV are
unchanged. The 165 displayed periods total 26:15:59.973; excluded interruption40
of 1:20.684 explicitly reconciles to the original 26:17:20.657. No within-period
timing or exclusive coding time is invented.

Both retained reviewers APPROVE the exact report, mapping and chart; no findings.
Root checks verify every displayed ordinal once, arithmetic, original/derived
source hashes, chart hashes, links and builder syntax. The chart was visually
inspected. No solver changes or test reruns. The new mapping is allowlisted in
the refreshed ZIP: 78 source files / 80 entries; CRC, current source bytes,
manifest and checksums pass. No external action occurred.

Report SHA256: `29aab88ea6fa2655bdd8c5258d3e93399da25e89a258d31188036163e08454c1`.
ZIP SHA256: `2bb77ad951604b1551ceb1f6aa0d665034dc0ac2d5dd6830a810d1d3362b4ee0`;
size: 2,221,219 bytes. Existing whole-period measurement limitations apply;
reviewers found no new material assumptions.

### Five-category time presentation

T04 follow-up: COMPLETE. Per owner instruction, submission-script development,
execution, verification and recovery share one non-product row (3:27:25.635).
Standalone environment/workflow work is omitted from the displayed breakdown.
Dedicated independent-review periods79/104 (30:39.140) move from development
to quality, yielding solver design/implementation 6:53:39.094 and quality
coverage/review/validation 2:45:25.196. Optimization planning78 stays design;
reviews embedded in other work packages are not artificially split out.

The five rows contain159 unique periods totaling26:05:07.749. The excluded
environment/workflow652,224ms and interruption80,684ms reconcile to the original
26:17:20.657. The original audit/CSV remain byte-identical. Both retained
reviewers APPROVE the exact report, mapping and chart; no findings. Existing
whole-period attribution limitations apply; no new material assumptions.

Arithmetic, coverage of all166 original ordinals, source/figure hashes, image
links and diff checks pass. Chart labels were visually inspected. Refreshed
ZIP:78 source files/80 entries; current source, manifest, checksum and CRC checks
pass. No solver changes, test reruns, server actions or external publication.
Report SHA256: `6b4212c7f456e9e240e5806c725bc83d7f4e01de450e21e4bedcde9d34b05165`.
ZIP SHA256: `4a741334afc7c3b4dfe61ddd8fc829ecc7495fe31545008eca574c5baa7b46ad`;
size:2,204,264 bytes.

### PDF report and recruiter reply draft

T04 follow-up: COMPLETE. The report is now a nine-page PDF with five original
charts and four vector diagrams. All 150 source prose/table units and six
reference URLs are preserved. Every page was visually inspected; no clipped
content or off-page characters were found. Retained reviewer A approved pages
1–4 and the renderer; reviewer B approved pages 5–9. Both independently approved
the reply text with no findings. Root additionally inspected pages 1, 6 and 8.
The Markdown report and existing charts remain unchanged.

An unsent Gmail reply was saved to the verified recruiter thread with the PDF
attached and the performance comparison chart inline. Readback confirmed the
recipient, reply threading, DRAFT label, reviewed HTML prefix and attachment
names/sizes. The private draft receipt and reply sources remain in ignored
`artifacts/`; they are excluded from the review ZIP. No email was sent.

The report-specific renderer and PDF validation evidence are included in the
allowlisted package. Refreshed ZIP: 81 source files / 83 entries, 2,932,396 bytes.
CRC, source equality, manifest hashes and archive checksums pass. No solver
behavior changed, so no solver tests or live tasks were repeated. No push,
remote PR creation or merge occurred.

Report SHA256: `6b4212c7f456e9e240e5806c725bc83d7f4e01de450e21e4bedcde9d34b05165`.
PDF SHA256: `97ea0c7821c82e5599da4c8bbeae623a1a16431b57ea92d514b0002dc327b88c`.
ZIP SHA256: `d7d61ff9465727b0b9a474d215679a60d3c46b4c1f0244c31c6167ff65f0ad25`.

Existing measurement limits apply: assistant elapsed time is not human labor
or a replacement for TiMaS, and measured candidate gains do not establish a
globally optimal solver. No new material assumptions or review findings.

Owner-requested email follow-up: COMPLETE. The existing unsent reply now embeds
the quality chart and all three stage comparison charts, with the PDF retained.
The headline states that 91/93 recorded tasks (97.8%) had no recorded product
issue; it does not claim uptime or first-attempt success. The two product stops,
93 valid submitted plans and 88 timely submissions remain distinct. Reviewer A
approved the exact text/HTML and denominator; reviewer B approved the images
at 900 px and factual framing. No required corrections. Gmail readback confirms
the same recipient/thread, exact revised HTML, four inline images and original
PDF, with DRAFT status. Private receipt updated; report, PDF and package unchanged.


## Final publication and close

The owner explicitly authorized finalization and publication to `main` on
2026-10-20. Implementation and the reviewable handover are complete; the
[closing PR #6](https://github.com/hhhhhusky777/blade_runner/pull/6) owns final-head
reviews, checks, merge outcome and target verification. Earlier no-publication
statements above record their historical authority boundary.

Both retained reviewers approved the final implementation audit and the small
offline CI workflow. The workflow checks the exact PR head using read-only
permissions, locked dependencies and unchanged time limits. It calls no game
endpoint and uploads no detailed task-result artifact.

### Actual final validation

| Evidence | Result / scope |
| --- | --- |
| Local source unittest | 116 tests ran; one Stage 3 child exceeded its 6-second outer timeout. One unchanged-budget isolated repeat passed. The original failure remains recorded. |
| Local strict types | Passed, 31 files. |
| Local full regressions | 657/658 passed. `economic-challenge-pool-034` was UNKNOWN at 30.3045 seconds; one unchanged 30-second repeat also returned UNKNOWN at 30.2802 seconds. |
| Local load observation | Load approximately 18 on 10 logical CPUs; Docker used several cores. Lower search throughput is consistent with contention, but the specific cause is unproven. No workload was stopped. |
| Fresh local package | 116/116 tests and all three offline submission smokes passed, without the research tree. |
| First clean GitHub runner | [Run 39432886934](https://github.com/hhhhhusky777/blade_runner/actions/runs/39432886934), head `6bc780c13b41bd65b3f442ff7158ca6f385ac0dc`: unit tests/types passed; regressions were 657/658. Its aggregate-only log cannot identify the failed case. Package check was skipped. |
| Diagnostic clean GitHub runner | [Run 39434315627](https://github.com/hhhhhusky777/blade_runner/actions/runs/39434315627), head `64c98da95d49786267baaa423e6550cef0a33e2f`: 116 unit tests, strict types, all 658 regressions at the unchanged 30-second limit, package build and extracted-package tests/smokes passed. Only diagnostic logging and independent package-step execution changed; solver bytes and budgets did not. |
| Source binding | Runtime/test digest `aa69559ad557f945f4549ebdcf868ef5111b5c868fbd9bd9c292f2903200312b`; fixture digest `b521b7bcf7c54a4c50544b7da797d1fc8bfb240c5bbf46fc85f53235838c94d4`. No solver or time-limit changes during final validation. |
| Publication contents | Exact reviewed paths only; configured-credential and private-path checks passed. Credentials, private email drafts and bulk research remain excluded. |

The failed local and first CI runs are not relabeled as passing. The diagnostic
run was requested to identify the failed case, not to retry until green; no case
failed in that run. Timing varies across environments and runs; the cause is
not established. Successful checks establish that run's result, not a universal
30-second guarantee. A bounded temporary comparison of redundant stock copies
and resource-tree lookups preserved a 20,000-state prefix but showed no material
CPU gain; no candidate optimization was adopted.
The historical performance report and its frozen time cutoff are unchanged.
Detailed local logs remain under `/private/tmp/blade-final-20261020`; durable
CI logs and final-head check results are linked from the closing PR.

### Archive and cleanup

The [combined delivery archive](archive/recruitment-solver-delivery.md) retains
the complete concluded whiteboard and this complete plan, with source hashes.
The original whiteboard remains byte-identical and both live documents remain
available to preserve existing review links. The current worktree and branch
are retained because they contain owner-held research and private artifacts;
deleting them would discard work outside the published package. No cleanup of
those files is authorized or claimed. The primary clean checkout can fast-forward
to the verified remote main after merge.

All three game stages are complete. Open performance and strategy proposals
remain tracked separately, especially [#4](https://github.com/hhhhhusky777/blade_runner/issues/4)
and [#5](https://github.com/hhhhhusky777/blade_runner/issues/5); this delivery does
not close them or claim unmeasured gains. The email draft includes the work-time
chart, documentation effort and links to the project and follow-ups. Email
sending and new game-task creation remain outside this authorization.

| Finding | Concrete example | Solution | Disposition |
| --- | --- | --- | --- |
| Deadline variability | Stage 2 stress case missed 30 seconds locally; first CI was also 657/658 | Preserve misses and subsequent diagnostic 658/658 result; retain the unchanged 30-second check | DISCLOSE; no solver change or universal timing claim |

| Assumption | Dangerous-assumption category | Evidence / validation state | Impact if false | Handling |
| --- | --- | --- | --- | --- |
| Host load fully explains deadline variability | Causal attribution | Local throughput fell, but the first clean CI also failed; cause unproven | Incorrect diagnosis of a timing risk | DISCLOSE; preserve failed evidence and avoid a causal claim |

## T05 — Owner-requested deadline reliability correction

The final-head run [39435720772](https://github.com/hhhhhusky777/blade_runner/actions/runs/39435720772)
on `5507d1d18f24b8fb9109ac567a3f4bc6db1b5880` again passed 657/658 cases;
`economic-challenge-pool-034` returned UNKNOWN at the unchanged 30-second budget.
Unit tests, strict types and the extracted package passed. The owner explicitly
chose to keep PR #6 open and fix reliability rather than merge with a timing
exception. Main remains at the original baseline.

This supersedes the proposed closure above. The source archive is a candidate
snapshot until regenerated from the corrected final plan. Existing passing and
failing evidence remains retained. No repeated unchanged attempts are used as a
substitute for a correction.

Both retained reviewers permit an implementation-only reduction of repeated
graph work under C1: preserve legal choices, distances, parent tie order,
inventory/turn semantics, policy defaults, pruning and all deadlines. Do not
activate the deferred pruning bundle or introduce map-specific behavior.
Measured candidates are bounded route/topology reuse and precomputed fixed
adjacency rules. A fixed-work comparison must preserve semantic counters and
plans; CPU and wall time are recorded separately. Focused graph-equivalence
checks precede all-stage regressions, repeated hard-case timing and final
package/CI verification. No new server calls or email sending are authorized.

Selected candidate: lazy, per-model static edge metadata. Resource cells and
BASE remain storage for the whole solve, so storage-to-storage exclusions and
matching-resource exclusions can be prepared once in the original neighbor
order. Occupancy, unbuilt extractors, costs, strict relaxation and queue order
remain dynamic and unchanged. The existing one-topology tree cache is retained.
No topology LRU or separate bitset connectivity mechanism is adopted.

| Local experiment | Observation / decision |
| --- | --- |
| Uninstrumented equal 20,000-state prefix | Baseline process CPU 2.277 s; lazy static edges 1.934 s (15.0% lower in this pair); semantic result/counters identical. This is not a full deadline result. |
| Topology/route LRU | Fewer graph rebuilds did not produce a meaningful net CPU benefit; reject. |
| Additional bitset connectivity | 5.8% higher median CPU than static edges alone in the direct paired comparison; reject. |
| Geometry equivalence | Independent original BFS and ordered route maps agree across both relay modes, topology changes, inventories and board boundaries. Four new portable tests; all ten Stage 2 tests passed. |
| Focused static checks | Strict typing passed for 31 files; purpose docstrings and parameter/return annotations remain complete in the edited Python modules. |

The local machine's variable scheduling and CPU rate limit timing conclusions.
Clean CI must now check all 658 retained cases, all unit tests/types and the
extracted package, plus three predeclared fresh-process attempts of the stress
control at 30 seconds each. Any failed repetition fails the check. Regression
telemetry now reports process CPU, outer wall time and expanded states without
printing inputs or plans. No retry-until-green rule or larger allowance is added.

The first corrected-head CI run
[39439593076](https://github.com/hhhhhusky777/blade_runner/actions/runs/39439593076)
on `e5a0a42e28fbe82cd1179c00b55ee9bd055754fb` still passed only 657/658.
The same control returned UNKNOWN in the suite and all three fixed repetitions.
Each consumed about 30.07 process-CPU seconds and 30.13 outer-wall seconds;
the repetitions expanded 316,692–330,445 states. This establishes CPU work as
the limiting cost in those CI runs; local scheduling alone cannot explain them.
All 120 unit tests, 31-file strict typing and the extracted-package checks passed.
Keep this failed correction as evidence; it does not establish deadline reliability.

The next bounded candidates schedule the existing optimistic bounds before
expensive wait-completion geometry, and share one immutable inventory summary
between the same bounds. A real wait-only win remains possible in every existing
relaxation, so early rejection removes no valid wait completion. Directly met
goals retain their shortcut; root checks, choices, policies, DP formulas and
limits remain unchanged. A final wait-winning state's earlier bound query may
populate additional DP entries: preserve and report that diagnostic difference,
rather than claiming all non-time counters must match.

Both retained reviewers approved runtime SHA256
`3c27cb83cbc7ff771d7b930cca5eb0a6eb6586c629a8eb67c915594eeaf326bc`.
It also returns the existing immutable state when all site stocks are zero:
the old settlement loop transferred nothing and never queried a tree in that
case. There is no new identity cache, producer mask, policy or work allowance.

| Follow-up evidence | Result and limit |
| --- | --- |
| Existing bounds before completion, alone | CPU fell 13.7% on an equal 20,000-state prefix and 12.5% on 100,000 states; non-time results matched. These are search segments, not complete deadlines. |
| Minimal combined candidate | Per-call summary reuse and zero-stock settlement join the bound move. Its short timing pair was affected by host-rate/scheduling drift and does not establish a combined speedup. |
| One full local attempt, 30 seconds | UNKNOWN: 30.175 s wall / 22.563 s CPU / 324,908 expanded states. Preserve the miss; clean CI remains the acceptance check. |
| Bounded semantic comparison | 30,314 assertions across 2,000 reachable states in both relay modes; 104 solve pairs across all four bound variants and probes on/off, including 64 replayed winning pairs and 40 impossible pairs. Plans and non-time results matched in these controls. |
| More elaborate summary prototype | Identity cache and producer masks were measured separately, then omitted from the chosen candidate to avoid unnecessary lifetime state. Its timing cannot be attributed to the minimal candidate. |

The immutable local investigation bundle has SHA256
`bba5a0285220febefb66a44a2d9d33f9ba961a8513d1e13e7332df03169a86e8`;
only these compact, sanitized results are published. The same full CI and three
fixed stress repetitions remain required. Focused tests must force DFS so probes
cannot bypass the reordered wait-completion path; counters on winning states
remain diagnostic, not a compatibility guarantee.

Focused portable validation passed all 15 Stage 2 tests, including forced DFS
across bound variants and relay modes, independently replayed wait/direct wins,
stranded stocks, summary equivalence, zero-stock topology changes, a tiny raw
oracle comparison and weak-pass DP exhaustion. Scoped typing and whitespace
checks passed. Test source SHA256 is
`87f3c3a47a8010a2c42cd0a55c8b6598918c7596441ac66581bdaeeaefc59b1f`.
The complete candidate's CI outcome follows below.

### Corrected final outcome

Clean CI [39443951274](https://github.com/hhhhhusky777/blade_runner/actions/runs/39443951274)
passed on `0e03c72e08cf4b23fa2ad4ddd2551ede7684a9ae` after both retained
reviewers approved the exact candidate with no findings. This completes T05's
correction and supersedes the proposed pre-correction closure and pending-state
statements above. The final documentation candidate contains the resulting
COMPLETE plan and regenerated full archive; PR #6 owns its exact-head checks,
authorized merge and target verification.

| Required check | Observed result |
| --- | --- |
| Unit tests / strict types | 125 passed; no issues in 31 source files. |
| Complete retained corpus | 658/658 passed at the unchanged 30-second budget, with original-input replay. |
| Stress repetition 1 | FEASIBLE; 20.8472 s wall / 20.8005 s CPU / 377,886 expanded states. |
| Stress repetition 2 | FEASIBLE; 21.1236 s wall / 21.0750 s CPU / 377,886 expanded states. |
| Stress repetition 3 | FEASIBLE; 21.0018 s wall / 20.9553 s CPU / 377,886 expanded states. |
| Fresh package | 125 tests passed without research files; all three offline submission smokes passed. |

The slowest repetition left 8.88 seconds within the local 30-second solve budget.
This is measured headroom on that CI runner, not spare time promised for server
acquisition, transport or every machine. The earlier 657/658 results, failed
static-edge correction and local combined-candidate timeout remain visible.
Do not turn the before/after CI runs on different hosts into a controlled speedup
percentage. The measured fixed-work comparison and successful final deadline
checks answer different questions.

No case, expected outcome or budget was weakened. Stage 1 and native Stage 3
algorithms remain unchanged; their regression coverage passed. No additional
game tasks, submissions or email sending occurred. The report's historical
timing comparisons and frozen work-time cutoff are unchanged. Broader performance
and partial-probe reuse proposals remain open in issues #4 and #5.
