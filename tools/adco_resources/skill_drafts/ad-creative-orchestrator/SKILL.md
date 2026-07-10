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

## Default Lightweight Spine

Use one control thread and project files by default. Complexity alone does not justify worker Threads, a council, or a fixed role roster.

Shortest safe path:

```text
messy materials -> intake/current truth -> requirements + gaps
-> creative-proposal (customer-readable text framework + proposal skeleton)
-> human review of the text framework
-> confirm-client-outline (pre-approval file hash + canonical content digest + current-state hash)
-> client-outline-gate PASS
-> immutable export-pptx version
-> exact-current PDF/preview/text extract
-> client language + visual layout + hash-bound asset authorization
-> client-pack-gate (ready for independent review, not send-ready)
-> independent manual review receipt
-> explicit exact-version send authorization
-> client-send-readiness-gate (never sends)
```

The double-click launcher stops after the text framework. It must not create PPT automatically.

Runtime phases are fixed: `P0 truth/lock -> P1 client outline -> P2 hash confirmation -> P3 creative/reference/neutral specialist -> P4 immutable PPT -> P5 language/visual/authorization/editability -> P6 fresh Client Pack binding -> P7 independent review/send readiness (never sends) -> P8 feedback/next version`. Do not merge P4, P6, or P7 into one delivery stage.

Use `inline` work unless isolation, genuinely parallel specialist work, or independent cold review materially improves the result. Use real Codex Threads only when explicitly requested or when a bounded isolated worker/reviewer is necessary. A thread ceiling is not a staffing target.

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
client-visible assets have independent authorization receipts bound to their exact file hash and scope
the client outline confirmation is bound to the exact current outline hash
the current Client Pack binding still matches every exact-current package input
independent manual review is bound to the exact current version, PPTX hash, and package digest
client-send readiness has a separate explicit send authorization bound to the same package digest
```

If new user feedback arrives after completion, reopen the stage as revision work. Do not keep claiming the previous goal is still complete.

### Version Safety Rule

Never overwrite a client-visible version file as the only copy of that version.

`adco export-pptx` writes a new immutable `AD-creative/ppt/exports/client_review_vNNN.pptx` and refuses to overwrite an existing target. Before changing any legacy exported file whose name includes a version such as `v1`, `v2`, or `final`:

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

Default decision: `no thread`. Select only the minimum bounded worker/reviewer needed for an explicit isolation, parallelism, or independence reason. Do not start a broad team for ordinary intake, proposal drafting, gates, or status work.

Default limits:

```text
max active worker/reviewer threads at one time: 3
max broad council threads without explicit user approval: 5
main thread is the only integration owner
execution workers own exact write_scope
read-only lanes are only research/review/cold-review
workers must not export final PPT/PDF
default loop_mode is sequential
allowed loop modes are sequential, rfc_dag, continuous_pr, and infinite only for bounded internal exploration
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

### Optional Role Roster

