# Project Adoption Manifest — Blade Runner

<!-- sdd: manifest -->

This reusable installation contract contains no feature-specific state.

## Installation

| Field | Value |
| --- | --- |
| Project / repository | [Blade Runner](https://github.com/hhhhhusky777/blade_runner) |
| Adoption state | `INSTALLED` |
| State before block | `None` |
| Playbook source repository | `https://github.com/hhhhhusky777/spec-driven-delivery-playbook.git` |
| Playbook revision | `74484f654c035ca4682a8cacd43abca1eb504c5a` |
| Upgrade state | `NONE` |
| Upgrade candidate | `None` |
| Adoption scope | This repository's documentation and future authorized solver delivery |
| Project adoption root | `.github/spec-driven-delivery` |
| Knowledge Base root | `.github/spec-driven-delivery/knowledge-base` |
| Materialization mode | Installer-verified immutable checkout; managed skills and complete official Knowledge Base |
| Target base revision | `Not applicable`: repository has no commits at discovery |
| Adoption owner | Project owner of [blade_runner](https://github.com/hhhhhusky777/blade_runner) |
| Required review | Two independent read-only agent reviews, then explicit owner acceptance |
| Owner acceptance | 2026-10-16; owner instructed "active" after both independent reviewers approved the adoption candidate |
| Last verified | 2026-10-16; installed runtime and authorities reconciled; authorized initial local commit resolves the unborn-repository gap G04 |

## Adoption outcome and scope

| Concern | Accepted outcome or boundary |
| --- | --- |
| Purpose | Keep project authority, design, delivery planning, and engineering guidance discoverable between sessions. |
| In scope | Pin the playbook; install its KB and local runtime; add an agent entry point, manifest, neutral whiteboard, experience guidance, and secret/cache exclusions. |
| Out of scope | Solver implementation, new game tasks, game submissions, email, remote changes, initial Git commit, and feature planning. |
| Success signal | Owner-accepted manifest pin; matching workflow runtime and managed guidance; empty whiteboard; no implementation plan. |
| Rollback boundary | Preserve all pre-existing project files. Before acceptance, abandon only adoption-owned additions; use installer ownership checks for local runtime cleanup. |

## Canonical project authorities

| Concern | Canonical source | Applicable boundary |
| --- | --- | --- |
| Project purpose, rules, setup, commands | [Project README](../../README.md) and [starter README](../../game_solver/README.md) | Existing local guidance; live game contract and actual task data govern server behavior. |
| Contributor / agent entry | [AGENTS.md](../../AGENTS.md) | Accepted installation routing and existing-work preservation. |
| API shapes and client behavior | [Models](../../game_solver/api_client/models.py) and [client](../../game_solver/api_client/client.py) | Starter code is evidence of client behavior, not proof of server enforcement. |
| Security and external actions | [README setup](../../README.md#setup-and-commands), [AGENTS.md](../../AGENTS.md), [.gitignore](../../.gitignore), and owner's current instructions | Keep tokens out of Git and final ZIPs; installation grants no server or publication authority. |
| Engineering practice | [Installed Knowledge Base](knowledge-base/README.md) | Complete official tree at the same immutable pin; guidance does not override project authority. |
| Reusable project lessons | [Project experience](../../docs/experience.md) | Verified lessons with applicability limits; not a new policy or delivery ledger. |
| Review and merge | [Pinned adoption skill](https://github.com/hhhhhusky777/spec-driven-delivery-playbook/blob/74484f654c035ca4682a8cacd43abca1eb504c5a/skills/sdd-project-adoption/SKILL.md) and owner's acceptance | Independent agent review precedes human acceptance. No merge permission or remote branch protection is inferred. |

### Project discovery inventory

| Concern | Existing authority or evidence | Discovery / handling |
| --- | --- | --- |
| Existing project work | Root README and 22 starter-package files; all untracked at discovery | Preserve byte-for-byte; no checkout, stash, reset, or initial commit. |
| Contribution, branches, PRs | No existing AGENTS.md, CONTRIBUTING.md, branch policy, or review policy; Git remote points to the project URL | Add a minimal entry point; record absence without inventing protection rules or importing the source repository's policy suite. |
| Tests and validation | Python 3.13 declared in [pyproject.toml](../../game_solver/pyproject.toml); no project tests or CI found | Nonblocking adoption gap. Select meaningful checks when solver delivery is designed; dependencies do not establish an accepted gate. |
| Documentation and contracts | Existing READMEs, client/models, and [game page](https://bladerunner.reef.pl/) | Preserve existing documents; distinguish documented rules from simulator behavior. |
| Security and privacy | README says to exclude tokens from Git and archives; no ignore file existed | Add local secret and Python-cache exclusions; no credentials copied or configured. |
| Release / operations | No release pipeline or deployed project service | Not applicable to this local solver installation. |
| Timing / performance | README describes the task-creation deadline and game-turn limit | No universal solver runtime guarantee or server validation exists. Future work must measure both. |
| Decisions and experience | README is the existing human overview; no separate Experience owner existed | Add concise project experience and keep the adoption whiteboard empty. |

## Stable project boundaries

| Boundary | Value |
| --- | --- |
| Protected content | Preserve existing README and supplied solver code during adoption. Official KB files remain installer-managed and revision-matched. |
| Required environments | Git and Bash for installation; Python 3.13 and uv for later solver use. Documentation check tools are validation aids, not new runtime dependencies. |
| External mutation authority | Follow the owner's instruction for each work scope. This installation includes no game requests/submissions, email, push, or merge. |
| Destructive-action authority | Installation does not authorize resetting or cleaning user work. Installer cleanup is limited to its verified owned runtime checkout. |
| Machine-local material | Runtime, managed skills, and installer are locally excluded by the installer. Manifest, KB, entry point, whiteboard, and Experience are Git-tracked installation material; no commit or publication is implied. |
| Known exceptions | Adoption discovery predates the first commit; Target base revision records that historical boundary. Current delivery baselines belong in their delivery context, not this manifest. |

## Validation and enforcement

These describe the installation check scope, not a new solver acceptance suite.

| Check | Scope / evidence | Status handling |
| --- | --- | --- |
| Runtime provenance | `./install-sdd.sh --validate`; pinned revision, ownership, skills, KB inventory | Must pass for this candidate. Before a manifest exists, pass the same explicit `--revision` used at installation. |
| Documentation | Check added document links, Markdown, lifecycle fields, and managed KB integrity | Validate the adoption candidate; report pre-existing issues separately. |
| Preservation / secrets | Compare all 23 baseline file hashes; check ignore patterns without printing credentials | Must preserve existing content and avoid secret inclusion. |
| Independent review | Two read-only agents inspect the same final candidate | Resolve material findings before presenting owner acceptance. |
| Solver tests / server acceptance | No product behavior changed; no live game task is needed for adoption | Not run; future delivery chooses appropriate checks. |
| Activation | Owner accepts the exact adoption candidate | Only then change to `INSTALLED`, regenerate the matching workflow runtime, and validate. |

## Gaps and proportional exclusions

| ID | Observed state | Handling / adoption impact |
| --- | --- | --- |
| G01 | No test suite or CI exists for the starter | Disclose; nonblocking for installation. Define solver validation during future authorized design. |
| G02 | No prior contributor, review, release, or general error-handling policy exists | Preserve absence; use owner instructions and existing authorities. No policy-file suite is required for this small project. |
| G03 | Local simulation does not fully validate the server's rules | Already documented in README and Experience; no solver-equivalence claim. Does not block installing guidance. |
| G04 | Adoption discovery found an unborn repository | Resolved 2026-10-16: owner authorized an initial local commit containing the existing project and approved installation. No remote publication or branch-protection claim follows. |

No playbook deviations are proposed. Service operations, production rollout,
database migration, and infrastructure policy are excluded because this is a
local client with no such components. Revisit if the project gains them.

## Adoption human brief

| Human need | Summary | Handling |
| --- | --- | --- |
| Acceptance scope | Owner accepted the pinned playbook adoption for this repository, retaining existing project content and the neutral whiteboard. | NONE |
| Sources and choices | Reuse existing READMEs and API code; add only installation routing, Experience, secret/cache exclusions, and the complete official KB. | DISCLOSE |
| Gaps and limits | G01–G04 above; no solver validation, Git publication, or server mutation. | DISCLOSE |
| Validation | Runtime and scoped checks plus both reviews are reported on the exact candidate in the adoption response; this manifest is not a review log. | DISCLOSE |
| Pin and activation | Full SHA above; adoption is INSTALLED under owner acceptance, with the workflow runtime selected at the same pin. | NONE |

Future feature state belongs in the implementation plan when one is created;
detailed PR review and merge evidence belong in pull requests.
