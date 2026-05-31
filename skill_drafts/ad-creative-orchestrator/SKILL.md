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
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py sample <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py demo [project_dir]
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py --version
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py doctor
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py support-bundle <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py open-dashboard <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py validate <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py check
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py run <project_dir> --material <materials_path>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py goal-plan <project_dir> --title <goal_title> --objective <goal_objective>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py intake <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py add-reference <project_dir> --url <https_url> --title <title>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py search-quality-gate <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py reference-pack-gate <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py add-asset <project_dir> --file <image_file> --slot-id <slot_id> --requirement-id <requirement_id>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py import-imagegen <project_dir> --slot-id <slot_id> --selected
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py visual-quality-gate <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py export-pptx <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py check-pptx <project_dir> --file <pptx_file>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py client-pack-gate <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py handoff-readiness-gate <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py audit-dashboard <project_dir> --render
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py install-skill
```

Installed CLI equivalent:

```text
python3 -m pip install .
adco init <project_dir>
adco demo [project_dir]
adco sample <project_dir>
adco --version
adco doctor
adco doctor --json
adco support-bundle <project_dir>
adco open-dashboard <project_dir>
adco status <project_dir>
adco next <project_dir>
adco validate <project_dir>
adco validate <project_dir> --json
adco check
adco run <project_dir> --material <materials_path>
adco goal-plan <project_dir> --title <goal_title> --objective <goal_objective>
adco-check
adco-validate <project_dir>
make dist-check
make release-check
```

Gate commands enforce adversarial council:

```text
reference-pack-gate / search-quality-gate / visual-quality-gate / client-pack-gate / handoff-readiness-gate
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
8. Run `adco validate` or `ad_creative_operator.py validate` before reporting status.
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
7. Update project board.
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
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

## Gate Rules

Hard block if client-facing material contains:

```text
internal notes
fake logo
fake packaging text
fake case study
untraced reference pretending to be real
contact sheet
low-quality collage
unregistered image asset
uneditable PPT content presented as editable
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
define PPT visual system
run PPT Gate
keep unapproved images as placeholders
do not claim PPT editability before checking actual PPTX
```

## Feedback Rules

When new feedback arrives:

```text
register source event
classify supplement / change / rejection / approval
update feedback_map
mark affected requirements and artifacts
supersede old versions instead of overwriting
update next_version_plan
```

## Validation Rule

After major stages, run:

```text
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py validate <project_dir>
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
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py search-quality-gate <project_dir>
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py reference-pack-gate <project_dir>
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
