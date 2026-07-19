# Project Rules for Ad Creative Orchestrator

These rules apply only when this root contains a valid
`AD-creative/orchestrator/project.yml` and matching
`AD-creative/orchestrator/control_plane_schema.json`, and the user explicitly
invokes `$ad-creative-orchestrator` for the initialized advertising project.

They do not apply to the `ad-creative-orchestrator` source repository, the
`Paperrolling-DIRcreative-SKILL` source repository, Skill maintenance, a Skill
Benchmark, AGENTS/SKILL/Schema/test changes, ordinary code refactoring, ordinary
advertising requests, or any task where ADCO was not explicitly invoked. In those
cases, use the task's normal workflow and do not create an ADCO control plane.

## Required Operating Surface

- When the applicability conditions above hold, use the explicitly invoked
  `$ad-creative-orchestrator` skill for this project.
- Work through `AD-creative/orchestrator/` and `AD-creative/handoff/`.
- Do not rely on chat memory as the operating record. Durable decisions, gaps, gates, artifacts, and handoff state must be written into project files.
- Keep the six top-level human folders (`00_项目资料_ProjectMaterials/` through `05_最终交付_FinalDelivery/`) useful. If source files or artifacts live under `AD-creative/`, update the matching `目录索引.md` so a human can find the current material, WIP, client-review, and final-delivery entries without digging through the control plane.

## Source Of Truth

Treat these files as the project source of truth:

- `AD-creative/orchestrator/current_truth.md`
- `AD-creative/orchestrator/version_map.csv`
- `AD-creative/orchestrator/artifact_index.csv`
- `AD-creative/orchestrator/requirements.csv`
- `AD-creative/orchestrator/gaps.csv`
- `AD-creative/orchestrator/gate_log.csv`

## Client-Visible Materials

Client-visible materials must not contain internal comments, prompts, thread names, worker names, lane plans, fake logos, fake packaging copy, raw imagegen prompts, untraceable references, or unapproved AI images.

Client-visible versions must not overwrite old versions. Before changing a client-visible PPTX, PDF, preview, or text extract, archive the old file under `AD-creative/ppt/exports/version_archive/` and update `version_map.csv` plus `artifact_index.csv`.

Do not replace all of `current_truth.md` during intake. Update owned sections and preserve Current Version Truth plus user-added sections. `adco export-pptx` writes a new immutable `client_review_vNNN.pptx`; it must never refresh or overwrite an existing version.

`VALIDATION=PASS` only means the project structure and traceability checks passed. It does not mean creative quality, visual taste, strategic quality, or client-ready quality passed.

Private/paid/login search, image generation, external upload, and final send actions require explicit authorization. Public official-source research may follow the project search plan.

Delegate film craft only when the current task belongs to this valid ADCO project,
the user or current Work Item explicitly requires a professional film artifact,
and a valid Specialist handoff exists. Words such as video, script, storyboard,
commercial, advertising film, or Prompt never trigger DIRcreative by themselves.
When those conditions hold, use the versioned `adco.specialist-exchange` handoff.
ADCO remains the only owner of client truth, adoption, version files, PPT,
FinalDelivery, and send readiness. Specialist QA or recommendation is never client
approval.

Before PPT, complete the customer-readable text framework and pass `client-outline-gate`. The launcher stops at this text checkpoint and does not auto-generate PPT.

`approval=PASS` is not asset authorization. Client-visible asset use requires a receipt in `asset_authorizations.csv` bound to the exact asset hash and scope. An unchecked manual review checklist is `NOT_RUN`, not PASS.

## Gates Before Handoff

Before delivery or handoff, run `adco validate`.

Run stage gates when relevant:

- `adco search-quality-gate <project>`
- `adco reference-pack-gate <project>`
- `adco creative-quality-gate <project>`
- `adco visual-quality-gate <project>`
- `adco visual-layout-gate <project>`
- `adco client-pack-gate <project>`
- `adco client-send-readiness-gate <project>`
- `adco handoff-readiness-gate <project>`

## Codex Threads

Default to no Thread. When isolation, bounded parallelism, independent review, or an explicit user request justifies Codex Threads, the main thread is the only integration owner. Workers must have explicit write scope, return receipts containing their real thread_id, and stop after their assigned task. The main thread records adoption/rejection separately.

Fixed poll counts are observation budgets, not automatic failure. Distinguish active_with_progress, silent, and finalizing_receipt; allow at most one reasoned bounded extension with an absolute deadline and one bounded rescue.

Workers should not directly publish, send client materials, update final status, or overwrite final files unless the main thread explicitly assigned that exact file scope.

After worker results are consumed, clean up or archive thread records and record the cleanup in `thread_cleanup_*.md` inside the project.
