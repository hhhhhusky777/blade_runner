# Testing and Reproduction

Use this guidance when choosing test evidence, reviewing its value, or
reproducing a failure. The project's testing and delivery authorities own
required gates, execution timing and acceptance; this topic adds no suite or quota.

## Core principles

> [!IMPORTANT]
> Test accepted behavior and material risks, not implementation trivia or
> coverage numbers alone. Prefer the smallest reliable evidence that can detect
> the relevant defect. Preserve the conditions that cause a failure before
> simplifying its reproducer. A successful retry is not proof that the defect
> is fixed; do not weaken required assertions to obtain a green result.

Choose evidence from the outcome and supported operating domain. Keep essential
critical-path proof, then emphasize applicable boundaries, errors and recovery,
concurrency, timing, ordering and interface contracts. Do not enumerate every
imagined interleaving or duplicate happy-path cases without additional value.
For a reproducible defect, a failing regression before a behavior change helps
establish that the later fix addresses the original problem, when practical.

## Useful and proportionate tests

Assert observable results at the owning contract. Keep setup, the operation,
and expected outcome easy to distinguish; use minimal inputs and independently
known expectations rather than reproducing production logic in the test.
Do not couple tests to private helpers or incidental structure unless that
structure is itself an accepted contract.

Use lower-level deterministic checks where they prove the behavior, and real
integration or end-to-end evidence where interactions cannot be shown locally.
Representative end-to-end smoke and production-like concurrent system or load
tests matter when the actual business, scale or shared-state risk warrants them.
Mocks can isolate unrelated dependencies but must not remove the behavior or
failure mechanism the test is meant to exercise. No fixed test-pyramid ratio
or new testing framework follows from these principles.

Coverage can reveal unexercised code, but execution without a meaningful
assertion is not correctness evidence. Evaluate whether tests would detect the
relevant wrong result, not just whether they reach the changed lines. Reuse
existing harnesses and fixtures before adding machinery. Separate evidence
design from run scheduling; follow the project's focused/final validation
boundary without claiming that missing or unrun tests passed.

## Faithful reproduction

Record expected and observed behavior, the exact relevant revision and
environment, and the smallest cause-bearing input or sequence. Preserve
configuration, permissions, state, scale, ordering or concurrency when they
affect the failure. Sanitize secrets and make setup/reset repeatable without
corrupting real data. Reduce the case only while the same failure remains;
do not mock away its suspected cause.

For an intermittent failure, preserve runs, failures and material conditions.
One passing run cannot establish absence. Inspect shared state, test ordering,
isolation and teardown before adding retries or sleeps. Where timing or races
matter, prefer controlled events or scheduling to arbitrary delays; account for
instrumentation altering the behavior. An unreproduced failure remains uncertain,
not disproved.

Verify a remedy against the original failure and affected invariants. When broad
testing discovers a defect, add the smallest deterministic regression at the
lowest useful layer when practical. Preserve failed evidence and distinguish
cause, mitigation and verified fix. Causal investigation and operational
permission remain with the project's triage and error-handling authorities.

## Reference-backed examples

These paraphrase source examples and observations, not project incidents.

| Reference example | What it reveals | Useful application | Source |
| --- | --- | --- | --- |
| A parser calls a private trimming helper | A helper returning the right value does not prove the caller uses it correctly | Verify the trimmed result through the parser's public operation | [Microsoft: Validate private methods with public methods](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices#validate-private-methods-with-public-methods) |
| A discount depends on whether the real calendar says Tuesday | Tests can pass or fail solely because the execution day changed | Use an existing controllable time seam to exercise both supported outcomes deterministically | [Microsoft: Handle stub static references with seams](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices#handle-stub-static-references-with-seams) |
| Tests pass sequentially but fail when run in parallel | A test may rely on another test's data or cleanup order | Identify and isolate the relevant shared state; repair fixtures rather than rerun until green | [pytest: System state](https://docs.pytest.org/en/stable/explanation/flaky.html#system-state) |

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty.
Reference techniques serve project requirements, not extra approval gates.

- [Google: Testing overview](https://abseil.io/resources/swe-book/html/ch11.html) — behavioral confidence, useful test sizes, failure testing and coverage limitations. Google's scale and test-distribution choices are contextual, not universal targets.
- [Microsoft: Unit-testing best practices](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices) — clear behavior, minimal setup, observable assertions and controllable dependencies. Its .NET syntax and naming conventions are examples, not cross-project mandates.
- [Chromium: Bug-reporting guidelines](https://www.chromium.org/for-testers/bug-reporting-guidelines/) — expected behavior, sufficient reproduction details and simplified test cases. Its browser-specific reporting process is not a project requirement.
- [pytest: Flaky tests](https://docs.pytest.org/en/stable/explanation/flaky.html) — uncontrolled state, ordering, teardown and timing. Framework-specific helpers and optional mitigation techniques do not waive the project's acceptance rules.
