# Thread Lane Plan

goal_id:
run_id:
created_at:
master_thread_id:
project_kind: ppt_material_project
task_signature_id:
current_version_id:
loop_mode: sequential
helper_mode: none

## Goal

```text
user_outcome:
success_standard:
blocked_if:
```

## Task Signature

```text
brand:
product:
talent_or_ip:
platform_or_channel:
deliverable:
stage:
primary_risks:
evidence_needed:
```

## Thread Budget

```text
max_active_worker_reviewer: 3
default_thread_mode: off; use real Threads only for bounded isolation, parallelism, or independent review
broad_council_requires_user_approval_over: 5
main_thread_only_for: integration,current_truth,version_map,artifact_index,gate_log,final_export,final_status
freeze_trigger: user reports thread confusion / high heat / wrong thread / cleanup request
replay_trigger: validation_result FAIL / missing receipt schema / stale evidence / out-of-scope edit / reopened feedback
stop_condition: receipt reconciled, eval_gate passed or blocker recorded, adoption_decision recorded, cleanup action planned
poll_rule: fixed poll counts are inspection budgets, never automatic failure
progress_states: active_with_progress,finalizing_receipt
no_progress_state: silent
deadline_rule: one reasoned bounded extension with an absolute deadline
failure_rule: thread_not_converged only after silent/reminder evidence past the absolute deadline
rescue_limit: 1
rescue_proof_rule: rescue has a separate dispatch receipt and rescue-bound receipt path
scope_proof_rule: host captures dispatch baseline; reconciliation compares actual diff with receipt + write_scope and writes host proof
```

## Loop Mode Contract

```text
loop_mode: sequential
allowed_loop_modes: sequential,rfc_dag,continuous_pr,infinite
sequential: default; finish one bounded lane step before the next handoff
rfc_dag: use only when an RFC-style dependency graph is written in the lane plan
continuous_pr: use only for controlled PR/check cycles with explicit validation commands
infinite: bounded internal exploration only; must declare iteration_budget, freeze_trigger, replay_trigger, and stop_condition
safe_stop: stop before client-visible send, paid/private/upload actions, destructive edits, global install, validation failure, or missing receipt proof
replay_trigger: validation_result FAIL, missing receipt schema, stale evidence, out-of-scope edit, or reopened feedback
freeze_trigger: thread confusion, wrong thread, heat/cost spike, budget exceeded, repeated same root cause, or cleanup request
stop_condition: receipt reconciled, eval_gate passed or blocker recorded, adoption_decision recorded, and cleanup action planned
```

Execution layer rule:

```text
main/control thread decomposes, assigns, integrates, validates, cleans up, and reports only.
execution_worker lanes own scoped implementation or artifact production.
read_only_review/research/cold_review lanes are the only read-only defaults.
execution_worker lanes must declare exact write_scope before spawn.
```

## Harness Field Contract

```text
action_space:
observation_contract:
error_recovery_contract:
context_budget:
iteration_budget:
eval_gate:
worker_recommendation:
worker_recommendation_reason:
loop_state:
replay_trigger:
freeze_trigger:
stop_condition:
```

## Stateless Secondary Helper Contract

```text
helper_mode: none by default; stateless_secondary_helper only when a real worker invokes a bounded local helper
helper_policy: optional stateless helper/subagent-style call inside L1 worker only; not a Codex Thread or substitute worker/reviewer
allowed_helper_kinds: image_generation,ocr,layout_lint,asset_resize,reference_extraction
helper_write_boundary: helper has no thread_id, no thread_registry.csv row, no write_scope, and no access to master truth/final export/client send
helper_evidence_required: helper_invocations, helper_input_refs, helper_output_refs, helper_artifacts, helper_validation_result, helper_adopted_by_worker, helper_failure_reason, worker_synthesis
helper_failure_policy: worker records helper failure and returns BLOCKED/PARTIAL or proceeds without helper only when safe
worker_synthesis: L1 worker adopts/rejects helper output before main/control reviews the worker receipt
```

## Lane Harness Matrix

| lane_id | action_space | observation_contract | error_recovery_contract | context_budget | iteration_budget | eval_gate | worker_recommendation | worker_recommendation_reason | loop_state | replay_trigger | freeze_trigger | stop_condition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Lane Helper Matrix

| lane_id | helper_mode | helper_policy | allowed_helper_kinds | helper_write_boundary | helper_evidence_required | helper_failure_policy | helper_invocations | helper_input_refs | helper_output_refs | helper_artifacts | helper_validation_result | helper_adopted_by_worker | helper_failure_reason | worker_synthesis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Lane Map

