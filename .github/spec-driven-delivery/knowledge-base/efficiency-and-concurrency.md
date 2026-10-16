# Efficiency and Concurrency

Use this guidance when overlapping execution or delegating independent work.
Reduce avoidable waiting without increasing coordination, conflicting changes,
or unverified results. Project authority owns scope, permissions, dependencies
and quality gates; parallel execution does not change them.

## Core principles

> [!IMPORTANT]
> Overlap useful independent work when its inputs are ready and its resources
> do not interfere. Delegate bounded work only when the expected benefit
> exceeds briefing, coordination and integration cost. More agents are not
> inherently better. The parent remains responsible for the integrated result.

Distinguish two opportunities: an agent can overlap its own commands and work,
or delegate independent reasoning or implementation. A simple command does
not need another agent. Tightly coupled work can be faster and safer locally.

## Overlapping execution

Use resumable background sessions when supported for long-running commands,
then advance useful work that does not consume their unfinished results.
Independent checks can run together only when files, generated outputs, data,
services and machine resources are isolated or safely shared. Running two
checks against a shared mutable fixture is not independent work.

Collect each command's exit status and relevant evidence before relying on its
result. Keep results bound to their actual inputs and candidate; overlapping
an edit with a check does not prove the edited candidate passed. Diagnose a
failed check through existing project error handling. Wait when dependencies,
resource contention or the absence of useful safe work require it; do not
manufacture busywork merely to avoid waiting.

## Delegation and integration

Delegate a bounded outcome that can be completed independently and verified
on return. Supply canonical source entry points, relevant design or task
outcomes, exact inputs or candidate, ownership and authority boundaries, and
the expected result and evidence. Return useful conclusions and references
rather than a raw stream of intermediate output.

Keep global requirements, cross-task tradeoffs, coordination, integration and
final verification with the parent. Continue the independent mainline while
workers run. Avoid duplicate investigation and overlapping writes; use explicit
ownership or isolated workspaces for write-heavy work. Delegation is not
permission to expand scope, operate a shared resource or bypass independent
reviewer creation requirements.

Reassess the benefit when briefing becomes substantial, shared context changes
rapidly, or worker outputs require expensive reconciliation. Prefer less
coordination when it achieves the same accepted result. Judge efficiency by
useful verified delivery, not agent count or activity alone.

## Reference-backed examples

These paraphrase published examples. Their application depends on project
boundaries, not a mandatory agent configuration.

| Reference example | What it reveals | Useful application | Source |
| --- | --- | --- | --- |
| Codex delegates code-review analysis for security, test gaps and maintainability | Read-heavy investigations can be separated without competing edits | Give each worker a bounded question and the same exact candidate; the parent reconciles findings | [OpenAI: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents#triggering-subagent-workflows) |
| Anthropic evaluates different aspects of a model response in separate calls | Independent aspects can receive focused attention concurrently | Split evidence gathering only where results can be combined without hidden dependencies | [Anthropic: Parallelization](https://www.anthropic.com/engineering/building-effective-agents#workflow-parallelization) |
| Anthropic researches board members across multiple companies in parallel | Breadth-first research benefits from distinct search domains | Divide independent source investigations, then verify and synthesize their results rather than duplicate searches | [Anthropic: Research system](https://www.anthropic.com/engineering/multi-agent-research-system) |

## References and maturity

Dependency-aware execution and explicit ownership are established engineering
principles. Multi-agent orchestration is evolving practice: published research
results do not establish universal coding speedups or justify a fixed agent
quota.

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty.

- [OpenAI: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) — bounded parallel work, summarized results, token cost and caution with simultaneous edits.
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — independent parallel work and dynamic orchestrator-worker decomposition; choose the simplest sufficient approach.
- [Anthropic: Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — delegation context, proportional effort and coordination limits; research-domain results are not a coding guarantee.
