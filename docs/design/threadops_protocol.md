# Codex ThreadOps Protocol

date: 2026-06-06
status: execution protocol
scope: Codex Goal + native threads for ad creative orchestration

## Direct Conclusion

This project can use Codex threads for execution, but threads must not become the source of truth.

Use threads as isolated work lanes. Use project files as durable state:

```text
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/thread_registry.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/orchestrator/events.jsonl
AD-creative/agents/
AD-creative/gates/
AD-creative/image_jobs/
AD-creative/visual_assets/asset_manifest.csv
AD-creative/handoff/
```

## Goal Model

Use one Codex Goal per meaningful delivery objective.

```text
Goal = user-facing outcome
Work item = project task inside the goal
Thread = temporary execution lane for one or more isolated work items
Gate = acceptance decision before state advances
```

The master/control thread owns orchestration only: decompose, assign, integrate, validate, clean up, and report. Execution workers own scoped implementation or artifact production inside their declared write scope. Read-only lanes are limited to explorer, reviewer, research, and cold-review work.

Prepare the local control plane with:

```text
adco goal-plan <project_dir> --title <goal_title> --objective <goal_objective>
adco thread-plan <project_dir> --title <goal_title> --objective <goal_objective> --roles brand_client,copy_creative,qa_review
```

`thread-plan` creates internal-only lane plans, role briefs, worker prompts, receipt placeholders, registry rows, and cleanup proof scaffolding. It does not create live Codex Threads by itself; the master thread uses the generated prompts to create or reuse threads.

## Thread Roles

| Thread | Purpose | Write Permission | Stop Condition | Required Output |
|---|---|---|---|---|
| master | Goal owner, decomposition, reconciliation, final answer | All project files, but only minimal necessary edits | Goal complete or blocked by explicit gate | Updated truth, gates, handoff, validation status |
| explorer | Read-only research or repo inspection | None | Findings are enough to choose next move | Evidence, candidate changes, risks |
| worker | Produce one artifact or file-scoped change | Exact declared files or directories only | Required output contract satisfied or blocked | Files changed, validation, dirty-state impact, cleanup actions, evidence, manifest/index updates |
| reviewer | Independent review of changed artifacts | None by default | Findings complete | Issues by severity, missing checks, approval/block |
| recovery | Investigate repeated workflow failure | Usually read-only; patch only if declared | Recurrence guard proposed | Root cause, fix, future guard |

## Employee Naming

Use stable employee-style names so the thread list remains readable.

```text
ADCO 主控｜<goal short name>
ADCO 员工｜Explorer｜<scope>
ADCO 员工｜Research｜<brand/product/reference scope>
ADCO 员工｜Strategy｜<direction scope>
ADCO 员工｜Story｜<script/storyboard scope>
ADCO 员工｜VisualPlan｜<asset lock scope>
ADCO 员工｜ImageVideo｜<asset/job scope>
ADCO 员工｜Reviewer｜<gate/review scope>
ADCO 员工｜Recovery｜<issue scope>
```

Naming rules:

```text
1. Prefix all project threads with ADCO.
2. Include one role only.
3. Include one short scope only.
4. Do not create duplicate role/scope threads while an active one exists.
5. Rename vague inherited titles before sending work.
```

## Thread Lifecycle

Every employee thread has a lifecycle owned by the master thread.

```text
planned -> created -> assigned -> running -> returned -> reconciled -> archived
```

Lifecycle rules:

```text
created: thread exists but has not returned useful work.
assigned: prompt includes role, files, write scope, stop condition, and return format.
running: thread is working or waiting for tool output.
returned: thread produced a handoff result.
reconciled: master accepted/rejected the result and updated project truth.
archived: thread is no longer needed in the active lane map.
```

Use explicit terminal/error states when needed:

```text
reconciled_accepted: master accepted the receipt and merged only approved changes.
reconciled_rejected: master rejected the receipt and recorded the reason.
blocked: worker cannot continue without user/project input.
failed: worker failed to produce usable output.
superseded: another lane or newer run replaced this lane.
stale: thread no longer matches the current goal or work item.
invalid: thread lacks a registry row, receipt path, write scope, or stop condition.
canceled: master or user intentionally stopped the lane.
```

The master should pin only active control/review threads. Worker threads should be unpinned or archived after reconciliation unless they are intentionally reused.

## Dead Thread Cleanup

The master runs cleanup at these points:

```text
before spawning a new employee thread
after a worker result is reconciled
before final response
when the active Goal changes
```

Cleanup checklist:

```text
1. list_threads with query ADCO.
2. keep the master thread active.
3. keep only employee threads whose lane status is created, assigned, running, or returned.
4. archive employee threads whose result is reconciled, superseded, duplicate, stale, or off-scope.
5. rename any active employee thread that violates the naming rule.
6. record cleanup notes in the lane plan, not in current_truth unless it affects delivery state.
```

