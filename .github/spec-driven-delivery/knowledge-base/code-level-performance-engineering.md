# Code-Level Performance Engineering

Use this guidance when writing or reviewing performance-sensitive code, or
choosing an implementation improvement for a demonstrated cost. Design-level
goals, measurement and whole-system trade-offs belong to
[Performance and Observability](performance-and-observability.md);
implementation readability belongs to
[Code Simplicity and Clarity](code-simplicity-and-clarity.md).

## Core principles

> [!IMPORTANT]
> Reduce avoidable work around the accepted operation, not necessary guarantees.
> Connect the code choice to its actual cost and choose the smallest suitable
> change using existing language, library and runtime capabilities. Preserve
> ownership, lifetime, consistency and accepted behavior; a lower local cost
> does not justify breaking them.

The five mechanisms below are an editorial organization, not an exhaustive
hardware taxonomy or optimization checklist. Follow the relevant execution
path to the code producing the cost: repeated calls, data traversals, allocation
sites, shared updates or I/O requests. Use the project's evidence and the
design-level guidance to decide what matters. Do not infer a bottleneck merely
from a keyword or require low-level tuning for every feature.

## Computation and instruction execution

Repeated parsing, conversion or calculation can spend more time preparing an
operation than doing useful work. Reuse a prepared result when its inputs and
validity are stable; use a simpler existing operation when it expresses the
same semantics. Inspect the algorithm and data structure before tuning individual
instructions. A table lookup can trade arithmetic for memory access rather
than eliminate cost; cached results also need a valid lifetime.

