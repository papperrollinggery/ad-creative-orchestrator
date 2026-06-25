---
name: ad-creative-orchestrator
description: Use for Codex-first advertising creative project orchestration. Handles messy client materials, requirement tracking, research plans, multi-agent handoff, visual/image workflows, gate review, PPT handoff, delivery, and project-local skill mining.
---

# Ad Creative Orchestrator

## Core Rule

Operate through project files, not chat memory.

Read and update:

```text
AD-creative/orchestrator/
AD-creative/handoff/
```

Keep user-facing summaries clear and low-density.

## Non-Negotiable Safety Rules

### Completion Rule

Do not mark a project goal complete only because a gate says PASS or a deck was exported.

Completion requires all of the following:

```text
latest client-visible artifact has a stable version id
version_map.csv and current_truth.md identify the same current version and supersession chain
artifact_index.csv registers the current PPTX, PDF, preview, and text extract
PPTX/PDF/preview/text extract were produced from and reviewed against the same current version
PPT editability check passes on the exact current PPTX
all received user/client/Pro-review diff comments are fixed, explicitly deferred with owner, or listed in 待你确认.md
project validation passes with ERRORS=0 and VALIDATION=PASS
thread cleanup / active-thread audit is done when Codex threads were used
open client-send blockers are recorded in 待你确认.md
```

If new user feedback arrives after completion, reopen the stage as revision work. Do not keep claiming the previous goal is still complete.

### Version Safety Rule

Never overwrite a client-visible version file as the only copy of that version.

Before changing any exported file whose name includes a version such as `v1`, `v2`, or `final`:

```text
1. Compute hash and stat for the existing PPTX/PDF.
2. Copy the existing files to AD-creative/ppt/exports/version_archive/ using an immutable name.
3. Register the archived files in artifact_index.csv and version_map.csv.
4. Write the next material revision to a new version name, for example v2.
5. Only after the new version is validated may legacy aliases be synchronized.
```

Do not rely on filenames such as `专业影视版` or `专业文案版` as the source of truth. Treat them as aliases. The source of truth is `version_map.csv` plus `current_truth.md`.

If a client-visible file exists only as `v1` or `final`, stop and archive it before editing. Never use "final", "professional", "影视版", or "文案版" as a version decision.

### Thread Budget Rule

Codex threads are expensive. Use them deliberately.

Default limits:

```text
max active worker/reviewer threads at one time: 3
max broad council threads without explicit user approval: 5
main thread is the only integration owner
execution workers own exact write_scope
read-only lanes are only research/review/cold-review
workers must not export final PPT/PDF
```

If the user reports thread confusion, high heat, wrong-thread behavior, or says to clean threads:

```text
freeze new worker creation
list project-related threads
archive all completed or mistaken workers
record cleanup in thread_registry.csv and a thread_cleanup_*.md file
verify only the main control thread remains active for the project query
resume production only after cleanup verification
```

After a worker receipt is consumed, update the lane lifecycle, archive or close the worker thread, and keep the receipt as the durable evidence. Do not leave consumed workers active.

### Fixed Role Roster

For advertising creative work, prefer a stable role roster rather than one-off task threads.

Default roster:

```text
CONTROL: main thread, integration and final validation
BRAND_CLIENT: brand task, client demand, risk of client misunderstanding
COPY_CREATIVE: concept, headlines, wording, campaign line, tone
FILM_DIRECTOR: story logic, treatment, timing, dialogue, scene rhythm
ART_DESIGN: visual system, layout, typography, image quality
PRODUCER_RISK: feasibility, budget/scope, alcohol/artist/platform risk
QA_REVIEW: final adversarial review and evidence check
```

Do not create a new role when an existing role can absorb the work. If a temporary role is necessary, write the reason in `thread_registry.csv` before using it.

### Worktree / Role MD Mode

Mature multi-thread work needs an explicit control plane. Do not spawn broad helper threads from chat alone.

Before starting any worker, create or update:

```text
AD-creative/orchestrator/thread_lane_plan.md
AD-creative/orchestrator/agency_staff_selection_*.md when Agency staff are used
AD-creative/agents/role_briefs/<role>_<work_id>.md
```

Every worker prompt must include:

```text
task signature
role markdown or project role brief path
agency selection id
agency source staff paths when available
work_id
read-first files
environment mode and workspace/worktree path
allowed actions
forbidden actions
write scope
receipt path
stop condition
merge owner
validation proof
```

