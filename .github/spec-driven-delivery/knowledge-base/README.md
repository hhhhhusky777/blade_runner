# Engineering Knowledge Base

Shared, distilled engineering guidance for authors and reviewers. Use it to
make project-specific decisions with less trial and error—not to introduce
another framework, checklist, or source of project policy.

## Applying the guidance

The project manifest identifies canonical authorities and the installed KB
root. Skills retain concise principles and tell agents which topic to read
when relevant. Read that topic directly; this README is a human-facing index,
not a mandatory intermediate step.

Apply the topic's core principles within the project's approved scope,
contracts, policies, and existing mechanisms. Choose the simplest sufficient
solution that satisfies both boundaries. Examples and techniques illustrate
choices; they are not universal implementation recipes. Neither mechanical
adoption nor silently ignoring a principle is an adequate application.

If these boundaries genuinely conflict, use the project's canonical
error-handling and decision authority. The KB grants no permission to change
scope, weaken a policy, or add a new blocking control.

[Solution Research](solution-research.md) owns evidence-grounded solution
selection at design and implementation levels. Topic references are starting
points; the shared guide explains research, applicability and evidence reuse.

Distinguish established engineering principles from evolving multi-agent
methods; neither a reference nor an example becomes project authority.

## Content selection and refinement

Select and refine topic guidance using all four criteria:

| Criterion | What the content must provide |
| --- | --- |
| Explain a problem class | Address a reusable engineering problem, not just an isolated trick. Reducing unnecessary data movement is a topic; zero-copy is one possible technique |
| Explain the causal chain | Show which design or code choice creates a cost or risk, and why an alternative may reduce it under stated conditions. Costs include execution, comprehension, change and maintenance—not only runtime overhead |
| Enable action | Help agents recognize the situation, locate the relevant code or design decision, identify applicability conditions, and choose a useful next action. Point to authoritative references for unresolved method questions |
| Preserve necessary boundaries | Retain ownership, lifetime, consistency, correctness, safety, compatibility and accepted project behavior. A simpler or faster alternative is not sufficient if it breaks these guarantees |

These criteria apply across the KB, including design, coding, testing and review.
Evaluate the topic as a whole; do not require every example to repeat its
surrounding explanation or every topic to use identical sections. Keep this
shared selection guidance here and topic-specific application in each document.
This is not another project gate or a mandatory technique checklist.

## Topic index

All topics below are available. Read the topic relevant to the work; this index
does not require reading the entire Knowledge Base.

| Topic | When it helps | Document |
| --- | --- | --- |
| Solution research | Select applicable solutions using project constraints and authoritative evidence | [Solution Research](solution-research.md) |
| Simple design and reuse | Reuse existing capabilities; minimize new responsibilities and mechanisms | [Simple design and reuse](simple-design-and-reuse.md) |
| Architecture, scope, and assumptions | Establish ownership and evidence-bounded design premises | [Architecture, scope, and assumptions](architecture-scope-and-assumptions.md) |
| Contracts and compatibility | Change interfaces without accidental contract breakage | [Contracts and compatibility](contracts-and-compatibility.md) |
| Error handling and diagnosability | Preserve invariants with simple failures and useful diagnosis | [Error handling and diagnosability](error-handling-and-diagnosability.md) |
| Testing and reproduction | Prove changed behavior and reproduce material failure risks | [Testing and reproduction](testing-and-reproduction.md) |
| Security basics | Protect actual trust boundaries proportionately | [Security basics](security-basics.md) |
| Proportional review | Assess material problems, correction value, and reasonable dispositions | [Proportional review](proportional-review.md) |
| Efficiency and concurrency | Overlap independent work without unnecessary coordination | [Efficiency and concurrency](efficiency-and-concurrency.md) |
| Experience and learning | Turn verified lessons into actionable reuse and refinement | [Experience and learning](experience-and-learning.md) |
| Code simplicity and clarity | Make implementation intent and behavior easy to understand without sacrificing correctness | [Code simplicity and clarity](code-simplicity-and-clarity.md) |
| Performance and observability | Design measurable, interpretable feedback and improve useful outcomes within whole-system trade-offs | [Performance and observability](performance-and-observability.md) |
| Code-level performance engineering | Locate avoidable implementation costs and choose bounded, source-backed improvements | [Code-level performance engineering](code-level-performance-engineering.md) |

## Installation and ownership

Official documents live in the playbook's `knowledge-base/` directory and are
installed at `.github/spec-driven-delivery/knowledge-base/`. They share the
manifest's immutable playbook revision, are Git-tracked, and survive feature
cleanup. Adoption and accepted upgrades synchronize the complete official
tree using the installer; candidate preparation is not activation. Legacy
revisions without a KB remain valid.

Keep general practice here and project-specific lessons in the manifest-linked
Experience document. Official synchronization preserves project policies,
Experience, and unrelated local content. A local edit to managed guidance
requires reconciliation, not silent replacement. Do not put feature status,
review history, secrets, or raw incident logs in the KB; the plan and PR retain
their existing responsibilities.
