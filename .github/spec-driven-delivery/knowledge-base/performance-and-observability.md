# Performance and Observability

Use this guidance during solution and system design, when investigating
bottlenecks, and when choosing feedback about runtime behavior or important
design properties. Design observability so relevant behavior is measurable
and interpretable: evidence should support decisions and improvement, not just
populate dashboards. This topic covers design-level choices and feedback, not
a catalog of code-level optimization techniques. Failure localization and recovery
belong to [Error Handling and Diagnosability](error-handling-and-diagnosability.md).

## Core principles

> [!IMPORTANT]
> Design for measurable, interpretable feedback about accepted outcomes.
> Choose the simplest sufficient improvement within project boundaries;
> more telemetry or a faster isolated benchmark is not itself an improvement.

These five boundaries consolidate the linked sources for this KB; they are
not a claimed industry-standard taxonomy or a prescribed optimization sequence.

| Boundary | Design judgment | Primary basis |
| --- | --- | --- |
| Useful outcomes | Improve the accepted operation and useful work per resource cost. A proxy metric can help explain behavior but cannot alone establish the intended gain | [Google: Application productivity](https://abseil.io/fast/7) |
| Evidence | Design how relevant behavior will be measured and interpreted; use representative evidence to locate limiting work and assess improvement claims | [Microsoft: Performance design](https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/principles) |
| Unnecessary work | Prefer removing avoidable processing or supporting work over adding a more elaborate mechanism. Supporting work may still be necessary for correctness or lower total cost | [Google: Optimizing optimization](https://abseil.io/fast/72) |
| Whole-system trade-offs | Preserve accepted correctness and behavior; assess latency, throughput, resource use and effects on other operations. A local cost increase may still improve the whole system | [Google: Application productivity](https://abseil.io/fast/7) |
| Proportional complexity | Expected benefit must justify implementation, operation and maintenance cost. Reuse suitable mechanisms and signals; do not chase theoretical optimality or add a monitoring platform without a demonstrated need | [Google: Optimizing optimization](https://abseil.io/fast/72), [Microsoft: Performance design](https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/principles) |

## Meaningful performance evidence

During design, identify the relevant operation, accepted target and how its
behavior can be measured. Use available evidence and distinguish estimates or
unmeasured properties from observed results. Considering performance early does
not require a full test run or fine-grained optimization during design.
Define what is measured, for which workload and over what interval. Choose
relevant latency, throughput, error or resource measures rather than every available metric.
Separate successful and failed requests where mixing them would hide poor
service. Tail latency can expose slow users that an average conceals; no
universal percentile or threshold follows from this guidance.

Establish a baseline under representative data, concurrency, traffic patterns
and environment. Profile or inspect existing evidence to locate the limiting
work before proposing an optimization. Compare the candidate with that
baseline under comparable conditions, accounting for variability. Disclose
synthetic data, omitted dependencies or scale differences that limit the claim;
a local microbenchmark does not establish production performance.

Retain evidence sufficient to explain the decision, not a second
performance-reporting system. Project authority still controls
test timing, production access and acceptable load; this topic creates no new
validation gate or permission to experiment on live users.

## Useful signals and feedback

Choose signals for the question being answered. Metrics describe aggregate
behavior over time; logs record events and context; traces connect operations
across a request's path. Correlation can explain where time goes, but not every
project or question needs all three. Reuse the project's instrumentation and
analysis tools before adding another mechanism.

Connect collected evidence to an interpretation and useful action: assess a
goal, locate expensive work, compare a change or detect meaningful degradation.
Choose resolution, retention and collection volume proportionate to that need
and the cost of observing the system. Avoid unused signals and noisy alerts;
an alert should support an actionable response, not merely report that a metric
changed. Preserve project privacy and security boundaries in telemetry.

## Architectural fitness evidence

Architectural fitness means evidence that a change preserves an important,
accepted design property. Where that property warrants it, use an existing
metric, test or analysis to make degradation visible. For example, a dependency
check can expose a cycle that violates an agreed module boundary.

Assess only the property the evidence actually covers. A static dependency
check does not prove runtime correctness or performance. Prefer a suitable
existing mechanism; this is not a requirement to adopt evolutionary architecture,
install an architecture-testing framework or create a test for every design
preference. Design authority determines the boundary being evaluated.

## Reference-backed examples

These paraphrase published examples. The application limits are our bounded
interpretation, not universal tool choices or new project requirements.

| Published example | Useful feedback | Application limit | Source |
| --- | --- | --- | --- |
| A service uses more CPU while processing more videos | Work completed per CPU-second distinguishes higher demand from lower efficiency; CPU use alone cannot | Choose the useful-work unit for the actual service; a lower resource counter is not automatically a better outcome | [Google: Application productivity](https://abseil.io/fast/7) |
| A service averages 100 ms at 1,000 requests per second, while 1% take 5 seconds | The average hides ten slow requests each second; the latency distribution reveals them | Choose a meaningful tail measure and target for the actual operation, not these illustrative numbers | [Google SRE: Latency distributions](https://sre.google/sre-book/monitoring-distributed-systems/#worrying-about-your-tail-or-instrumentation-and-performance-Yms9Ck) |
| An orders-table index is evaluated against the original schema under the same load | Query latency, CPU and throughput test whether the proposed optimization helps | The stated improvement is a hypothesis, not a promised result for another database or workload | [Microsoft: Performance testing](https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/performance-test) |
| A webpage request crosses an API gateway, backend and database, with spans in one trace | The connected path supplies context that isolated events lack | Instrument only the relevant path within project authority; this does not require OpenTelemetry adoption | [OpenTelemetry: Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/#distributed-traces) |
| ArchUnit groups Java classes by package and checks those groups for dependency cycles | An executable check can reveal erosion of an accepted acyclic-module constraint | Covers the selected classes and dependencies, not overall architecture quality; keep an existing suitable module mechanism | [ArchUnit: Slices](https://www.archunit.org/userguide/html/000_Index.html#_slices) |

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty. Actual
workloads, targets and bottlenecks require canonical project sources or direct
evidence; an external benchmark or example cannot establish them.

- [Google: Application productivity](https://abseil.io/fast/7) — useful work per resource cost and whole-application effects instead of isolated proxy improvements.
- [Google: Optimizing optimization](https://abseil.io/fast/72) — expected benefit, total engineering effort, reuse and measurement; its experimental shortcuts do not waive project correctness boundaries.
- [Microsoft: Performance Efficiency design principles](https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/principles) — performance from design onward, whole-system trade-offs and proportionate evidence; cloud-specific mechanisms and test gates are not additional project requirements.
- [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) — user-relevant measures and targets rather than arbitrary numbers or every available metric.
- [Google SRE: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) — meaningful signals, latency distributions and proportionate, actionable monitoring.
- [Microsoft: Performance testing](https://learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/performance-test) — representative workloads, baselines and hypothesis-driven comparison; its test schedules do not replace project authority.
- [OpenTelemetry: Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/) — the different questions metrics, logs and traces help answer; no telemetry platform mandate.
- [Thoughtworks: Building Evolutionary Architectures, second-edition excerpt](https://www.thoughtworks.com/content/dam/thoughtworks/documents/books/bk_building_evolutionary_architectures_second_edition_free_chapter.pdf) — proportionate architecture effort and feedback on important design characteristics, especially printed pages 4–5.
- [ArchUnit: User Guide](https://www.archunit.org/userguide/html/000_Index.html) — a concrete dependency-cycle example in sections 4.7 and 8.2; section 8.3 retains suitable existing module systems.
