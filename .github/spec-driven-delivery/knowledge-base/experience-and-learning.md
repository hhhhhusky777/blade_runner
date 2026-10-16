# Experience and Learning

Use this guidance when reusing or maintaining project lessons. Experience lets
the next agent recognize a known situation and choose a verified response with
less trial and error. Project authority owns permissions, recovery and changes;
a past success does not establish the cause of a new failure.

## Core principles

> [!IMPORTANT]
> Preserve verified, actionable lessons that materially reduce future effort.
> Search existing experience when unexpected situations arise, check whether
> its conditions still apply, and improve the same lesson as evidence grows.
> Prefer eliminating the underlying problem or codifying its solution in the
> existing owner. Keep only useful residual guidance in Experience.

The shared KB explains the practice; the manifest-linked project Experience or
existing equivalent holds local lessons. Keep it durable and discoverable by
agents without prior conversation. Project policies remain authoritative.

## Reusing a lesson

An unexpected situation or failure is the primary lookup trigger. Search using
the observed symptom and relevant environment before repeating investigation.
Known applicable lessons can also prevent a repeat before related work begins;
this does not require a lookup for every operation.

Compare the entry's conditions with current configuration, versions, inputs
and authority where they affect the result. Similar symptoms can have different
causes. Use the lesson to guide verification, not to skip diagnosis or infer
permission. If the advice no longer fits, preserve that uncertainty and use the
project's existing triage or error-handling guidance.

## Recording useful knowledge

A first verified resolution can qualify; recurrence is not a prerequisite.
Keep a lesson when another agent can use it to avoid meaningful investigation,
mistakes or repeated setup. An environment discovery can be valuable even when
it produces no product-code change. Time spent alone does not establish value;
measured effort or recurrence may support the rationale but must not be invented.

Use the project's existing entry format. Make the recognition signal, relevant
conditions, effective approach, supporting evidence and limits clear. Explain
what a reader should do differently and how to verify the result. Distinguish a
workaround from a verified fix; do not turn a plausible cause into a fact.
Link an existing guide, script, contract or issue instead of copying it. Keep
secrets, raw logs, transient progress and one-off guesses out of durable lessons.

Learning should produce action where justified. Correct or codify a verified
solution within approved scope; track material follow-up through the existing
issue process with an owner and verifiable outcome. A note does not complete
the fix. Avoid prescribing a full postmortem or new automation for every lesson.

## Refinement and ownership

Reuse is review: check accuracy while applying knowledge. Refine an existing
lesson for a verified variation, making its different conditions explicit.
Keep distinct causes separate when combining them would mislead the reader;
do not enumerate hypothetical variants. Reconcile parallel contributions using
their evidence rather than letting the newest edit silently win.

Fix an entry when the correction is verified and authorized. Otherwise flag
what is uncertain and the evidence needed to resolve it. Correct, merge or
retire stale and redundant advice through normal project change controls;
preserve useful links and rely on version history for superseded text.
If a documented problem recurs, examine findability, clarity, changed conditions
and whether the preventive action was completed before adding another entry.

## Reference-backed examples

These paraphrase published examples and guidance, not project incidents.

| Reference example | What it reveals | Useful application | Source |
| --- | --- | --- | --- |
| Similar problem descriptions require different resolutions in different environments | A symptom alone may retrieve the wrong lesson | Record the environment that distinguishes when an approach applies | [KCS: Simple template](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/030/020/010) |
| Two articles describe the same cause and resolution in different words and later appear in the same search | Duplicate knowledge can hide a useful shared lesson | Merge verified content and recognition terms while preserving relevant links | [KCS: Flag It or Fix It](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/030/040/030) |
| Google's poor postmortem example proposes vague improvements and training people to avoid unsafe commands | Recording advice without concrete corrective action can leave the failure mechanism intact | Prefer an owned, verifiable system improvement when justified, with reusable guidance for the remaining conditions | [Google SRE: Postmortem culture](https://sre.google/workbook/postmortem-culture/) |

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty.

KCS describes a support knowledge system with broad capture and its own roles.
This playbook adopts its useful structure, reuse and refinement principles;
project Experience retains the narrower verified, valuable-lesson boundary.
Neither KCS nor SRE examples introduce new roles, quotas or review gates here.

- [KCS: Use a simple template](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/030/020/010) — recognizable issue, relevant environment and effective resolution.
- [KCS: Reuse is review](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/030/040/020) — maintain accuracy in the context of use and shared ownership.
- [KCS: Flag It or Fix It](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/030/040/030) — evidence-informed correction, refinement and useful duplicate consolidation.
- [Google SRE: Postmortem culture](https://sre.google/workbook/postmortem-culture/) — factual learning, concrete preventive action and follow-through; a project lesson need not become a full incident report.
