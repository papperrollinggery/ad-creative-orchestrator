# Codex Thread Operations Reference

Read this file before any Thread planning, dispatch, observation, receipt reconciliation, adoption, rescue, or cleanup.

## Decision and budget

Default decision: no Thread. A same-task internal second opinion stays on the
Content Surface and can be returned read-only in the current conversation; it is
not a dispatch reason. Use the minimum bounded worker/reviewer only when the user
explicitly requests isolation/parallel execution, genuinely independent work must
proceed concurrently, or an exact client-visible version needs a separately bound
review receipt.

```text
default max active worker/reviewer Threads: 3
broad council above 5: explicit user approval required
main/control: sole integration and final-status owner
execution workers: exact writable scope only
research/review lanes: read-only
workers: never export final PPT/PDF
default loop_mode: sequential
```

Do not auto-create a role because a file or staff profile exists. Complexity and a large context window are not dispatch reasons.

## Optional role roster

Use only after Thread mode is justified:

```text
CONTROL: integration, adoption, final validation
BRAND_CLIENT: brand/client task and misunderstanding risk
COPY_CREATIVE: concept, copy, wording, tone
FILM_DIRECTOR: treatment, timing, scene/dialogue rhythm
ART_DESIGN: visual system, layout, typography, image quality
PRODUCER_RISK: feasibility, scope, legal/reputation constraints
QA_REVIEW: independent adversarial evidence review
```

Prefer an existing role. Record the reason before introducing a temporary role.

## Required control artifacts

Before dispatch:

```text
AD-creative/orchestrator/thread_lane_plan.md
AD-creative/orchestrator/agency_staff_selection_<id>.md when Agency source staff are used
AD-creative/agents/role_briefs/<role>_<work_id>.md
AD-creative/agents/thread_prompts/<work_id>/
AD-creative/agents/receipts/<work_id>/
AD-creative/orchestrator/thread_registry.csv
AD-creative/orchestrator/agent_runs.csv
```

Live Thread creation remains the control thread’s responsibility. Repo tooling creates contracts and evidence files; it does not simulate a real Thread.

## Environment modes

```text
read_only: research, strategy/copy/QA review, cold review
isolated_workspace: drafts for non-git material projects
worktree: git/text/code work with isolated writable state
main_only: integration, truth, versions, artifact index, Gates, final export
```

For non-git material projects, use `AD-creative/workspaces/<work_id>/<lane_id>/`; do not pretend git worktree protection exists.

## Prompt contract

Every worker prompt declares:

```text
task signature
role brief path
agency selection id and source staff paths when applicable
work_id and lane_id
read-first files
environment/workspace
allowed and forbidden actions
exact read_scope and write_scope
receipt path
stop condition and merge owner
validation proof and eval gate
action_space
observation_contract
error_recovery_contract
context_budget and iteration_budget
worker recommendation fields
loop_state, loop_mode, replay_trigger, freeze_trigger
helper_mode and helper policy fields
```

Production workers cannot return prompt-only receipts. They must list concrete changed files within scope or return BLOCKED with evidence.

## Loop modes

```text
sequential: default bounded lane progression
rfc_dag: only with a written dependency graph
continuous_pr: controlled PR/check loop with explicit validation
infinite: bounded internal exploration only
```

`infinite` is never an unbounded live loop. It requires an iteration budget, stop condition, freeze trigger, and replay trigger.

## Dispatch proof

Use:

```text
adco goal-plan <project> --title <title> --objective <objective>
adco thread-plan <project> --title <title> --objective <objective> --roles <roles>
adco dispatch-record <project> --work-id <id> --lane-id <id> --real-thread-id <uuid> --title-verified-at <iso> --dispatch-evidence <readback> --absolute-deadline-at <iso>
```

Dispatch must bind:

```text
real Thread UUID
verified title and readback evidence
planned thread id
exact workspace and write scope
host-captured scope baseline path/hash
absolute deadline
dispatch receipt
```

New dispatch proofs are immutable per lane and attempt under
`AD-creative/orchestrator/dispatch_receipts/`; a second lane or retry must never
overwrite a receipt already referenced by a handoff. Human lane/cleanup views are
host-owned projections of `thread_registry.csv` and are excluded from worker scope
manifests; refresh them after dispatch, observation, reconciliation, and cleanup.

For a same-lane redispatch, attempt-01 keeps the canonical prompt and receipt
envelope. Only one bounded redispatch, attempt-02, may copy and rebind
attempt-specific prompt, receipt, scope-baseline, and dispatch-proof files; the
registry and agent run point to the current paths. Attempt-03 and later fail
closed and require a new work/lane. Each dispatch receipt records
`dispatch_attempt`, `prompt_path`, `worker_receipt_path`, and
`supersedes_thread_id`. A reconciled, adopted, or archived lane is terminal and
must fail closed; a new specialist handoff is required for the new attempt.