## Spawn Rules

Spawn a worker thread only when all are true:

```text
1. The work item can be described without hidden context.
2. Input files and reference files are named.
3. Write scope is isolated.
4. Stop condition is objective.
5. Required output can be verified by the master thread.
```

Before spawning, the master must search/list existing ADCO threads and reuse, rename, or archive stale ones instead of creating duplicates.

Prefer read-only explorer/research/reviewer/cold-review threads when:

```text
scope is uncertain
task is mostly research
multiple options need comparison
the master thread should avoid context overload
```

Use execution workers when a scoped implementation, document edit, artifact, or material production task can be isolated. A dirty repo is not by itself a reason to make the lane read-only; it means the handoff must name exact write_scope, expected dirty-state impact, and cleanup receipt requirements.

Prefer a worktree thread only when:

```text
the project is a git repository or text/code project
the worker will edit code or shared docs
two workers may touch nearby files
the change might be rejected
validation may generate temporary files
```

Use AD-creative isolated workspace mode for PPT/material projects:

```text
worker output path: AD-creative/workspaces/<work_id>/
worker may write only its receipt and declared workspace files
worker must not update current_truth, version_map, artifact_index, gate_log, or final exports
master imports accepted files after review
```

Use local read-only threads when:

```text
the worker is read-only
or the master explicitly owns reconciliation immediately after
```

## Standard Thread Prompt

```text
Repo: /Users/jinjungao/work/ad-creative-orchestrator
Mode: <execution_worker | read_only_review | research | cold_review>
Goal: <subgoal>
Work item: <work_id>

Read first:
- <absolute or project-relative files>

Allowed actions:
- <tools / commands / files>

Forbidden:
- Do not edit outside <write_scope>.
- Do not update current_truth, gate_log, or final handoff unless explicitly assigned.
- Do not mark client-visible assets without gate approval.
- Do not treat prompts as final visual deliverables.

Return:
- summary
- files_changed
- validation
- dirty_state_impact
- cleanup_actions
- evidence refs
- manifest/index rows affected
- QA/gate status
- open questions
- workflow issue and recurrence guard, if found
```

## Execution Loop

```text
1. Master sets or confirms Codex Goal.
2. Master reads current_truth and work_items.
3. Master creates or updates work_items, agent_runs, and thread_registry.
4. Master writes handoff packet for the worker.
5. Master creates/sends worker thread prompt.
6. Worker runs inside declared boundary.
7. Worker returns receipt with files_changed, validation, dirty-state impact, and cleanup actions.
8. Master reads the worker thread result.
9. Master reconciles accepted output into project files.
10. Master runs the relevant gate/checks.
11. Master archives completed employee threads after consuming the receipt and updates thread_registry.
12. Master either advances, retries, asks user, or records blocked state.
```

## Project Lane Map

| Lane | Worker Role | Typical Files |
|---|---|---|
| research | Brand/product/reference evidence | `AD-creative/references/`, `source_events.csv`, `requirements.csv` |
| strategy | Direction and option structure | `AD-creative/creative/`, `proposal_architecture/` |
| story | Narrative, shot list, script | `AD-creative/story/`, `image_jobs/`, `client_review/slide_spec.md` |
| visual-plan | Character/product/environment/style locks | `visual_assets/visual_asset_slots.csv`, `image_jobs/` |
| image-video | Prompt pack, generation receipts, asset outputs | `image_jobs/`, `visual_assets/raw/`, `asset_manifest.csv` |
| visual-qa | Asset review and visibility decision | `visual_review/`, `gates/visual_review_*` |
| sample | HTML or slide sample | `client_review/`, `ppt/` |
| delivery | Final package and handoff | `delivery/`, `handoff/` |
| workflow-recovery | Repeated issue fix | project template or docs file named by master |

## Review Gates

Threads do not approve their own stage advancement.

```text
worker completion -> master reconciliation -> gate -> next stage
```

Minimum gates:

```text
Research Gate
Creative Gate
Visual Plan Gate
Visual Review Gate
PPT Gate
Final Gate
Skill Mining Gate
```

## Recurrence Guard

If a worker sees a problem likely to recur in long-thread work, it must report:

```text
issue:
impact:
where_seen:
fix_applied_or_proposed:
future_guard:
template_or_skill_candidate:
```

The master can then choose:

```text
record in events.jsonl
patch project template
add gate check
draft skill opportunity
ask user before global install
```

## Operating Boundary

ThreadOps should not be used for every small edit. It is justified when it reduces interference, preserves context, or creates independent review.

Do not spawn threads for:

```text
single-file typo fixes
final reconciliation
global truth updates
user decision making
high-risk account/payment/private actions
```

Use threads for:

```text
parallel reference research
independent QA/review
large creative option exploration
visual prompt/asset batches with isolated output folders
workflow failure investigation
```
