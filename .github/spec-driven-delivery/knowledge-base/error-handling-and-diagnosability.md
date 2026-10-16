# Error Handling and Diagnosability

Use this guidance when designing failure behavior, deciding whether an operation
can be retried, or making a failure diagnosable. The project's error-handling
authority owns classification, recovery permission, issue tracking and escalation.

## Core principles

> [!IMPORTANT]
> Keep handling simple and invariant-based, not an enumeration of every edge
> case or interleaving. Preserve consistency; fail closed when continuing could
> violate a required invariant. Permit client-controlled retry only when its
> effects are safe. Make failures identifiable and locatable without exposing
> secrets or hiding the original cause.

Choose the smallest handling that protects the accepted outcome. Reuse existing
transaction, idempotency, cleanup and error-reporting mechanisms before adding
recovery state or orchestration. A failure must not be reported as success;
partial effects and uncertain outcomes need honest contract meaning.

## Safe recovery and retry

A timeout says the caller stopped waiting, not that the operation had no effect.
For an uncertain write, use the owning contract's idempotency guarantee or
reconcile authoritative state before repeating it. An identical payload does
not by itself establish the same intent. Do not invent duplicate detection or
compensation outside the component that owns the effect.

Separate a transient failure from an input, permission or policy problem that
requires a change before another attempt can succeed. Expose a stable outcome
and useful next action through the existing error contract. Returning a
retryable error is often sufficient; it does not require server-side retry
orchestration.

Where automatic retries are already justified, reuse the established client
policy and bound attempts and elapsed time. Consider load amplification and
retry ownership across layers; backoff and jitter help only when retry itself
is safe and useful. No fixed retry count, timeout, circuit breaker or universal
recovery framework follows from this guidance.

## Useful failure evidence

At the appropriate failure boundary, preserve enough evidence to identify the
failed operation, its stage or component, the error category, and the affected
request or run. Reuse structured logs, stable unambiguous error codes,
correlation identifiers, exception causes or traces as appropriate. Human
messages explain what happened; machine decisions use the established typed
error contract, not fragile parsing of prose.

Separate client-safe information from internal diagnosis. Redact secrets and
sensitive payloads; retain useful causal context in authorized diagnostics.
Record an error where that context is available, avoiding duplicate reports of
the same propagated exception or labeling a successfully handled condition as
an operation failure. This is not a mandate to log every branch or install a
telemetry stack. Reuse existing evidence before adding instrumentation.

Review whether the failure can be located, its resulting state understood, and
the smallest safe next action determined. Detailed causal investigation belongs
to the project's triage guidance; broader performance feedback is a separate
concern. New failure behavior remains subject to accepted design and authority.

## Reference-backed examples

These paraphrase the named references, not project incidents or mandatory designs.

| Reference example | Risk or diagnostic distinction | Smallest sufficient application | Source |
| --- | --- | --- | --- |
| An EC2 singleton launch receives no response | Retrying can create a second instance if the first request took effect | Use the API's established request-token guarantee or reconcile the original effect | [AWS: Retrying and side effects](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/#Retrying_and_side_effects) |
| Five service layers each make three attempts on a failed downstream request | Attempts multiply to 243 at the database | Avoid independent retry multiplication; use the appropriate existing retry owner | [AWS: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| A create-if-absent operation handles an already-existing resource | The handled condition is not an operation failure | Preserve relevant context without falsely reporting failure or duplicating a propagated exception | [OpenTelemetry: Recording exceptions](https://opentelemetry.io/docs/specs/semconv/general/recording-errors/#recording-exceptions) |

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty.
Use these sources within project authority, not as permission for new controls.

- [AWS: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) — ambiguous effects, caller intent and established idempotency contracts; its service implementation is not a compulsory recipe.
- [AWS: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) — bounded retry, amplification and load-aware timing; choose measures from actual dependency behavior.
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html) — stable problem identity, occurrence context, actionable client detail and security limits. It specifies an HTTP format, not a required replacement for an existing error contract.
- [OpenTelemetry: Recording errors](https://opentelemetry.io/docs/specs/semconv/general/recording-errors/) — contextual classification and useful, nonduplicated failure evidence. These conventions are marked Development; their evolving instrumentation details are not a universal logging mandate.