When evidence points to instruction execution, consult the target compiler's
optimization reports and official guidance before choosing vectorization or
other target-specific techniques. Dependencies, aliasing and numerical semantics
limit legal transformations; source-level cleverness need not improve generated
code. [Google's RE2 guidance](https://abseil.io/fast/21),
[microbenchmark cautions](https://abseil.io/fast/39) and
[LLVM's vectorizer documentation](https://llvm.org/docs/Vectorizers.html)
show these different questions; none requires adopting those tools.

## Data movement and access

Copies, pointer chasing and fetching unused fields consume bandwidth and can
delay useful work. Inspect where values are copied or materialized and how a
loop traverses them. Where ownership and lifetime permit, construct data in its
destination, use an existing view, or traverse a layout that keeps needed data
close together. Contiguous or compact storage helps only when its access pattern
and semantics fit; pointer stability or independent ownership may justify a copy
or indirection. See [Google's memory-bandwidth guidance](https://abseil.io/fast/62).

Do not treat every transfer as the same problem. Register spills are
compiler-inserted memory accesses when values cannot remain in available
registers, not thread context switches. Inspect generated code and target
constraints before changing live ranges or unrolling; consult
[LLVM's register-allocation documentation](https://llvm.org/docs/CodeGenerator.html#register-allocation).
For cross-core interference, [Linux's false-sharing guidance](https://docs.kernel.org/kernel-hacking/false-sharing.html)
explains how independent fields on one cache line can still interfere when
written. Padding or separating data trades locality and space for less
interference; it is not a universal layout rule.

## Resource creation and reclamation

Repeated allocation, initialization and teardown add work; managed runtimes may
also pay collection costs. Inspect allocation frequency, object size and
lifetime. Avoid an unnecessary intermediate object before adding a pool.
Where size is known, suitable preallocation can avoid repeated growth; existing
small-buffer, buffer-reuse or connection-management facilities may amortize
setup. Reuse must retain the correct ownership, reset and release behavior.
Unused capacity, retained memory and coordination can outweigh the saving.
Use [Google's allocation examples](https://abseil.io/fast/83) and the actual
runtime's guidance, such as [ASP.NET Core's allocation guidance](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/best-practices#minimize-large-object-allocations),
and [ObjectPool trade-offs](https://learn.microsoft.com/en-us/aspnet/core/performance/objectpool),
rather than invent an allocator or pool for hypothetical demand.

## Scheduling, synchronization and coordination

Tiny tasks, repeated handoffs and frequent shared writes can make coordination
larger than the work performed. Inspect task granularity and the actual shared
state. Keep suitable work local and combine results when required ordering,
visibility and numerical behavior permit it. More workers do not create more
CPU or memory bandwidth; partitioning and synchronization also cost time.
[Microsoft's parallelism pitfalls](https://learn.microsoft.com/en-us/dotnet/standard/parallel-programming/potential-pitfalls-in-data-and-task-parallelism)
explain why cheap or dependent work may be better left sequential.

For I/O waiting, use an appropriate existing asynchronous API when the runtime
and dependency support it. It can release a thread to serve other work; it does
not remove CPU computation. Moving blocking I/O onto another worker can merely
add a handoff. [ASP.NET Core's blocking-call guidance](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/best-practices#avoid-blocking-calls)
illustrates this distinction. Preserve synchronization and cancellation
semantics; a contention symptom is not permission to remove a required lock.

## I/O and access amplification

One logical operation may induce many requests, transferred fields, block reads
or rewrites. Inspect the request loop, query plan and storage behavior rather
than equate a small response with little work. Fetch the required data without
unnecessary columns or repeated round trips using existing query/batch APIs.
[Microsoft's query examples](https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying)
show both projection and the extra per-record requests caused by lazy loading.
Preserve complete required results and transaction semantics; fewer queries can
still transfer more duplicate data.

Batching amortizes per-request costs but can add waiting and memory use; fit
size and delay to accepted latency and partial-failure behavior. See the
interaction of `batch.size` and `linger.ms` in
[Kafka's producer configuration](https://kafka.apache.org/41/configuration/producer-configs/),
not a universal batch size. Storage read/write amplification is a different
cost: [RocksDB's tuning guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide#amplification-factors)
relates logical operations to device work and explains read/write/space
trade-offs. Metadata, compaction and recovery records may serve necessary
guarantees; an amplification factor alone does not prove removable waste.

## Reference-backed examples

These paraphrase published examples. The application limits are our bounded
interpretation, not mandatory replacements or promised speedups.

| Published example | Avoidable cost and useful change | Application limit | Source |
| --- | --- | --- | --- |
| The same RE2 pattern is passed as a string on repeated matches | Each temporary RE2 object parses and compiles the pattern; reuse a suitably prepared expression | Pattern validity, lifetime and concurrency behavior must permit reuse; this is not a mandate for a new cache | [Google: RE2 object churn](https://abseil.io/fast/21#minimise-re2-object-churn) |
| A temporary protobuf submessage is populated, then copied into its parent | Populate the final submessage directly to avoid the temporary and deep copy | Ownership, visibility and failure behavior must allow in-place construction | [Google: Minimize copies](https://abseil.io/fast/62#minimize-copies) |
| A short-lived vector normally holds only a few pointers | An existing inline-capacity container avoids common small heap allocations while supporting larger inputs | Choose capacity from actual sizes; preserve larger-input support and account for increased object size | [Google: Reducing memory indirections](https://abseil.io/fast/83) |
| A parallel loop sums integers with local subtotals and a synchronized final addition | Shared-state coordination occurs at subtotal completion rather than every element | The reduction must preserve required arithmetic and visibility; not a replacement for an immediately consistent shared counter | [Microsoft: Thread-local loop state](https://learn.microsoft.com/en-us/dotnet/standard/parallel-programming/how-to-write-a-parallel-for-loop-with-thread-local-variables) |
| A read-only query prints blog URLs but fetches every column of each blog | Project only the URL to avoid transferring and materializing unused properties | Other consumers or entity updates may require more data; do not truncate the accepted result | [Microsoft: Project needed properties](https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying#project-only-properties-you-need) |

## References

For [Solution Research](solution-research.md), start from the cost mechanism
and project constraints, not a technique name. The sources above illustrate
comparable problems; follow relevant official language, compiler, runtime,
library or storage documentation for the project's actual version. For example,
unnecessary data movement motivates investigating ownership and copy costs;
zero-copy is only one candidate, not a conclusion implied by this topic.

These sources expose particular implementations. Their APIs, counters and
tuning settings are not portable defaults. Use the shared design-level
performance boundaries to evaluate the resulting change; this topic adds no
test schedule, permission or optimization gate.