| lane_id | lane_run_id | thread_id | thread_title | thread_role | professional_identity | agent_role_md | agency_selection_id | agency_role_brief | agency_source_agents | source_staff_count | work_id | purpose | spawn_mode | mode | environment | workspace_path | read_first | write_scope | receipt_path | receipt_status | reconciliation_status | stop_condition | validation_proof | required_output | merge_owner | final_export_allowed | lifecycle_status | cleanup_note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Spawn mode values:

```text
execution_worker: scoped implementation, document edit, artifact production, visual/story/material drafting
read_only_review: independent QA, diff review, gate review, cold review
research: evidence gathering or option mapping with no writes
cold_review: isolated readiness/release review with no edits
main_only: integration, version truth, final export, final status, and user report
```

Environment values:

```text
read_only: only for read_only_review, research, and cold_review lanes
isolated_workspace: execution_worker writes only AD-creative/workspaces/<work_id>/ plus its receipt
worktree: execution_worker for git/text/code edits where merge is safe
main_only: use for integration, version truth, final export, and final status
```

## Thread Registry

| thread_id | title | role | lane_id | lane_run_id | lifecycle_state | convergence_state | absolute_deadline_at | bounded_extension_used | rescue_count | receipt_thread_id | adoption_decision | scope_baseline_path | scope_baseline_sha256 | scope_proof_path | scope_proof_sha256 | rescue_dispatch_receipt_path | rescue_dispatch_evidence | receipt_status | reconciliation_status | pinned | archived | archived_at | cleanup_action | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Master Thread Rules

```text
Owns current_truth, work_items, agent_runs, gate_log, artifact_index, and final answer.
Reads every worker result before accepting it.
Requires the receipt thread_id to equal the real dispatched thread id.
Captures the host scope baseline at dispatch and requires a successful hash-bound host scope proof before adoption.
Does not copy worker output blindly.
Runs or records the relevant validation/gate before advancing state.
Lists existing ADCO threads before creating a new employee thread.
Renames vague employee thread titles before assigning work.
Archives duplicate, stale, superseded, or reconciled employee threads after consuming receipts.
Assigns a role markdown file before every worker starts.
Uses execution_worker for scoped production/editing work; uses read_only only for explorer/reviewer/research/cold-review lanes.
Requires exact write_scope for every execution_worker before spawn.
Does not allow more than 3 active workers without explicit user approval.
Does not allow more than 5 broad council/reviewer threads without explicit user approval.
Allows stateless secondary helpers only inside real worker threads; helpers are not Codex Threads and have no thread_id, registry row, write_scope, or adoption authority.
Exports final PPT/PDF only from the main control thread.
```

## Worker Prompt Envelope

```text
Repo:
Mode:
Loop mode:
Helper mode:
Task signature:
Agent role md:
Agency selection id:
Agency role brief:
Agency source agents:
Source staff count:
Goal:
Work item:
Read first:
Environment:
Workspace path:
Allowed actions:
Forbidden actions:
Write scope:
Receipt path:
Expected real thread id:
Absolute deadline:
Stop condition:
Merge owner:
Final export allowed: no
Completion proof:
Host scope baseline ref (main/control supplied):
Return format:
action_space:
observation_contract:
error_recovery_contract:
context_budget:
iteration_budget:
eval_gate:
worker_recommendation:
worker_rejection_reason:
loop_state:
replay_trigger:
freeze_trigger:
helper_policy:
allowed_helper_kinds:
helper_write_boundary:
helper_evidence_required:
helper_failure_policy:
```

## Worker Handoff Checklist

```text
summary:
files_changed:
validation_result:
dirty_state_impact:
cleanup_actions:
manifest_updates_needed:
manifest_index_updates:
evidence:
qa_gate_status:
open_questions:
workflow_issues_found:
recurrence_guard:
worker_recommendation:
worker_rejection_reason:
helper_mode:
helper_invocations:
helper_input_refs:
helper_output_refs:
helper_artifacts:
helper_validation_result:
helper_adopted_by_worker:
helper_failure_reason:
worker_synthesis:
prompt_only_output: invalid for production workers
recommended_next_action:
host_scope_proof: written only by main/control reconciliation; worker must not self-issue it
```

## Reconciliation Log

| lane_id | main_adoption_decision | main_rejection_reason | files_merged | gate_id | archived_at | notes |
|---|---|---|---|---|---|---|

## Cleanup Log

| checked_at | active_threads_kept | threads_archived | duplicate_titles_fixed | notes |
|---|---|---|---|---|
