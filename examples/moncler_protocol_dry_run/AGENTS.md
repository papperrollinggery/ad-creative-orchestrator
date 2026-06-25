# Project Rules for Ad Creative Orchestrator

These rules apply to this project root and every subdirectory.

## Required Operating Surface

- Use `ad-creative-orchestrator` for this project.
- Work through `AD-creative/orchestrator/` and `AD-creative/handoff/`.
- Do not rely on chat memory as the operating record. Durable decisions, gaps, gates, artifacts, and handoff state must be written into project files.

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

`VALIDATION=PASS` only means the project structure and traceability checks passed. It does not mean creative quality, visual taste, strategic quality, or client-ready quality passed.

Real search, imagegen, and final send actions still require human confirmation.

Video, commercial-film, storyboard, and video-prompt modules should be handed to `dircreative` or a dedicated specialist film workflow instead of being forced through the normal deck workflow.

## Gates Before Handoff

Before delivery or handoff, run `adco validate`.

Run stage gates when relevant:

- `adco search-quality-gate <project>`
- `adco reference-pack-gate <project>`
- `adco creative-quality-gate <project>`
- `adco visual-quality-gate <project>`
- `adco client-pack-gate <project>`
- `adco handoff-readiness-gate <project>`

## Codex Threads

When using Codex Threads, the main thread is the only integration owner. Workers must have explicit write scope, return worker receipts, and stop after their assigned task. The main thread must review receipts before adopting work.

Workers should not directly publish, send client materials, update final status, or overwrite final files unless the main thread explicitly assigned that exact file scope.

After worker results are consumed, clean up or archive thread records and record the cleanup in `thread_cleanup_*.md` inside the project.
