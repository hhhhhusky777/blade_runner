# Proportional Review

Use this guidance when evaluating findings, proposing corrections, or deciding
an author's disposition. Project authorities own scope, acceptance, review
gates and escalation; this topic does not change them.

## Core principles

> [!IMPORTANT]
> Review for fitness to the accepted outcome and maintainable system health,
> not perfection. Challenge the value and complexity of your own request.
> Authors must assess findings independently, not accept them automatically.
> Use evidence and engineering tradeoffs to fix, reject or defer; neither
> rejection nor deferral waives a mandatory control or critical invariant.

Read the change in its design and system context. Check intended behavior,
contracts, useful evidence and necessary complexity, including material edge,
concurrency and failure risks. A technically possible case is not automatically
an urgent defect, and a real defect is not automatically best solved with a new
framework. Prefer the smallest correction that protects the accepted outcome.

## Finding value and priority

Establish a credible trigger and consequence from the actual candidate and
supported operating domain. Assess exposure and likelihood, impact, urgency,
and the remedy's implementation and maintenance cost. Do not invent numerical
probabilities or treat rarity as impossibility. Low likelihood does not erase
a credible critical security, safety or consistency violation.

Explain why action is needed now, not merely why another approach is possible.
Distinguish mandatory correction from optional improvement or personal taste.
Project standards govern required style; other equally sound choices remain
with the author. Omit low-value polish, or label genuinely useful optional advice
clearly enough that it cannot be mistaken for an approval condition.

Consider whether the proposed remedy removes risk or just transfers complexity
into tests, recovery code, abstractions or operations. A simpler safe failure or
existing mechanism can be better than handling every hypothetical case. Do not
expand accepted scope through a review recommendation.

## Author disposition and convergence

Understand the finding before editing. Accept a necessary correction; reject
an unsupported or disproportionate request with evidence and tradeoffs. Defer
valuable nonblocking work to an owned, linked issue only when current acceptance
and protected boundaries remain satisfied. A promise to fix later is not a
substitute for a required correction, and deferral must not conceal complexity
or regression introduced by this change.

For disagreement, compare the protected outcome and competing approaches,
rather than repeatedly changing code to satisfy preferences. Reviewers should
withdraw a request when the author's evidence shows it is mistaken, or explain
the remaining material concern. Clarify confusing code itself first. When
further clarification is impractical, add a useful comment explaining why the
logic exists. Use a PR-only explanation when a code comment would add no value.

Record the disposition and rationale in the PR. Reopen a settled finding only
when new evidence or changed content invalidates its basis. Escalate unresolved
critical disagreement through existing project authority instead of an endless
review-change loop. Review approval binds to the inspected candidate and does
not supply human acceptance or merge authority.

## Reference-backed examples

These paraphrase Google's published review guidance, not project incidents.

| Reference example | What it reveals | Useful application | Source |
| --- | --- | --- | --- |
| A reviewer suggests a style preference outside the governing style guide | Useful polish is not necessarily a merge condition | Mark it optional rather than block an otherwise sound change | [Google: Review standard](https://google.github.io/eng-practices/review/reviewer/standard.html#principles) |
| An author chose X for explicit pros/cons and thinks Y would worsen the tradeoff | Refusal without reasoning cannot resolve the technical disagreement | Explain the competing costs and ask which accepted outcome Y better serves | [Google: Handling comments](https://google.github.io/eng-practices/review/developer/handling-comments.html#think-collaboratively) |
| A change introduces complexity but the author promises cleanup later; it also exposes unrelated surrounding problems | New regression and existing adjacent debt are different obligations | Correct introduced complexity now; track surrounding work separately when it cannot be addressed here | [Google: Handling pushback](https://google.github.io/eng-practices/review/reviewer/pushback.html#cleaning-it-up-later) |

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty.
Google's organization-specific processes do not replace project authority.

- [Google: Review standard](https://google.github.io/eng-practices/review/reviewer/standard.html) — balance progress with code health; technical evidence outranks preference, and perfection is not required.
- [Google: What to look for](https://google.github.io/eng-practices/review/reviewer/looking-for.html) — design fit, behavior, useful tests, surrounding context and unnecessary complexity.
- [Google: Handling pushback](https://google.github.io/eng-practices/review/reviewer/pushback.html) — reassess a contested request, justify its value and distinguish introduced complexity from adjacent cleanup.
- [Google: Handling comments](https://google.github.io/eng-practices/review/developer/handling-comments.html) — understand the request, improve clarity and resolve disagreement through constructive technical tradeoffs.
