# Security Basics

Use this guidance when designing or reviewing a change that affects trust,
access, sensitive data, or exposure. Project security and ownership authorities
define the applicable requirements; this topic adds no policy suite or approval gate.

## Core principles

> [!IMPORTANT]
> Protect actual assets and trust boundaries with the smallest sufficient
> controls. Verify identity and permission at the enforcing boundary; neither
> authentication nor an internal location alone grants access. Limit privilege,
> exposure and blast radius. Reuse suitable maintained platform protections
> rather than inventing security machinery. Proportionality does not excuse a
> credible critical violation or an existing mandatory requirement.

Identify the changed assets, actors, data flows and privileges. Assess credible
misuse from the real operating environment and its consequences, including
confidentiality, integrity and availability. Prioritize material exposure;
do not enumerate every hypothetical attack or import a complete enterprise
security program into a bounded task. Add defense in depth where failure of a
primary control would create unacceptable impact, not by duplicating the same check.

## Access and input boundaries

Authentication establishes identity; authorization determines the permitted
action on the particular resource. Enforce access at the trusted server or
owning service, consistently across relevant entry points. Client controls and
unguessable object identifiers do not replace that decision. Deny protected
access without a valid grant, and preserve that boundary when checks fail.
Use the project's existing authorization mechanism before creating another.

Keep untrusted data separate from executable instructions. Use the execution
environment's supported safe APIs and context-appropriate handling; input
validation alone does not establish that separation. Reuse existing safe
interfaces rather than inventing a universal escaping helper.

## Sensitive data and operational exposure

Use the project's approved secret store and access mechanism. Do not commit
credentials or expose them in logs, examples or review evidence. Limit access
and lifetime to the operation's needs; use existing short-lived identity and
rotation capabilities when suitable. An exposed credential requires authorized
revocation or rotation; deleting its visible copy does not invalidate it.
Keep evidence useful without disclosing secret values.

Protect sensitive data across its actual lifecycle with established platform
mechanisms. Account for deployment configuration and dependency provenance,
not just application code. Reduce unnecessary endpoints, privileges and data
retention; evaluate changed dependencies and known vulnerabilities in the
project's security process. Do not build another scanner or cryptographic
implementation where a suitable maintained mechanism exists.

Verify the affected security boundary with proportionate evidence: permitted
behavior still works, and relevant unauthorized access or unsafe input cannot
bypass the control. Use existing tests and tooling at the project's prescribed
execution boundary. Recovery and incident authority stay with the project's
error-handling policy; this document grants no permission to alter live access
or rotate credentials.

## Reference-backed examples

These paraphrase source examples, not project incidents or mandatory frameworks.

| Reference example | What it reveals | Useful application | Source |
| --- | --- | --- | --- |
| A user changes the account ID in a transaction URL | A valid login does not authorize access to another account; hiding IDs is insufficient | Check permission for the requested account at the owning service | [OWASP: Lookup IDs](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#ensure-lookup-ids-are-not-accessible-even-when-guessed-or-cannot-be-tampered-with) |
| A username contains SQL-looking text | Concatenation can turn data into query instructions | Bind the value so it is treated as a literal username, not SQL | [OWASP: Prepared statements](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html#safe-java-prepared-statement-example) |
| Moving a web app to stored procedures leads it to run as database owner | A supposedly safer mechanism can widen privilege and breach impact | Grant only the required execution/data privileges; assess the whole control, not its label | [OWASP: Stored-procedure risk](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html#when-stored-procedures-can-increase-risk) |

## References

If the method or applicability is uncertain, confidence is low, or a material
engineering claim lacks support, you MUST read the relevant sources below.
Guesses and unsupported assumptions do not resolve that uncertainty.
Technology-specific techniques serve project requirements, not extra gates.

- [Microsoft: Security design principles](https://learn.microsoft.com/en-us/azure/well-architected/security/principles) — explicit trust, least privilege, blast-radius containment and business-aware protection. Azure services and enterprise processes are contextual, not universal project requirements.
- [OWASP: Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) — resource-specific access, server-side enforcement and safe failure. Its access-control-model preferences do not mandate replacing a suitable project model.
- [OWASP: SQL injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) — separate instructions from values and assess privilege implications. SQL mechanisms do not automatically protect other interpreters.
- [OWASP: Secrets management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) — restricted access, credential lifetime, exposure response and established management capabilities. Its architecture examples are options, not a requirement for another secret platform.
