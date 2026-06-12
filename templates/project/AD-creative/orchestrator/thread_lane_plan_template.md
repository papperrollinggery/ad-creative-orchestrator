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

## Lane Map

| lane_id | thread_id | thread_title | thread_role | agent_role_md | agency_selection_id | agency_role_brief | agency_source_agents | source_staff_count | work_id | purpose | spawn_mode | environment | workspace_path | read_first | write_scope | receipt_path | stop_condition | validation_proof | required_output | merge_owner | final_export_allowed | lifecycle_status | cleanup_note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Environment values:

```text
read_only: default for research, copy review, strategy review, QA, and council lanes
isolated_workspace: use AD-creative/workspaces/<work_id>/ for PPT, image, story, or material drafting in non-git projects
worktree: use only for git repositories or text/code projects where branch merge is safe
main_only: use for integration, version truth, final export, and final status
```

## Thread Registry

| thread_id | title | role | lane_id | lifecycle_state | pinned | cleanup_action | notes |
|---|---|---|---|---|---|---|---|

## Master Thread Rules

```text
Owns current_truth, work_items, agent_runs, gate_log, artifact_index, and final answer.
Reads every worker result before accepting it.
Does not copy worker output blindly.
Runs or records the relevant validation/gate before advancing state.
Lists existing ADCO threads before creating a new employee thread.
Renames vague employee thread titles before assigning work.
Archives duplicate, stale, superseded, or reconciled employee threads.
Assigns a role markdown file before every worker starts.
Uses read_only by default; uses isolated_workspace or worktree only when writing is necessary.
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
files_produced:
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
