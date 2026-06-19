# Thread Lane Plan

goal_id:
run_id:
created_at:
master_thread_id:
project_kind: ppt_material_project
task_signature_id:
current_version_id:

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
broad_council_requires_user_approval_over: 5
main_thread_only_for: integration,current_truth,version_map,artifact_index,gate_log,final_export,final_status
freeze_trigger: user reports thread confusion / high heat / wrong thread / cleanup request
```

Execution layer rule:

```text
main/control thread decomposes, assigns, integrates, validates, cleans up, and reports only.
execution_worker lanes own scoped implementation or artifact production.
read_only_review/research/cold_review lanes are the only read-only defaults.
execution_worker lanes must declare exact write_scope before spawn.
```

## Lane Map

| lane_id | thread_id | thread_title | thread_role | professional_identity | agent_role_md | agency_selection_id | agency_role_brief | agency_source_agents | source_staff_count | work_id | purpose | spawn_mode | mode | environment | workspace_path | read_first | write_scope | receipt_path | receipt_status | reconciliation_status | stop_condition | validation_proof | required_output | merge_owner | final_export_allowed | lifecycle_status | cleanup_note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

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

| thread_id | title | role | lane_id | lifecycle_state | receipt_status | reconciliation_status | pinned | cleanup_action | notes |
|---|---|---|---|---|---|---|---|---|---|

## Master Thread Rules

```text
Owns current_truth, work_items, agent_runs, gate_log, artifact_index, and final answer.
Reads every worker result before accepting it.
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
Exports final PPT/PDF only from the main control thread.
```

## Worker Prompt Envelope

```text
Repo:
Mode:
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
Stop condition:
Merge owner:
Final export allowed: no
Completion proof:
Return format:
```

## Worker Handoff Checklist

```text
summary:
files_changed:
validation:
dirty_state_impact:
cleanup_actions:
manifest_updates_needed:
evidence:
qa_status:
open_questions:
workflow_issues_found:
recommended_next_action:
```

## Reconciliation Log

| lane_id | accepted | rejected | files_merged | gate_id | notes |
|---|---|---|---|---|---|

## Cleanup Log

| checked_at | active_threads_kept | threads_archived | duplicate_titles_fixed | notes |
|---|---|---|---|---|