Use these environment modes:

```text
read_only: default for research, copy review, strategy review, QA, and council lanes
isolated_workspace: for PPT/image/story drafts in non-git material projects
worktree: for git repositories or text/code projects where branches can be merged safely
main_only: for integration, version_map, artifact_index, current_truth, gate_log, final export
```

In non-git PPT/material projects, do not pretend git worktree protection exists. Use `AD-creative/workspaces/<work_id>/` as an isolated drafting area, then let the main thread import accepted files.

Workers may write only their receipt unless the lane plan grants exact writable paths. The main thread is the only default owner of:

```text
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/version_map.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/ppt/exports/
```

### Agent Agency Integration

If `/Users/jinjungao/.claude/agents` exists, treat it as a reusable staff library.

Use it this way:

```text
1. Build a task signature from the current project: brand, product, talent, platform, deliverable, stage, risk, and required evidence.
2. Search `/Users/jinjungao/.claude/agents/*.md` by filename and frontmatter description for matching staff.
3. Select 2-4 source staff files per lane, not a fixed global list.
4. Record selected and rejected candidates in `AD-creative/orchestrator/agency_staff_selection_*.md`.
5. Generate a project-specific role brief in `AD-creative/agents/role_briefs/<role>_<work_id>.md`.
6. Put the selection id, role brief path, and source staff paths in `thread_lane_plan.md`.
7. Extract only role quality standards, critical rules, workflow, and deliverable templates.
8. Keep AD-creative rules higher priority than upstream staff behavior.
```

Do not use it this way:

```text
do not paste hundreds of staff files into context
do not auto-spawn staff just because a file exists
do not let staff-specific model/tool/frontmatter override Codex thread budget or version safety
do not copy upstream staff descriptions into client-facing decks
```

Only use staff files as source material for a concise project role brief. Do not paste long upstream prompts into worker instructions, receipts, or customer-facing pages.

Staff selection scoring:

```text
domain_fit: does the staff match the brand/product/talent/platform?
deliverable_fit: can the staff improve PPT, copy, film treatment, visual asset, QA, or production gate?
risk_fit: does the staff cover alcohol, artist image, client misunderstanding, legal/reputation, or version risk?
evidence_fit: can the staff produce verifiable receipt output, not just opinion?
non_overlap: does the staff add a distinct lens instead of duplicating another selected staff?
context_cost: can the useful part fit into a concise project role brief?
```

Selection limits:

```text
default source staff per lane: 2-4
default total source staff for one wave: <= 12
do not select broad councils unless there is a written question for each staff
do not spawn workers merely because staff were selected
```

Project-specific role brief requirements:

```text
source_staff_paths
project facts to honor
role objective for this work_id
what to extract from each source staff
what to ignore from each source staff
output contract
forbidden actions
acceptance evidence
```

If a task is materially different from the previous task, redo staff selection. Treat `agent_agency_mapping_*.md` as fallback memory, not as a mandatory fixed roster.

### Recurrence Prevention Checklist

Before declaring an advertising creative task complete, explicitly check these known failure modes:

```text
premature_completion: gate/export alone is not completion
version_overwrite: never overwrite a client-visible version as the only copy
thread_sprawl: no worker without lane plan, role brief, write scope, receipt, and cleanup
static_staff_mapping: redo Agency staff selection for the actual task instead of reusing stale roles blindly
copied_staff_prompt: synthesize a project role brief; do not paste upstream staff text wholesale
internal_language_leak: client-visible pages must not mention prompts, execution steps, threads, lane plans, or worker roles
story_thinning: proposal pages must retain story, segment summary, brand mapping, timing, and key dialogue where relevant
layout_regression: PDF/PPT visual QA must check overflow, cropping, busy image text, repeated stills, font legibility, timing labels, key dialogue labels, and story-beat differentiation
external_review_reopen: if new Pro/client/reviewer feedback changes blockers, mark stage reopened/revision instead of saying the old completion still stands
```

## User Entrypoints

### double-click launcher

For a non-developer on this Mac, use:

```text
/Users/jinjungao/work/ad-creative-orchestrator/启动广告创意项目.command
```

It prompts for project folder, material file/folder, and goal, then opens:

```text
AD-creative/handoff/操作台.html
```

### ad-creative:operator

Use when the user wants a non-developer handoff surface or one local command.

Run:

```text
adco quickstart [project_dir]
adco quickstart [project_dir] --json
adco sample <project_dir>
adco demo [project_dir]
adco --version
adco doctor
adco support-bundle <project_dir>
adco support-bundle <project_dir> --json
adco open-dashboard <project_dir>
adco audit-dashboard <project_dir> --render --json
adco validate <project_dir>
adco check
adco run <project_dir> --material <materials_path>
adco creative-proposal <project_dir> --work-id <WORK-ID>
adco creative-proposal <project_dir> --json
adco creative-quality-gate <project_dir>
adco goal-plan <project_dir> --title <goal_title> --objective <goal_objective>
adco thread-plan <project_dir> --title <goal_title> --objective <goal_objective> --roles brand_client,copy_creative,qa_review
adco profile-analyze <project_dir> --source-id <SRC-ID> --brand <brand> --company <company>
adco hygiene <project_dir>
adco intake <project_dir>
adco add-reference <project_dir> --url <https_url> --title <title>
adco search-quality-gate <project_dir>
adco reference-pack-gate <project_dir>
adco add-asset <project_dir> --file <image_file> --slot-id <slot_id> --requirement-id <requirement_id>
adco import-imagegen <project_dir> --slot-id <slot_id> --selected
adco visual-quality-gate <project_dir>
adco export-pptx <project_dir>
adco check-pptx <project_dir> --file <pptx_file>
adco client-pack-gate <project_dir>
adco handoff-readiness-gate <project_dir>
adco audit-dashboard <project_dir> --render
adco install-skill
```

Installed CLI equivalent:

```text
python3 -m pip install .
adco init <project_dir>
adco quickstart [project_dir]
adco quickstart [project_dir] --json
adco demo [project_dir]
adco sample <project_dir>
adco --version
adco support-bundle <project_dir> --json
adco audit-dashboard <project_dir> --render --json
adco doctor
adco doctor --json
adco release-status
adco release-status --json
adco docs
adco docs --json
adco support-bundle <project_dir>
adco open-dashboard <project_dir>
adco status <project_dir>
adco next <project_dir>
adco validate <project_dir>
adco validate <project_dir> --json
adco check
adco run <project_dir> --material <materials_path>
adco creative-proposal <project_dir> --work-id <WORK-ID>
adco creative-proposal <project_dir> --json
adco creative-quality-gate <project_dir>
adco goal-plan <project_dir> --title <goal_title> --objective <goal_objective>
adco thread-plan <project_dir> --title <goal_title> --objective <goal_objective> --roles brand_client,copy_creative,qa_review
adco profile-analyze <project_dir> --source-id <SRC-ID> --brand <brand> --company <company>
adco hygiene <project_dir>
adco-check
adco-validate <project_dir>
make dist-check
make release-check
```

Gate commands enforce adversarial council:

```text
creative-quality-gate / reference-pack-gate / search-quality-gate / visual-quality-gate / client-pack-gate / handoff-readiness-gate
```

If no valid adversarial council note exists for the stage, a clean PASS is downgraded to PARTIAL_PASS.

Use `sample` when a new user needs a runnable local project without real client materials.

Then use:

```text
AD-creative/handoff/操作台.html
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/客户追问话术.md
AD-creative/gates/THREE-COUNCIL-READINESS_report.md
```

### ad-creative:run

One-command project operation.

Use when the user gives a project directory plus messy client materials and expects Codex to proceed until a real decision point.

Steps:

```text
1. If project files are missing, initialize from /Users/jinjungao/work/ad-creative-orchestrator/templates/project without overwriting existing files.
2. Register provided materials as source events.
3. Classify each source as initial, supplement, change, feedback, approval, rejection, director_note, or unknown.
4. Update current_truth, requirements, gaps, work_items, artifact_index, gate_log, and handoff files.
5. Decide whether search is needed and write search_plan if needed.
6. Continue through the next safe internal stage only if no human decision is blocking.
7. Stop at any required user decision and update 待你确认.md.
8. Before any client-visible version change, archive the previous version and update version_map.csv.
9. Run `adco validate` before reporting status.
```

User only needs to provide:

```text
项目目录
资料位置
本轮目标
```

Default stop points:

```text
client deck send
paid/login/private account actions
external upload of client materials
destructive overwrite or delete
AI image client visibility
global skill install
```

### ad-creative:thread-plan

Use when a project needs Codex Threads as controlled execution lanes.

Run:

```text
adco goal-plan <project_dir> --title <goal_title> --objective <goal_objective>
adco thread-plan <project_dir> --title <goal_title> --objective <goal_objective> --roles brand_client,copy_creative,qa_review
```

This creates:

```text
AD-creative/orchestrator/thread_lane_plan.md
AD-creative/orchestrator/thread_cleanup_<work_id>.md
AD-creative/agents/role_briefs/
AD-creative/agents/thread_prompts/<work_id>/
AD-creative/agents/receipts/<work_id>/
thread_registry.csv planned rows
agent_runs.csv planned rows
```

Rules:

```text
Use the generated prompts to create or reuse Codex Threads.
Keep at most 3 active worker/reviewer threads by default.
Workers return receipts; the main/control thread merges only accepted results.
After receipt reconciliation, archive the worker and update thread_registry.csv.
Client-visible material must not mention prompts, threads, workers, lane plans, or execution steps.
```

### ad-creative:profile-analyze

Use when meeting notes, transcripts, client discussions, or brand/company background should guide research or strategy.

Run:

```text
adco profile-analyze <project_dir> --source-id <SRC-ID> --brand <brand> --company <company>
```

This creates or updates:

```text
AD-creative/orchestrator/profile_knowledge/profile_subjects.csv
AD-creative/orchestrator/profile_knowledge/meeting_voice_map.csv
AD-creative/orchestrator/profile_knowledge/profile_insights.csv
AD-creative/orchestrator/profile_knowledge/profile_conflicts.csv
AD-creative/orchestrator/profile_knowledge/profile_current_truth.md
AD-creative/handoff/画像分析简报.md
```

Rules:

```text
Every profile claim should tie back to source_event evidence where possible.
Decision power, influence, personality, preference, and concern labels are candidate judgments until confirmed.
Do not turn internal profile analysis into client-visible claims unless separately approved.
If stakeholders disagree, record the disagreement in profile_conflicts.csv and propose a reconciliation path.
Research, strategy, copy, and visual lanes should read profile_current_truth.md before making assumptions about the client or brand.
```

### ad-creative:hygiene

Use before final status, after Codex Threads were used, or whenever the user reports dirty workspace / stale execution environment.

Run:

```text
adco hygiene <project_dir>
```

Rules:

```text
This command is read-only; do not delete user materials automatically.
Treat git tracked changes as intentional work until reviewed, not something to reset.
Treat __pycache__, .pytest_cache, *.pyc, unexpected untracked files, and unarchived thread rows as cleanup issues.
Use /tmp or AD-creative/workspaces/<work_id>/ for validation and scratch output.
After validation, clean Python caches and archive consumed Codex Threads before final status.
```

### ad-creative:start

Resume or start a project.

Steps:

```text
1. Read project.yml, current_truth.md, work_items.csv, artifact_index.csv, gate_log.csv.
2. Read 项目看板.md and 待你确认.md if present.
3. Report current stage, blockers, pending decisions, and next action.
4. Do not produce new creative work unless the user also asks to continue.
```

### ad-creative:add-materials

Handle new client materials, meeting notes, director notes, or feedback.

Steps:

```text
1. Register source event.
2. Decide whether it is initial, supplement, change, feedback, approval, rejection, or unknown.
3. Update requirements, gaps, current truth, decisions, and resolutions.
4. Mark conflicts and deprecated requirements.
5. Write client question script if needed.
6. Update 项目看板.md and 待你确认.md.
```

### ad-creative:next

Default forward motion.

Steps:

```text
1. Read current state.
2. If a human decision is blocking, update 待你确认.md and stop.
3. If search is needed, propose search plan and ask before searching.
4. If work can continue, create or advance work item.
5. If specialist work is needed, generate handoff packet.
6. Run required gate before moving stage.
7. If threads were used, run a thread cleanup / active-thread audit before final status.
8. Update project board.
```

### ad-creative:status

Read-only status.

Output:

```text
stage
active work
blocked work
pending user/client/director decisions
latest artifacts
next recommended action
```

### ad-creative:gate

Run a gate review on a stage or artifact.

Do not directly edit production artifacts.

Output:

```text
gate report
status
blocking issues
revision items
questions
affected artifacts
next state
```

### ad-creative:mine-skill

Generate project-local skill draft when a reusable path appears.

Never install globally without explicit user approval.

## Required Files

If missing, create from templates:

```text
AD-creative/orchestrator/project.yml
AD-creative/orchestrator/events.jsonl
AD-creative/orchestrator/source_events.csv
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
AD-creative/orchestrator/decisions.csv
AD-creative/orchestrator/resolutions.csv
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/orchestrator/version_map.csv
AD-creative/orchestrator/thread_registry.csv
AD-creative/orchestrator/profile_knowledge/profile_subjects.csv
AD-creative/orchestrator/profile_knowledge/meeting_voice_map.csv
AD-creative/orchestrator/profile_knowledge/profile_insights.csv
AD-creative/orchestrator/profile_knowledge/profile_conflicts.csv
AD-creative/orchestrator/profile_knowledge/profile_current_truth.md
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

## Gate Rules

Hard block if client-facing material contains:

```text
internal notes
prompts
execution steps
thread/lane/worker language
fake logo
fake packaging text
fake case study
untraced reference pretending to be real
contact sheet
low-quality collage
unregistered image asset
uneditable PPT content presented as editable
```

Client-visible copy must read like an advertising proposal, not an execution plan. Keep story, segment summary, brand mapping, timing, and key dialogue/key phrase where those are part of the concept. Do not compress story pages into generic slogans just to make layout easier.

Creative proposal drafts are internal, traceable strategy artifacts. Use `adco creative-proposal <project_dir> [--work-id <id>]` to create or update:

```text
AD-creative/creative/creative_directions.md
AD-creative/creative/option_matrix.csv
AD-creative/proposal_architecture/proposal_structure.md
AD-creative/client_review/slide_spec.md
```

Then run `adco creative-quality-gate <project_dir>`. This gate checks proposal completeness, evidence gaps, generic slogans, unsupported case/reference claims, product-to-benefit translation, differentiated directions, key visual/action, client choice rationale, and internal language leaks. `VALIDATION=PASS` is structural only; it is not creative quality approval.

## Visual Rules

Before generating or accepting visual assets:

```text
bind requirement
bind reference role
bind asset slot
define use case
define client visibility
record prompt or edit instruction
import image_gen output from CODEX_HOME/generated_images into AD-creative/visual_assets before referencing it
run visual-quality-gate before PPT/client packaging
run visual review gate
update asset manifest
```

## PPT / Review Rules

Before a client-review deck:

```text
create client_review_outline
create slide_spec
define PPT visual system
run PPT Gate on the actual exported PPTX/PDF package
keep unapproved images as placeholders
do not claim PPT editability before checking actual PPTX
do not call a deck final/current until PDF, preview, text extract, current_truth, artifact_index, and version_map agree
```

PPT Gate must explicitly check:

```text
text overflow or cropping
busy-image text contrast
repeated stills / repeated backgrounds
font legibility and font count
key dialogue / key phrase labels
timing labels such as second marks or segment durations
story-beat image differentiation
PPT editability on the exact current PPTX
```

## Feedback Rules

When new feedback arrives:

```text
register source event
classify supplement / change / rejection / approval
update feedback_map
mark affected requirements and artifacts
supersede old versions instead of overwriting
if the feedback changes a client-visible artifact, increment the version instead of reusing the old version filename
update next_version_plan
```

## Postmortem / Learning Rule

When a project has version overwrite, thread confusion, premature completion, or user-corrected delivery quality problems:

```text
1. Create AD-creative/gates/POSTMORTEM-*.md with evidence, root causes, and rule changes.
2. Update this skill or a project-local rule only after verifying the issue from project files.
3. Add a memory note only when the user explicitly asks to remember or prevent recurrence.
4. Re-run `adco validate <project_dir>` after updating project records.
```

## Validation Rule

After major stages, run:

```text
adco validate <project_dir>
```

Proceed only if:

```text
ERRORS=0
VALIDATION=PASS
```

## Search Rules

After three-council PASS, public official-source search may proceed without another authorization step.

Ask before search only when it uses private accounts, paid/login platforms, uploads client materials, or would expose confidential details.

Before searching, state:

```text
gap to solve
platforms to search
why these platforms
what happens if not searched
expected output
```

After search planning or reference registration, run:

```text
adco search-quality-gate <project_dir>
adco reference-pack-gate <project_dir>
```

## Handoff Rules

Every specialist agent gets:

```text
work_id
objective
input files
required outputs
allowed actions
forbidden actions
gate to pass
handoff back format
```

Every specialist returns:

```text
summary
files changed or produced
evidence
open questions
recommended next action
```
