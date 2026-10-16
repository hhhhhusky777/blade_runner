# Code Simplicity and Clarity

Use this guidance when writing, refactoring or reviewing implementation code.
Make intent and behavior easy to understand and change safely. This topic covers
code-level simplicity and clarity; design-level decisions belong to
[Simple Design and Reuse](simple-design-and-reuse.md).

## Core principles

> [!IMPORTANT]
> Prefer explicit intent, straightforward control and data flow, and the
> smallest useful abstraction. Refactoring and code refinement MUST preserve
> existing behavior and business semantics,
> including evaluation order, side effects, errors and concurrency semantics.
> Fewer lines, variables or functions are not evidence of a better solution.

## Making implementation understandable

Choose names that communicate the domain concept or operation at the reader's
level of detail. Follow project conventions; avoid both unexplained shorthand
and names that merely narrate syntax. A reader should understand the operation
without mentally executing its implementation.

Keep related decisions and operations together when they express one coherent
purpose. Extract a function when its name clarifies that purpose and its inputs
and effects remain understandable. Extraction need not wait for duplication;
conversely, splitting every expression into a helper can hide the flow behind
unnecessary navigation. Prefer the boundary that makes the actual code easier
to reason about, not a universal function-size limit.

Use intermediate values when they name a concept, expose a useful stage, retain
a deliberate snapshot or prevent repeated work. Remove aliases that merely
pass a value along without improving meaning. A named query can make a coherent
calculation reusable, but recomputing it may change cost or observations. A local
value can be the clearer and more correct choice.

Consolidate conditions when they express the same decision with the same
outcome and evaluation semantics remain equivalent. Identical-looking checks
are not sufficient evidence: an intervening operation may change their inputs,
or a predicate may have effects. Do not merge distinct responsibilities merely
because their code currently looks similar.

Use abstractions for current concepts and variation, not speculative flexibility.
Keep the necessary behavior visible instead of hiding it behind a generic
framework or clever compression. Comments explain non-obvious reasons,
constraints and tradeoffs; they should not compensate for avoidably confusing
code or repeat its syntax. Complex algorithms may still need an explanation.
Keep relevant comments accurate when changing behavior.

## Behavior-preserving change

Inspect the actual language and project semantics before applying a refactoring.
For the affected behavior, account for short-circuiting, evaluation count/order,
mutable state, exceptions, cleanup and synchronization where relevant. For
example, replacing a saved value with a repeated query is not equivalent if
the underlying state can change between reads.

Add focused regression tests where existing coverage is insufficient to detect
unintended behavior changes from refactoring.
Keep the change within accepted scope rather than bundle unrelated style
cleanup. Review for a concrete improvement in comprehension or maintenance,
not personal preference or the shortest possible expression.

## Reference-backed examples

These paraphrase the published examples. The application limits explain what
to verify in a real project; the transformations are not mandatory recipes.

| Published example | Clarity gained | Application limit | Source |
| --- | --- | --- | --- |
| Invoice printing moves customer and amount output into a named details operation | The caller states the purpose while the helper contains the display detail | Preserve output order and values; avoid helpers that add navigation without meaning | [Fowler: Extract Function](https://refactoring.com/catalog/extractFunction.html) |
| Several disability-benefit checks each return zero; one named eligibility predicate expresses that shared decision | The reader sees the business question rather than reconstructing it from separate conditions | Combine only equivalent outcomes; preserve short-circuiting and effects, not just the final Boolean | [Fowler: Consolidate Conditional Expression](https://refactoring.com/catalog/consolidateConditionalExpression.html) |
| A quantity-times-unit-price calculation becomes a named base-price query used in pricing | The calculation has a meaningful, reusable boundary | A query is not automatically better than a local value: retain a snapshot or cached result when repeat evaluation changes semantics or cost | [Fowler: Replace Temp with Query](https://refactoring.com/catalog/replaceTempWithQuery.html) |

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty. Project
semantics require canonical contracts, code or direct evidence; an external
refactoring example cannot prove equivalence in the current implementation.

- [Google: What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) — comprehensibility, useful names and comments, necessary complexity and nonblocking style preferences.
- [Martin Fowler: Extract Function](https://refactoring.com/catalog/extractFunction.html) — name a coherent operation and separate purpose from detail.
- [Martin Fowler: Consolidate Conditional Expression](https://refactoring.com/catalog/consolidateConditionalExpression.html) — express a shared decision with a meaningful predicate.
- [Martin Fowler: Replace Temp with Query](https://refactoring.com/catalog/replaceTempWithQuery.html) — expose a calculation through a named query; not a ban on local variables.
