# Contracts and Compatibility

Use this guidance when defining, consuming, or changing an interface. Preserve
the behavior promised to supported consumers, not merely the shape of a message.

## Core principles

> [!IMPORTANT]
> Make the owning contract explicit. Evaluate changes against supported
> consumers and their observable behavior, including defaults and failures.
> Prefer the smallest compatible change; a breaking change needs the project's
> accepted migration or versioning decision, not an agent-created exception.

Use the project's existing contract owner—such as an API specification,
library interface, event schema, or documented command—to establish inputs,
outputs, preconditions, effects, and failure meaning. Record only what the
change materially needs. Do not create a parallel specification or expose
implementation details as promises.

Compatibility has several dimensions: existing code may need to compile,
messages must remain interpretable, and the resulting behavior must still meet
the supported consumer's expectations.

## Applying a change

Determine which consumers and version combinations the project supports.
An independently deployed public API and a private interface whose callers
are updated together need different migration measures. Do not invent support
for every historical version or assume that all consumers update together.

Assess changes in each direction: what old consumers send or read, and what
new consumers require from old producers. Additive fields are not automatically
safe: required inputs, unknown-value handling, defaults, serialization, and
observable effects can change behavior without removing an existing field.

Preserve established behavior when omitted new inputs are intended to keep
old callers working. When a change is genuinely incompatible, use the owning
project's approved transition, update affected consumers and documentation,
and make any coexistence or retirement boundary explicit. Do not add a second
versioning mechanism when an existing one suffices.

Use focused evidence at the contract boundary for the affected supported
combinations and behavior. Reuse existing fixtures, consumer checks, or
integration tests; compatibility does not require a new test framework or an
exhaustive combination matrix.

## Reference-backed examples

These paraphrase examples in the named sources, not project incidents.

| Reference example | Compatibility consequence | Smallest sufficient response | Source |
| --- | --- | --- | --- |
| An API previously returns all items, then adds pagination with a smaller default page | Old callers can mistake a partial page for the complete result | Preserve the supported old behavior or obtain an accepted transition; a new optional field alone is not proof of compatibility | [Google AIP-180: Adding components](https://google.aip.dev/180#adding-components) |
| A customer response gains a creation-date field | It can remain compatible when existing clients ignore unknown fields | Verify that property for supported consumers; retain their existing fields and meaning | [Microsoft: No versioning](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#no-versioning) |
| A customer's address changes from a string to a structured object | Existing clients expecting a string can break | Use the project's accepted incompatible-change strategy; Microsoft's separate-version illustration is one option, not a universal requirement | [Microsoft: URI versioning](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#uri-versioning) |

For review, compare the promised behavior before and after the change, including
affected consumers, defaults and failures. Distinguish an actual supported
consumer break from a hypothetical dependency outside the accepted domain.
Unresolved material authority follows the project's existing decision and
error-handling boundary; this topic introduces no new rejection mechanism.

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty.
These sources inform application; project authority owns the supported domain
and acceptance.

- [Google AIP-180: Backwards compatibility](https://google.aip.dev/180) — source, wire, and semantic compatibility; defaults and additive changes. Its detailed rules assume public APIs and particular transport formats, not every private interface.
- [Microsoft: Web API design](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#implement-versioning) — consumer impact, compatible additions, and versioning tradeoffs. Its REST examples do not prescribe a universal protocol or versioning scheme.
