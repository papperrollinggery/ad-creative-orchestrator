# Agent Handoff Packet

run_id:
work_id:
task_signature_id:
agent_role:
agent_role_md:
agency_selection_id:
agency_role_brief:
agency_source_agents:
source_staff_count:
task_objective:
harness_id:
worker_thread_id:
agent_run_status:
target_gate_id:
reconciliation_result:
loop_mode: sequential
loop_state:
helper_mode: none
spawn_mode:
environment:
workspace_path:
write_scope:
receipt_path:
stop_condition:
merge_owner:
final_export_allowed: no

## Input Files

## Required Outputs

## Harness Contract

```text
action_space:
observation_contract:
error_recovery_contract:
context_budget:
eval_gate:
adoption_decision:
rejection_reason:
loop_state:
replay_trigger:
freeze_trigger:
stop_condition:
role_boundary:
agency_staff_used:
project_specific_brief:
tool_surface:
write_scope:
workspace_path:
iteration_budget:
output_contract:
completion_proof:
recovery_rule:
helper_policy:
allowed_helper_kinds:
helper_write_boundary:
helper_evidence_required:
helper_failure_policy:
```

## Loop Mode Contract

```text
allowed_loop_modes: sequential,rfc_dag,continuous_pr,infinite
sequential: default; finish one bounded lane step before the next handoff
rfc_dag: use only when an RFC-style dependency graph is written in the lane plan
continuous_pr: use only for controlled PR/check cycles with explicit validation commands
infinite: bounded internal exploration only; must declare iteration_budget, freeze_trigger, replay_trigger, and stop_condition
safe_stop: stop before client-visible send, paid/private/upload actions, destructive edits, global install, validation failure, or missing receipt proof
```

## Stateless Secondary Helper Contract

```text
helper_mode: none by default; use stateless_secondary_helper only for bounded local helper subtasks inside this real worker
allowed_helper_kinds: image_generation,ocr,layout_lint,asset_resize,reference_extraction
helper_boundary: helper may be a stateless helper/subagent-style call, but is not a Codex Thread or substitute worker/reviewer; no thread_id, registry row, write_scope, or adoption authority
helper_receipt_fields: helper_invocations, helper_input_refs, helper_output_refs, helper_artifacts, helper_validation_result, helper_adopted_by_worker, helper_failure_reason, worker_synthesis
worker_synthesis: worker must adopt/reject helper output before returning this receipt
```

## Allowed Actions

## Forbidden Actions

```text
Do not write internal notes into client-facing drafts.
Do not invent logos, packaging text, cases, or source evidence.
Do not overwrite old versions.
Do not mark assets client-visible without gate approval.
Do not mark the work complete with prompt-only output.
Do not return a production worker receipt that is prompt-only; list changed files or return BLOCKED with evidence.
Do not write outside the assigned write_scope.
Do not treat a stateless helper as a Codex Thread, worker, reviewer, registry row, or write_scope.
Do not let helper output touch master truth, final exports, client send, or adoption decisions directly.
Do not export final PPT/PDF from a worker lane.
Do not mention prompts, thread plans, lane plans, or worker roles in client-facing copy.
```

## Linked Requirements

## Linked References

## Linked Assets

## Linked Prompt / Job Specs

## Gate To Pass

## Completion Proof Required

```text
artifact paths
exact source version used
manifest or index rows affected
agent_runs row status
gate_log row or target_gate_id
reconciliation result
QA or gate status
user/client/Pro-review comments addressed or deferred
adoption_decision and rejection_reason when not adopted
recurrence guard
helper evidence and worker_synthesis when helper_mode is stateless_secondary_helper
evidence refs
known risks
```

## Handoff Back Format

```text
summary
files produced
manifest updates needed
evidence
qa status
open questions
workflow issues found
adoption_decision
rejection_reason
recurrence_guard
helper_mode
helper_invocations
helper_input_refs
helper_output_refs
helper_artifacts
helper_validation_result
helper_adopted_by_worker
helper_failure_reason
worker_synthesis
recommended next action
```
