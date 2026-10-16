# Simple Design and Reuse

Use this guidance when designing or reviewing a solution: satisfy the current
requirement by reusing existing capabilities and introducing the fewest new
responsibilities and mechanisms necessary. This topic concerns design choices,
not coding style or source-level refactoring.

## Core principles

> [!IMPORTANT]
> Reuse suitable existing capabilities and framework mechanisms before adding
> new ones. Extend the existing owner of a responsibility instead of creating
> a parallel owner. Design only for demonstrated current requirements, not
> speculative features or extension points.

## Applying the principles

Identify which existing component or mechanism owns the required behavior and
compare its contract with the current requirement. Prefer configuration,
composition, or a bounded extension when that meets the need without weakening
existing guarantees. Reuse is unsuitable when it crosses ownership boundaries,
changes an unrelated contract, or needs more adaptation than a small coherent
new mechanism.

When proposing a new component, abstraction, dependency, or control, identify
the current requirement that the existing mechanism cannot adequately satisfy.
Weigh its benefit against added coupling, migration, operation, and maintenance
cost. Choose the least costly sufficient alternative, not the smallest diff if
that diff leaves duplicate ownership or fragile integration.

Keep responsibilities clear and changes easy to evolve. Existing extension
points can support change without inventing a generic framework. A new
abstraction is justified by current variation or a concrete responsibility,
not by imagined future formats or consumers. Necessary safety, compatibility,
and verification are part of a sufficient design, not optional complexity.

## Concrete examples and limits

Everyday illustrations below are adapted from the referenced principles, not
reported incidents or quotations. Illustrations of the same principle share a
row rather than introduce another rule.

| Situation | Smallest suitable change | Limit to check | Everyday illustration (adapted) |
| --- | --- | --- | --- |
| Current pricing requirements cover one risk; another risk is only a forecast | Deliver the current pricing capability without speculative future behavior | Fowler's YAGNI example distinguishes postponed speculative capability from maintaining ease of change | Only CSV export is required: support CSV, not a plugin framework for ten hypothetical formats. Unused formats already incur development and maintenance cost |
| Two settings have the same value but represent different concepts | Keep their ownership separate instead of treating equal values as a shared design responsibility | Microsoft's DRY guidance warns against coupling coincidentally similar concepts | Upload size and cache capacity are both 10 MB: keep separate settings so changing the upload limit cannot accidentally change cache capacity |
| Multiple teams maintain overlapping solutions to a demonstrated operational problem | Consider a shared capability with a small contract when reuse benefits exceed extraction and coordination costs | Meta's Shard Manager illustrates justified common infrastructure at actual scale, not early platform building for one hypothetical consumer | — |
| An existing project mechanism already satisfies the required contract | Integrate with that owner rather than create a second implementation | Verify suitability first; reuse must preserve required guarantees | A new API uses the project's suitable authentication middleware instead of reimplementing token validation; one security responsibility avoids divergent implementations |

## Conditional design techniques

Shared capabilities are justified by real common requirements, compatible
contracts, and clear ownership. First reuse what already exists. If extraction
is warranted, expose the smallest useful shared contract; account for migration
and coordination costs. Similar-looking code or imagined future consumers are
not sufficient justification for a new platform.

When replacing an existing system, prefer gradual replacement if a large
cutover would introduce material delivery or operational risk and the behavior
can be separated safely. AWS's Strangler Fig example redirects bounded
capabilities progressively rather than replacing the entire system at once.
Include routing, coexistence, data consistency, and retirement costs in the
comparison. A small safe replacement may be simpler; this technique does not
require microservices, a proxy, or parallel implementations in every project.

These techniques solve different questions: shared capability concerns what
to reuse; gradual replacement concerns how to migrate. They may coexist, but
neither is a required architecture. Use necessary existing evidence to confirm
important design goals; detailed coding, testing, and observability methods
belong to their own topics.

For design review, examine the existing option, the evidenced gap, the proposed
increment, and its total cost. Challenge an addition with a concrete sufficient
alternative; do not demand a universal framework or theoretical perfection.

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty.
Their examples are not additional project requirements.

- [Google: What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) — design fit, integration with existing components, and unnecessary generality.
- [Martin Fowler: YAGNI](https://martinfowler.com/bliki/Yagni.html) — avoid speculative capabilities without neglecting code health or ease of change.
- [Microsoft: Architectural principles](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/architectural-principles) — explicit contracts, responsibility boundaries, and reuse without coupling unrelated concepts; its concrete .NET architecture is not a universal requirement.
- [AWS: Operational excellence design principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html) — small reversible changes reduce delivery risk; cloud-specific mechanisms are contextual.
- [Meta: Scaling services with Shard Manager](https://engineering.fb.com/2020/08/24/production-engineering/scaling-services-with-shard-manager/) — a case of shared infrastructure justified by repeated real operational needs, not a universal platform mandate.
- [AWS: Strangler fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) — gradual replacement and its coexistence, routing, and consistency costs; use only when those tradeoffs suit the project.