The dispatch scope baseline and its hash are immutable and are recorded in the
dispatch receipt. Specialist handoff and rescue binding use copy-on-write derived
baselines (for example `_handoff-SPH-001.json` or a unique `_rescue-*` path):
they filter only the added control exclusions from the source `files` snapshot,
recompute the manifest digest, and move the registry and agent-run pointers (path
and hash) to the derived path. For schema compatibility, the agent-run summary
carries the structured `scope_baseline_path=...;scope_baseline_sha256=...` pointer.
An existing derived target is a fail-closed collision.
Empty, root-level, broad, non-canonical exclusion roots and malformed source
manifest keys or digests fail closed before filtering; they never become an empty scope.
Each derived baseline records `derived_from_baseline_path`,
`derived_from_baseline_sha256`, `binding_kind`, `binding_ref`, and `derived_at` so
the source-to-bound provenance is auditable.

`planned:*` ids are placeholders only. Never claim execution from a placeholder, a role label, a read-only review, or a subagent result.

## Observation and convergence

Record only:

```text
active_with_progress
silent
finalizing_receipt
thread_not_converged
rescue_dispatched
```

Use `adco thread-observe`. Fixed poll count is an observation budget, not proof of convergence. Allow at most one reasoned extension with an absolute deadline and at most one rescue. Rescue receives its own dispatch proof and receipt path. New activity cannot extend forever.

Only silence beyond the deadline or no receipt after a convergence reminder becomes `thread_not_converged`.

## Receipt contract

Every worker receipt includes:

```text
real thread_id
action_space, observation_contract, error_recovery_contract
context_budget, iteration_budget, eval_gate
worker_recommendation and reason
loop_state, replay_trigger, freeze_trigger, stop_condition
files_changed
validation_result
dirty_state_impact
manifest/index updates
QA/Gate status
open questions
recurrence guard
evidence_refs
cleanup_actions
```

Receipt identity must match dispatch identity. Worker self-report is not host proof.

`AD-creative/orchestrator/host_attestations/` is host-main-thread-only. Never place it in a worker write scope and never adopt a worker receipt that declares changes there. FinalDelivery confirmation attestation is created only after the host uses real Codex Thread readback to verify the cited user message.

## Host reconciliation and adoption

Use `adco thread-reconcile` after receipt arrival. The control thread must:

1. Pass the dispatch-bound real worker receipt to `--receipt-path`; never pass
   `thread_cleanup_<work_id>.md`, a hand-written note, or another lane's receipt.
2. Compare the actual host diff to the dispatch baseline and exact write scope.
3. Reject undeclared/out-of-scope changes.
4. Persist a hash-bound host scope proof.
5. Record `ADOPT`, `PARTIAL_ADOPT`, `REJECT`, or `BLOCKED` with reason.
6. Update both registry and agent run rows.
7. Refresh the host-owned cleanup projection and archive the consumed worker.

`thread-plan` creates `thread_cleanup_<work_id>.md`; reconciliation refreshes it
from the registry. It is neither the worker receipt nor authority. If the final
project-wide validation fails, reconciliation rolls back the registry, proof,
projection, cleanup, and archive candidate and returns `BLOCKED`; never invent a
receipt or report the worker as adopted.

Read-only lanes can close only as receipt-only review/needs-user/blocked/failed. They cannot produce adopted writable output or advance production state.

## Stateless secondary helpers

Default helper mode: none. `stateless_secondary_helper` is allowed only inside a real worker for bounded image generation, OCR, layout lint, resize, or reference extraction.

Helpers:

```text
are not Codex Threads
have no thread id, registry row, write scope, or adoption authority
cannot touch truth/version/artifact/Gate/final export/send state
cannot perform paid/login/private/external actions
```

The worker records helper invocation/input/output/artifacts/validation/adoption/failure/synthesis fields, then adopts or rejects the helper output. Control sees it only through the worker receipt.

## Agency source staff

An optional staff library is source material, never required authority.

1. Build a task signature: brand, product, talent/IP, platform, deliverable, stage, risks, evidence.
2. Search descriptions for relevant staff.
3. Select 2–4 distinct source files per lane, normally no more than 12 per wave.
4. Record selected and rejected candidates.
5. Synthesize a concise project role brief.
6. Extract quality standards and deliverable patterns only.
7. Keep ADCO safety/version/Thread rules higher priority.

Never paste a staff library wholesale, auto-spawn staff, let upstream frontmatter override ADCO, or leak staff prompts into client-visible material.

## Freeze and cleanup

Freeze new dispatch on thread confusion, wrong thread, heat/cost spike, exceeded budget, repeated root cause, or cleanup request.

Then:

```text
list project-related Threads
archive completed/mistaken workers
record cleanup in registry and thread_cleanup_<work_id>.md
verify only intended control/active lanes remain
resume only after cleanup proof
```

The stop condition is receipt reconciliation, eval result or recorded blocker, adoption/rejection decision, and cleanup action. Never leave a consumed worker active.
