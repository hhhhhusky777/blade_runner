# Solution Research

Choose engineering solutions from relevant evidence and project constraints,
not a familiar technique or unsupported guess. This guidance applies to design
and implementation, including reviewer alternatives and triage methods/remedies.

## Research requirement

> [!IMPORTANT]
> Before selecting any engineering solution, at design or implementation level,
> you MUST search the web for comparable problems and authoritative guidance using
> the problem, requirements, project boundaries and applicable KB principles.
> Include relevant language/version, runtime, libraries and deployment constraints.
> Use non-sensitive descriptions, not private project data, in external searches.
> Read the primary sources and assess applicability and trade-offs against
> project evidence and suitable existing mechanisms. Choose the simplest
> sufficient solution; familiarity, guesses, unsupported assumptions and
> subjective confidence MUST NOT substitute for research.

Treat language as an established constraint or an explicitly authorized choice;
research never grants authority to introduce a language or change project policy.
External practice cannot establish project facts or prove a bottleneck: verify
those premises against canonical contracts, code or direct evidence. Research
supports a triage method or remedy, not proof of a project-specific cause.

## PoCs and comparative experiments

Use a small proof of concept (PoC) or comparative experiment when research and
existing project evidence leave a decision-critical uncertainty that an
experiment can resolve at proportionate cost. Research identifies candidates;
experiments test their project fitness. Neither replaces the other, and a PoC
is not mandatory for every solution.

| Focus | Application |
| --- | --- |
| Decision | Define the question, success criteria and how the result will affect the choice before building. |
| Scope | Implement only the slice needed to answer that question. Bound time and cost, and define when to stop; do not expand the experiment merely to make a preferred candidate pass. |
| Comparison | Include a suitable existing mechanism as the baseline. Use comparable goals and representative inputs and load; disclose relevant language, runtime and configuration differences. Account for measurement variability rather than select the best run. |
| Choice | Weigh correctness, benefit, cost, complexity and maintenance. Choose the simplest sufficient option, not the highest isolated metric. Evidence against a candidate is a useful result. |
| Limits | State tested and untested conditions and what the results establish. A small demonstration does not prove production performance or readiness, and a PoC does not replace required delivery tests. |
| Safety | Use authorized non-production resources and appropriately protected data. Experimentation does not authorize production changes, new dependencies or wider scope. |

For example, compare a representative processing path using an existing library
and a proposed framework. If both meet the requirements, a small speed gain may
not justify the new framework's integration and maintenance cost. Keep the
decision and material evidence in the existing design, plan or PR, not a new
PoC report or approval gate.

## Reuse and uncertainty

Reuse already-read research while it remains current and applicable; do not
repeat browsing for each coding action. For unresolved engineering-method or
applicability questions, low confidence or unsupported material claims, read
the relevant primary references before deciding. If sources are unavailable or
material uncertainty remains, disclose it and follow existing error handling.

A skill summary or prior familiarity does not replace reading this document;
unchanged content already read in context need not be reread routinely.
No per-delivery research record, fixed source count, prescribed technique or
separate gate is required. Keep material rationale in its existing design,
implementation or PR owner.

## Supporting references

These sources support evidence-based judgment and contextual trade-offs. The
mandatory research trigger is this playbook's requirement, not a claim that
the sources require browsing for every action or another decision record.

- [Google: The standard of code review](https://google.github.io/eng-practices/review/reviewer/standard.html#principles) — technical facts and engineering principles take precedence over personal preference; more than one solution can be valid.
- [Microsoft: Architecture decision records](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record) — context, requirements, constraints, alternatives and consequences explain why a choice fits and whether it still applies.
- [Microsoft: Synapse PoC guidance](https://learn.microsoft.com/en-us/azure/synapse-analytics/guidance/proof-of-concept-playbook-dedicated-sql-pool) — bounded scope, measurable goals, representative data and interpretation of results; its product-specific durations and dataset sizes are not general requirements.
- [AWS: Use benchmarking to drive architectural decisions](https://docs.aws.amazon.com/wellarchitected/latest/framework/perf_architecture_use_benchmarking.html) — workload-relevant baselines, metrics and repeated measurements; benchmarks complement rather than replace load testing.
- [Google: Validate a migration plan](https://docs.cloud.google.com/architecture/migration-to-google-cloud-best-practices#consider_creating_a_proof_of_concept) — small feasibility experiments with explicit success criteria and separation of experimental resources from production; migration-specific procedures are not a universal PoC workflow.
