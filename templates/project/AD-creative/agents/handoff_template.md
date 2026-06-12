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
```

## Allowed Actions

## Forbidden Actions

```text
Do not write internal notes into client-facing drafts.
Do not invent logos, packaging text, cases, or source evidence.
Do not overwrite old versions.
Do not mark assets client-visible without gate approval.
Do not mark the work complete with prompt-only output.
Do not write outside the assigned write_scope.
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
recommended next action
```
