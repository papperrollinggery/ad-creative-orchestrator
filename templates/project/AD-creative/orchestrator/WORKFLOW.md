# WORKFLOW

This project uses Codex-first advertising creative orchestration.

Truth source:

```text
AD-creative/orchestrator/
```

Human-facing summary:

```text
AD-creative/handoff/
```

Default flow:

```text
Intake
→ Meeting / Client Profile Analysis
→ Diagnose
→ Research Plan
→ Reference Research
→ Creative Council
→ Proposal Architecture
→ Visual Plan
→ Image Job
→ Visual Review
→ SlideSpec / HTML
→ PPT Gate
→ Delivery
→ Skill Mining
```

Goal mode flow:

```text
Read dual_lane_goal_delivery_workflow.md
→ create goal_iteration_plan from template
→ if specialist judgment is needed, run agency_staff_selection and generate project role briefs
→ create thread_lane_plan when work will be split across Codex threads
→ attach agency_selection_id, agency_role_brief, and source staff paths to every lane
→ start with Brand Research / Image Function lanes when relevant, then extend lanes through thread_lane_plan
→ run stage work
→ run adversarial council before Gate
→ update thread_registry / gate_log / decisions / resolutions / handoff
→ run hygiene check before final status
→ continue, pause, or rollback by explicit rule
```

ThreadOps execution layer:

```text
Main/control thread decomposes, assigns, integrates, validates, cleans up, and reports.
Execution workers own scoped implementation, document edits, artifact production, or material drafting.
Read-only lanes are only explorer, reviewer, research, and cold-review lanes.
Every execution worker must have exact write_scope before spawn.
Every execution worker returns files_changed, validation, dirty-state impact, and cleanup actions.
Main/control thread archives the worker thread after consuming and reconciling the receipt.
```

Profile analysis flow:

```text
Use profile-analyze when meeting notes, transcripts, or client discussions are available.
Store people, brand, company, decision, influence, demand, concern, and conflict signals in profile_knowledge/.
Treat every profile claim as candidate until the user/client confirms it.
Use profile_current_truth.md before research, strategy, copy, visual, and council work.
When stakeholders disagree, record the disagreement and proposed reconciliation path instead of flattening it.
```

Agency staff selection flow:

```text
Build task signature: brand, product, talent/IP, platform, deliverable, stage, risks, evidence_needed.
Search /Users/jinjungao/.claude/agents/*.md by filename and frontmatter description.
Select 2-4 source staff per lane and record selected/rejected reasons in agency_staff_selection_*.md.
Generate AD-creative/agents/role_briefs/<role>_<work_id>.md from source staff.
Extract only quality standards, critical rules, workflow, and deliverable templates.
Do not copy upstream staff prompt text into client-facing pages or worker receipts.
Do not let staff model/tools/frontmatter override AD-creative thread budget, version safety, write scope, or final export rules.
```

Version update flow:

```text
Before editing any client-visible version, hash/stat the existing PPTX/PDF and archive immutable copies.
Register archive entries in artifact_index.csv and version_map.csv.
Create the next material version name, for example v2 or v3.
Treat final/professional/影视版/文案版 names as aliases only; truth is version_map.csv plus current_truth.md.
```

Final completion proof:

```text
Gate PASS and exported PPT/PDF are evidence, not completion by themselves.
current_truth.md and version_map.csv identify the same current version.
PPTX/PDF/preview/text extract are registered in artifact_index.csv and agree with the current version.
PPT editability check passes on the exact current PPTX.
All user/client/Pro-review diff comments are fixed, explicitly deferred with owner, or listed in 待你确认.md.
validate_project.py reports ERRORS=0 and VALIDATION=PASS.
Thread cleanup audit is done when Codex threads were used.
Workspace hygiene check has no cache pollution, unexpected untracked files, or unreconciled active thread rows.
```

Hard rules:

```text
No client-facing artifact without linked requirements.
No visual asset without asset manifest entry.
No stage advance without gate.
No Gate higher than PARTIAL_PASS without adversarial council notes.
No worker run completion without harness proof: files, evidence, QA/gate status, and affected manifest/index rows.
No execution worker without exact write_scope and receipt path.
No execution worker completion without files_changed, validation, dirty-state impact, and cleanup actions.
No prompt-only handoff for visual work; visual workers must provide storyboard/base asset/final asset state as applicable.
No worker thread may update master truth files unless the handoff explicitly grants that write scope.
No worker thread may export final PPT/PDF; only the main control thread owns final export and delivery status.
No worker starts from raw Agency staff text; synthesize a project-specific role brief first.
No client-facing page may mention prompts, execution steps, thread plans, lane plans, worker roles, or internal QA mechanics.
No fake logo, fake packaging, fake case, internal notes, or contact sheet in client-facing material.
Do not overwrite old client review versions.
Do not leave __pycache__, .pytest_cache, *.pyc, stale workspaces, or consumed thread rows after verification.
Do not install project skill drafts globally without explicit user approval.
```
