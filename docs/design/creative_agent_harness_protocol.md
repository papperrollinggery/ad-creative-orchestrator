# Creative Agent Harness Protocol

date: 2026-06-06
status: design protocol
scope: apply public Higgsfield MCP workflow lessons without connecting to Higgsfield

## External Pattern

The useful lesson is not "use Higgsfield". It is the harness around the agent:

- One controlled creative tool surface for generation, history, characters, presets, workspace scope, and scoring.
- A brief-to-storyboard-to-base-assets-to-final-video sequence, with human review before final generation.
- Structured generation parameters instead of a freeform prompt: model or route, ratio, quality, reference assets, character or product identity, style preset, motion preset, and completion proof.
- Async generation receipts: job id, status, output URL/path, retries, cost/credit awareness, and failure state.
- Reuse of previous generations as inputs, so iteration is asset-backed rather than chat-memory-backed.
- Final polish is a separate step: captions, pacing, transitions, color, audio, and delivery packaging.

Observed public workflow:

```text
Connect the agent to the creative workspace
-> give a commercial brief
-> generate character design, environment visuals, base images, and storyboard
-> review and refine until the story, style, and product message match
-> generate the full 15-second commercial from the finalized storyboard
-> polish in editing tools before delivery
```

## Project Conclusion

This repo should not depend on a vendor MCP as the quality layer. The durable quality layer should be a local harness contract that every worker thread follows.

Use external MCP/tools only as optional execution routes. The project truth remains:

```text
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/visual_assets/asset_manifest.csv
AD-creative/image_jobs/
AD-creative/gates/
```

## Harness Layers

Each worker thread must be constrained by seven layers.

| Layer | Required Control | Why |
|---|---|---|
| Role envelope | Worker role, scope, forbidden ownership | Prevents role-chat drift |
| Input inventory | Requirements, references, assets, current truth | Prevents invented facts |
| Tool surface | Allowed tools/routes/actions only | Prevents uncontrolled execution |
| Prompt spec | Structured brief, scene, style, camera, negative constraints | Prevents vague prompt blobs |
| Job lifecycle | draft, submitted, running, completed, failed, selected, rejected | Makes async generation auditable |
| Completion proof | Files, manifest rows, QA notes, gate status | Prevents prompt-only completion |
| Recovery loop | issue found, fix applied, recurrence guard | Prevents repeated long-thread mistakes |

## Worker Thread Contract

Before work starts, the master thread gives the worker a handoff packet with:

```text
work_id
agent_role
task_objective
input_files
linked_requirements
linked_references
linked_assets
allowed_actions
forbidden_actions
write_scope
iteration_budget
output_contract
gate_to_pass
completion_proof
recovery_rule
```

The worker may only write inside its assigned output paths. It must hand back:

```text
summary
files_produced
manifest_updates_needed
evidence
qa_status
open_questions
workflow_issues_found
recommended_next_action
```

## Visual Production Contract

For visual/image/video work, the worker cannot jump from concept directly to final output.

Required sequence:

```text
1. Creative brief normalization
2. Character/product/environment/style lock
3. Storyboard or shot list
4. Base image generation or sourcing
5. Visual review and selection
6. Final asset generation or assembly
7. Post-production polish notes
8. Gate report
```

Required object fields:

```text
storyboard_id
shot_id
linked_requirement_ids
linked_reference_ids
linked_asset_ids
use_case
visibility
ratio
model_route
mode_or_preset
prompt_spec
negative_constraints
input_image_roles
job_status
output_paths
qa_status
retry_reason
```

## Master Thread Duties

The master thread owns orchestration, not production details:

- Split work by artifact boundary, not by vague roles.
- Assign only one accountable worker per artifact.
- Reconcile worker results into `current_truth.md`, indexes, and gate logs.
- Reject handoff if proof is missing.
- Convert recurring issues into project-local workflow fixes before they recur.

## Recurrence Guard

When a worker discovers a repeatable workflow problem, it must report it as:

```text
issue:
where_seen:
impact:
fix_applied:
future_guard:
candidate_template_or_skill_change:
```

The master thread then chooses one of:

```text
record_only
patch_project_template
add_gate_check
draft_skill_opportunity
ask_user_before_global_install
```

## Non-Goals

This protocol does not:

- connect to Higgsfield;
- require a paid media generation platform;
- replace the local project files as truth;
- allow workers to mark client-visible assets without gate approval;
- treat a prompt, screenshot, or chat answer as a finished deliverable.