Only after Thread mode is justified, prefer a stable role roster rather than one-off task threads. Do not instantiate the roster by default.

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
action_space
observation_contract
error_recovery_contract
context_budget
iteration_budget
eval_gate
worker_recommendation
worker_recommendation_reason
loop_state
replay_trigger
freeze_trigger
helper_mode
helper_policy
allowed_helper_kinds
helper_write_boundary
helper_evidence_required
helper_failure_policy
helper_invocations
helper_input_refs
helper_output_refs
helper_artifacts
helper_validation_result
helper_adopted_by_worker
helper_failure_reason
worker_synthesis
```

Use these environment modes:

```text
read_only: default for research, copy review, strategy review, QA, and council lanes
isolated_workspace: for PPT/image/story drafts in non-git material projects
worktree: for git repositories or text/code projects where branches can be merged safely
main_only: for integration, version_map, artifact_index, current_truth, gate_log, final export
```

In non-git PPT/material projects, do not pretend git worktree protection exists. Use `AD-creative/workspaces/<work_id>/` as an isolated drafting area, then let the main thread import accepted files.

Use these loop modes:

```text
sequential: default; finish one bounded lane step before the next handoff
rfc_dag: use only when an RFC-style dependency graph is written in the lane plan
continuous_pr: use only for controlled PR/check cycles with explicit validation commands
infinite: bounded internal exploration only; must declare iteration_budget, freeze_trigger, replay_trigger, and stop_condition
```

Safe-stop and recovery rules:

```text
safe_stop: stop before client-visible send, paid/private/upload actions, destructive edits, global install, validation failure, or missing receipt proof
replay_trigger: validation_result FAIL, missing receipt schema, stale evidence, out-of-scope edit, or reopened feedback
freeze_trigger: thread confusion, wrong thread, heat/cost spike, budget exceeded, repeated same root cause, or cleanup request
stop_condition: receipt reconciled, eval_gate passed or blocker recorded, adoption_decision recorded, and cleanup action planned
```

Stateless secondary helper invocation contract:

```text
Model: CONTROL main thread -> real Codex Thread worker/reviewer -> optional stateless secondary helper invocation inside that worker.
Default helper_mode: none.
Allowed helper_mode: stateless_secondary_helper.
Allowed helper kinds: image_generation, OCR, layout_lint, asset_resize, reference_extraction.
Helpers may be stateless helper/subagent-style calls inside the worker, but they are not Codex Threads or substitute workers/reviewers.
Helpers have no thread_id, no thread_registry.csv row, no write_scope, and no adoption authority.
Helpers cannot touch current_truth, version_map, artifact_index, gate_log, final exports, client send, uploads, paid/login/private-account actions, or client-visible status.
The L1 worker records helper_invocations, helper_input_refs, helper_output_refs, helper_artifacts, helper_validation_result, helper_adopted_by_worker, helper_failure_reason, and worker_synthesis in its receipt.
The L1 worker adopts or rejects helper output first; main/control adopts or rejects only through the L1 worker receipt.
Do not implement real imagegen/OCR/helper calls in this repo unless a separate task explicitly grants that tool action; this contract only validates evidence.
```

Workers may write only their receipt unless the lane plan grants exact writable paths. The main thread is the only default owner of:

```text
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/version_map.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/ppt/exports/
```

### Agent Agency Integration

If an optional reusable staff library such as `$HOME/.claude/agents` exists, it may be used as source material. It is never required for ADCO operation.

Use it this way:

```text
1. Build a task signature from the current project: brand, product, talent, platform, deliverable, stage, risk, and required evidence.
2. Search the discovered staff library by filename and frontmatter description for matching staff.
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
human_workspace_drift: do not let the six top-level human folders stay empty while real work is buried in AD-creative; update `目录索引.md` or place approved copies in the matching 00-05 folder
internal_language_leak: client-visible pages must not mention prompts, execution steps, threads, lane plans, or worker roles
prompt_only_receipt: production worker receipts must list changed files or return BLOCKED with evidence
missing_adoption_proof: main/control must record adoption_decision and rejection_reason before merging or discarding worker output
named_skill_skip: when the user names a local skill or specialist skill, read that SKILL.md before production and convert its rules into current-task gates with `adco preflight-skill`
browser_asset_skip: before declaring images missing or generating replacements, inspect both local files and browser-held Grok/ChatGPT/ImageGen assets and record with `adco preflight-asset` or `adco browser-asset-intake`
fake_thread_dispatch: planned:* thread ids are placeholders only; real execution requires real_thread_id, title verification, dispatch receipt, worker receipt, adoption/rejection, and cleanup evidence
worker_self_report_as_proof: worker-declared files_changed/write_scope is not host proof; reconcile against the host-captured dispatch baseline and persist a hash-bound host scope proof
missing_client_outline: no PPT builder before `adco client-outline-gate <project>` passes
unconfirmed_client_outline: a complete outline is still blocked until `confirm-client-outline` records explicit user/client confirmation bound to its exact hash
client_language_leak: client export is blocked by `adco client-language-gate <project>` if prompt/thread/worker/AI/gate/internal execution language appears
asset_source_drift: PPT images must appear in `asset_current_manifest.csv` with source, platform, conversation, local_file, hash, original_or_processed, approval, direct_client_use, used_in_slide, and qa_flags
asset_authorization_self_stamp: approval=PASS or a notes token is not authorization; require asset_authorizations.csv receipt bound to asset hash, scope, approver, time, and evidence
fake_package_format: extensions and hand-filled gate_status are not evidence; exact current PPTX/PDF/preview/text extract must parse and match registered hash/size/derivation
stale_client_pack_binding: any exact-current package input change invalidates the previous package digest; rerun client-pack-gate before manual review/send readiness
manual_review_self_stamp: generating an unchecked checklist is NOT_RUN, not PASS; require a separate independent receipt bound to current version/hash
goal_plan_self_review: a goal plan or main-thread council row is not independent adversarial review evidence
Duffy_v2_regression: customer decks may be 22-45+ low-density decision pages; never collapse them into short pitch cards or production tables
validation_scope_misuse: `VALIDATION=PASS` means structure and traceability only; it is not creative quality, client language, visual taste, asset authorization, or send approval
final_delivery_overwrite: user-placed files in `05_最终交付_FinalDelivery` are protected by default; only hash-register with `adco final-delivery-lock <project>`
unbounded_loop: infinite mode is not a live infinite loop; it is bounded internal exploration only
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
adco migrate-control-plane <project_dir> --dry-run
adco migrate-control-plane <project_dir>
adco agency-audit <project_dir>
adco creative-proposal <project_dir> --work-id <WORK-ID>
adco creative-proposal <project_dir> --json
adco creative-quality-gate <project_dir>
adco preflight-skill <project_dir> --work-id <WORK-ID> --requested-skill <skill> --skill-path <SKILL.md> --rules-read "<rules>" --derived-gates "<gates>"
adco specialist-handoff <project_dir> --work-id <WORK-ID> --profile-id dircreative.film-preproduction --objective "<objective>" --input-artifact <ART-ID> --expected-output film.story_package --descriptor <descriptor.json>
adco specialist-adopt <project_dir> --handoff <handoff.json> --receipt <receipt.json> --decision <adopt|partial_adopt|reject|defer> --reason "<reason>" --map-output <PROVIDER-ID=AD-creative/path>
adco preflight-asset <project_dir> --work-id <WORK-ID> --source-scope "<local/browser/download/generated scope>"
adco confirm-client-outline <project_dir> --confirmed-by "<human/client>" --confirmed-at <iso_time> --evidence-ref "<user_confirmation:id|client_confirmation:id>"
adco client-outline-gate <project_dir>
adco client-language-gate <project_dir>
adco asset-current-manifest <project_dir>
adco browser-asset-intake <project_dir> --work-id <WORK-ID> --source Grok --browser-evidence "<evidence>"
adco goal-plan <project_dir> --title <goal_title> --objective <goal_objective>
adco thread-plan <project_dir> --title <goal_title> --objective <goal_objective> --roles brand_client,copy_creative,qa_review
adco dispatch-record <project_dir> --work-id <WORK-ID> --lane-id <LANE-ID> --real-thread-id <thread_id> --title-verified-at <iso_time> --dispatch-evidence "<readback evidence>" --absolute-deadline-at <iso_time>
adco thread-observe <project_dir> --work-id <WORK-ID> --lane-id <LANE-ID> --state <active_with_progress|silent|finalizing_receipt|thread_not_converged|rescue_dispatched> --observed-at <iso_time> --evidence "<readback>"
adco thread-reconcile <project_dir> --work-id <WORK-ID> --lane-id <LANE-ID> --receipt-path <receipt> --adoption-decision <ADOPT|PARTIAL_ADOPT|REJECT|BLOCKED> --reconciled-at <iso_time> --cleanup-action "<action>"
adco profile-analyze <project_dir> --source-id <SRC-ID> --brand <brand> --company <company>
adco hygiene <project_dir>
adco intake <project_dir>
adco add-reference <project_dir> --url <https_url> --title <title>
adco search-quality-gate <project_dir>
adco reference-pack-gate <project_dir>
adco add-asset <project_dir> --file <image_file> --slot-id <slot_id> --requirement-id <requirement_id>
adco import-imagegen <project_dir> --slot-id <slot_id> --selected
adco visual-quality-gate <project_dir>
adco visual-layout-gate <project_dir>
adco export-pptx <project_dir>
adco check-pptx <project_dir> --file <pptx_file>
adco client-pack-gate <project_dir>
adco client-send-readiness-gate <project_dir>
adco final-delivery-lock <project_dir>
adco dedupe-audit <project_dir>
adco cleanup-plan <project_dir>
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
adco migrate-control-plane <project_dir> --dry-run
adco migrate-control-plane <project_dir>
adco agency-audit <project_dir>
adco preflight-skill <project_dir> --work-id <WORK-ID> --requested-skill <skill> --skill-path <SKILL.md> --rules-read "<rules>" --derived-gates "<gate>"
adco specialist-handoff <project_dir> --work-id <WORK-ID> --profile-id dircreative.film-preproduction --objective "<objective>" --input-artifact <ART-ID> --expected-output film.story_package --descriptor <descriptor.json>
adco specialist-adopt <project_dir> --handoff <handoff.json> --receipt <receipt.json> --decision <adopt|partial_adopt|reject|defer> --reason "<reason>" --map-output <PROVIDER-ID=AD-creative/path>
adco preflight-asset <project_dir> --work-id <WORK-ID> --source-scope "<local/browser/download/generated scope>"
adco confirm-client-outline <project_dir> --confirmed-by "<human/client>" --confirmed-at <iso_time> --evidence-ref "<user_confirmation:id|client_confirmation:id>"
adco client-outline-gate <project_dir>
adco client-language-gate <project_dir>
adco asset-current-manifest <project_dir>
adco browser-asset-intake <project_dir> --work-id <WORK-ID> --source Grok --browser-evidence "<evidence>"
adco visual-layout-gate <project_dir>
adco export-pptx <project_dir>
adco check-pptx <project_dir> --file <pptx_file>
adco client-pack-gate <project_dir>
adco client-send-readiness-gate <project_dir>
adco handoff-readiness-gate <project_dir>
adco final-delivery-lock <project_dir>
adco dedupe-audit <project_dir>
adco cleanup-plan <project_dir>
adco dispatch-record <project_dir> --work-id <WORK-ID> --lane-id <LANE-ID> --real-thread-id <thread_id> --title-verified-at <iso_time> --dispatch-evidence "<readback evidence>" --absolute-deadline-at <iso_time>
adco thread-observe <project_dir> --work-id <WORK-ID> --lane-id <LANE-ID> --state <active_with_progress|silent|finalizing_receipt|thread_not_converged|rescue_dispatched> --observed-at <iso_time> --evidence "<readback>"
adco thread-reconcile <project_dir> --work-id <WORK-ID> --lane-id <LANE-ID> --receipt-path <receipt> --adoption-decision <ADOPT|PARTIAL_ADOPT|REJECT|BLOCKED> --reconciled-at <iso_time> --cleanup-action "<action>"
adco profile-analyze <project_dir> --source-id <SRC-ID> --brand <brand> --company <company>
adco hygiene <project_dir>
adco-check
adco-validate <project_dir>
make dist-check
make release-check
```

Gate commands:

```text
creative-quality-gate / client-outline-gate / client-language-gate / reference-pack-gate / search-quality-gate / visual-quality-gate / visual-layout-gate / client-pack-gate / client-send-readiness-gate / handoff-readiness-gate
```

Creative/reference/search/visual/client-pack stage gates downgrade clean PASS to PARTIAL_PASS when independent adversarial evidence for the exact stage target is missing. Client outline, client language, visual layout, asset manifest, send readiness, dedupe, cleanup, and final delivery lock gates hard-block on their own evidence rules. Handoff readiness is an internal-operations continuity check and treats content-stage gaps as warnings.

Use `sample` when a new user needs a runnable local project without real client materials.

Before PPT builder or client export:

```text
The human/client reviews the text framework first. `confirm-client-outline` then binds that explicit confirmation to the exact current outline hash; `client-outline-gate` must PASS before PPT builder. Every row needs page_title, body_copy, client_confirmation_point, material_role, visual_slot, and visual_asset_status. Detailed Duffy V2-style customer decks may be 22-45+ pages, but every page must stay low-density and decision-readable.
client-language-gate must PASS before client-visible export.
asset-current-manifest must list source, platform, conversation, local_file, hash, original_or_processed, direct_client_use, used_in_slide, and qa_flags for PPT images. `approval=PASS` alone is never authorization; client use requires a hash-bound row in asset_authorizations.csv.
browser-asset-intake or preflight-asset must run before replacement generation when the user says Grok/ChatGPT/ImageGen/browser assets exist.
visual-layout-gate must run before client-pack-gate and cannot PASS without the exact current PPTX plus a real preview. It checks distortion/crop/small image/crowding/nested-card/report-feel/short copy/image-copy mismatch/repeated-image misuse/portrait-landscape mismatch.
final-delivery-lock must hash-register user-placed `05_最终交付_FinalDelivery` files before cleanup/final status.
dedupe-audit and cleanup-plan are review-only; they never delete, move, or overwrite files.
VALIDATION=PASS is structure/traceability only, not creative quality, client language, visual approval, asset authorization, or send approval.
client-pack-gate can only mean ready for independent human review. It writes an immutable input manifest plus current package binding; any bound input change makes that binding stale. Only client-send-readiness-gate may report send readiness, and it requires manual review and send authorization bound to the same fresh package digest. It never sends.
handoff-readiness-gate means only that a non-developer operator can continue the project internally. It does not require or prove PPT, Client Pack, FinalDelivery, or send readiness.
```

Then use:

```text
AD-creative/handoff/操作台.html
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/客户追问话术.md
AD-creative/gates/THREE-COUNCIL-READINESS_report.md
00_项目资料_ProjectMaterials/目录索引.md
01_参考资料_References/目录索引.md
02_重要素材_KeyAssets/目录索引.md
03_阶段成果_WorkInProgress/目录索引.md
04_客户审阅_ClientReview/目录索引.md
05_最终交付_FinalDelivery/目录索引.md
```

### ad-creative:run

One-command project operation.

Use when the user gives a project directory plus messy client materials and expects Codex to proceed until a real decision point.

Steps:

```text
1. If project files are missing, initialize from /Users/jinjungao/work/ad-creative-orchestrator/templates/project without overwriting existing files.
2. Register provided materials as source events.
3. Classify each source as initial, supplement, change, feedback, approval, rejection, director_note, or unknown.
4. Merge owned sections into current_truth without replacing Current Version Truth or user-added sections.
5. Create the customer-readable text framework/proposal skeleton with `creative-proposal`; record material gaps and client questions.
6. Stop for human/client review of the text framework; record explicit confirmation with `confirm-client-outline`, then require `client-outline-gate` PASS before any PPT.
7. Update the six top-level `目录索引.md` files so Project Materials, References, Key Assets, Work In Progress, Client Review, and Final Delivery show where the current files live.
8. Decide whether search is needed and write search_plan if needed.
9. Continue through the next safe internal stage only if no human decision is blocking.
10. Run `adco validate` before reporting status. Do not auto-export PPT.
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
Receipts must include the real thread_id plus action_space, observation_contract, error_recovery_contract, context_budget, iteration_budget, eval_gate, worker_recommendation, loop_state, replay_trigger, freeze_trigger, stop_condition, files_changed, validation_result, dirty_state_impact, manifest/index updates, QA/gate status, open questions, recurrence guard, and cleanup actions. Main/control records adoption_decision or rejection_reason separately.
Receipts that set helper_mode to stateless_secondary_helper must include helper_invocations, helper_input_refs, helper_output_refs, helper_artifacts, helper_validation_result, helper_adopted_by_worker, helper_failure_reason, and worker_synthesis.
Production worker receipts cannot be prompt-only; execution workers must produce declared files or return BLOCKED with evidence.
Dispatch captures a host-side scope baseline after the real thread id is bound. Reconciliation compares the actual host diff to the receipt and exact write_scope, then persists a hash-bound host scope proof. Worker self-report alone is never adoption evidence.
The lane plan defaults to loop_mode sequential. rfc_dag and continuous_pr require explicit dependency/check contracts. infinite is allowed only as bounded internal exploration.
Replay failed lanes with tighter acceptance criteria. Freeze new worker creation on thread confusion, wrong-thread behavior, repeated same root cause, budget breach, or cleanup request.
Live Codex Thread creation remains main/control responsibility; this repo only generates contract artifacts and prompts. If real Threads or isolated writable scope are unavailable, stop with TOOL_BLOCKED instead of falling back to subagents or role-play.
Stateless secondary helper invocations may be used only inside a real worker for bounded local subtasks; they are not Threads, have no thread id or registry row, and cannot make adoption decisions.
After receipt reconciliation, archive the worker and update thread_registry.csv.
Client-visible material must not mention prompts, threads, workers, lane plans, or execution steps.
Fixed poll count is only an observation budget. Record active_with_progress, silent, or finalizing_receipt; allow at most one reasoned extension with an absolute deadline and at most one rescue. Rescue gets its own dispatch proof and receipt path. New visible activity cannot extend forever. Only silence past the deadline or no receipt after convergence reminder becomes thread_not_converged.
```

### ADCO ↔ DIRcreative Specialist Exchange

ADCO owns client/business truth, adoption, versions, PPT, FinalDelivery, and send readiness. DIRcreative owns film story/script/shot/visual-bible/prompt/QA specialist output. DIRcreative recommendations never become ADCO adoption automatically.

Use the neutral protocol:

```text
protocol_id: adco.specialist-exchange
contract_version: 1.0
profile_id: dircreative.film-preproduction
default execution_mode: inline
nested_dispatch_allowed: false
```

Create a handoff with `specialist-handoff`, then validate the returned receipt and record a separate ADCO decision with `specialist-adopt`. Input and output artifacts must be project-relative, indexed, hash-bound, and inside exact scopes. Provider outputs must be non-empty single-link files, never symlinks or hardlinks; provider id, kind, canonical path, and physical inode are each unique. `needs_user` question ids must be non-empty and unique. A `read_only` handoff grants only its exact receipt path and can close only as receipt-only `needs_user` / `blocked` / `failed` plus ADCO `defer` / `reject`, with no adopted output or Gate advance. `prompt_only` keeps generation unauthorized with no ref; `real_media` requires project-contained structured user/client authorization evidence bound to the host baseline. A descriptor must explicitly advertise `real_media`; omission defaults to `prompt_only`, so DIRcreative v1 remains prompt-only without a DIR-side change. Packaged canonical JSON Schemas are executed before adoption and again by project validation; an index/hash update cannot legalize a schema-invalid receipt or adoption. Descriptor versions may evolve within compatible `1.x` while explicitly supporting base contract `1.0`. A provider may declare a required receipt extension; ADCO copies its id/version into handoff acceptance and rejects receipts that omit the negotiated extension. This lets DIRcreative evolve its domain receipt independently without changing ADCO ownership. `needs_user` returns structured questions to ADCO; the specialist does not contact the client. Domain QA PASS never means client-ready, PPT-ready, FinalDelivery-ready, send-ready, project-complete, or control-plane-updated. Use `codex_thread` only when explicitly selected and only with a verified ThreadOps lane/real thread id/host scope proof. Never hardcode a DIR repository path, DIR package version, `.dircreative/runs`, or DIR validator path.

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
6. Update the relevant top-level `目录索引.md` files.
7. Update 项目看板.md and 待你确认.md.
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
8. Update the relevant top-level `目录索引.md` files.
9. Update project board.
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
AD-creative/orchestrator/specialist_exchange/exchange_index.csv
AD-creative/orchestrator/profile_knowledge/profile_subjects.csv
AD-creative/orchestrator/profile_knowledge/meeting_voice_map.csv
AD-creative/orchestrator/profile_knowledge/profile_insights.csv
AD-creative/orchestrator/profile_knowledge/profile_conflicts.csv
AD-creative/orchestrator/profile_knowledge/profile_current_truth.md
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/visual_assets/asset_authorizations.csv
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

Copywriting, proposal, strategy, client handoff, and gate output should follow humanizer principles without pasting a separate writing guide into project files:

```text
prefer concrete customer moment, product benefit, evidence, risk, and next action
remove chatbot residue such as "of course", "hope this helps", "please let me know"
replace vague authority such as "experts say" or "industry reports show" with a source id or a question
avoid exaggerated significance such as "pivotal", "crucial role", "marks a shift", "重塑格局"
avoid not-only/but framing in English or Chinese
avoid repeated em dash, en dash, or -- rhythm in proposal and client-facing text
avoid generic AI vocabulary clusters such as "seamless", "vibrant", "showcase", "underscore", "格局", "赋能", "焕新"
```

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
record explicit user/client confirmation with confirm-client-outline, bound to the exact outline hash
require client-outline-gate PASS
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
