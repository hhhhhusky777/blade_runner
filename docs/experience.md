# Project experience

Use this document for verified, reusable lessons that help future work. It is
project guidance, not policy, feature status, or permission to act.

Search relevant entries when an unexpected situation occurs or a known lesson
applies. Recheck their conditions against current code and contracts. Update
the existing entry when evidence changes; link the owning source rather than
copying instructions. Add lessons only after verification. Keep secrets, raw
logs, speculative diagnoses, and delivery progress elsewhere.

| Situation | Effective approach and evidence | Applicability / limits |
| --- | --- | --- |
| A local run appears to prove a legal winning plan | Inspect the action implementation and validate against the game rules; the starter allows negative build balances and omits other checks. See [simulator limits](../README.md#code-limits-and-delivery) and [actions](../game_solver/game_simulation/actions.py). | Applies to the supplied Stage 1 starter. Recheck after changes; no server equivalence has been demonstrated. |
| Choosing between practice and progression commands | Use the [documented commands](../README.md#setup-and-commands): `tasks` lists existing tasks; `solve-task` asks before submission unless `--auto-submit` is used; `advance` can create a task and submits automatically. See [CLI implementation](../game_solver/main.py). | Reading an existing task does not reset its creation deadline. Confirm behavior if the CLI or server contract changes. |
