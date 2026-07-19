# Changelog

## Unreleased

- Replaced the fixed three-direction template path with an evidence-bound `creative-brief` → Sol/professional Specialist → independent Critic → `creative-import` contract; `creative-proposal` remains only as a deprecated brief alias.
- Added multi-format, source-preserving ingestion plus evidence chunks and a structured fact inventory; long inputs use an explicit aggregate budget and present facts no longer invert into missing gaps.
- Made default `adco run` lightweight and measurable: one dashboard render, no Council/Specialist/PPT/Client Pack/full validation, affected-scope validators only, and JSON phase timings/counters.
- Added Specialist Exchange v2 highest-common-version negotiation, minimal inline handoff/receipt contracts, v1-only provider fallback, independent ADCO adoption, and rejection of nested dispatch or outer readiness claims.
- Made source/package activation explicit-only and generated project agent policy conditional so ADCO/DIR source maintenance cannot recursively activate the ADCO project workflow.
- Reworked chat-native key-visual review around ADCO's own advertising craft: proposal role, customer moment, product proof, brand memory, focusable region judgments, target-format placement, and creative revision intent instead of a generic status-card flow.
- Bound real-candidate review to ADCO's current project/version, artifact registry, source event, human/client authorization, and exact-asset channel checks; illustrative fixtures now use a separate fail-closed path and cannot certify production claims.
- Fixed confirmation echoes to show recorded choice, preserved content, required rechecks, and next step explicitly, and bound writeback validation to the action actually selected instead of the first action in the surface.
- Make chat-native asset review distinguish illustrative placeholders from real candidates, derive user-visible usability from source, authorization, and channel-fit status, and block misleading placeholder approval paths.
- Fixed Codex chat delivery so generated ADCO fragments are mounted with the native `::codex-inline-vis` directive instead of being left as invisible local HTML files.
- Aligned inline surfaces with the host Visualizations design system, added real 736/320 light/dark keyboard and follow-up browser audits, and separated host-visible acceptance from file/browser checks.
- Added task-based routing across Mermaid, Codex inline Visualizations, Creative Production image Widgets, optional Data Analytics evidence, and fullscreen MCP Apps without turning ADCO into a dashboard.
- Added an OpenAI Visualizations-first chat interaction contract for ADCO status, P0-P8 logic, blocking decisions, option comparison, exact asset/PPT review, feedback impact, and confirmation echo.
- Added a versioned, hash-bound visualization spec/writeback harness with thread-scoped fragments, human-readable follow-up actions, complete Markdown/table/Mermaid fallback, responsive accessibility checks, and fail-closed source/authority validation.
- Documented how optional Data Analytics evidence and file preview/annotations complement Visualizations without expanding or duplicating the existing local dashboard.

## 0.3.2 - 2026-07-13

- Refreshed README, install, roadmap, security, runbook, and operating descriptions to the current v0.3.x control-plane semantics and removed retired colon-prefixed pseudo-command guidance from current onboarding docs.
- Packaged the public README, changelog, install guide, adoption patterns, release plan, and first-run transcript so `adco docs` exposes real documents in installed-package mode.
- Added source-to-package published-document parity and wheel-content checks so stale or missing descriptions fail the release gate.

## 0.3.1 - 2026-07-12

- Made Thread dispatch proof immutable per work/lane/attempt and kept host projections outside worker scope baselines.
- Bound Film Quality Gate evidence to exact adopted specialist artifact ids, paths, and hashes without treating domain QA as client readiness.
- Hardened section-aware brief extraction, removed cross-domain scenario defaults, and kept fresh review artifacts/ThreadOps rows out of legacy debt.
- Clarified that Film Quality Gate scans active control-plane film artifacts while separately validating adopted specialist outputs and domain QA evidence.
- Clarified agent route names and their `adco` CLI entrypoints.

## 0.3.0 - 2026-07-11

- Rebuilt Human Workspace indexes around exact-current truth, canonical path deduplication, resolvable links, physical-file discovery, and explicit missing or unregistered evidence.
- Added schema-v2 control-plane migrations with traceable artifact tombstones, legacy quarantine, current-versus-legacy diagnostics, and strict legacy validation when required.
- Added fail-closed FinalDelivery inventory and explicit rename or supersession reconciliation without silently rewriting protected baselines.
- Hardened Thread convergence around observable progress, absolute deadlines, a single bounded extension, and at most one bounded rescue.
- Split the operating Skill into focused references and added complete managed-tree installation manifests and source/package/install parity checks.
- Expanded adversarial regression coverage for legacy migration, FinalDelivery safety, Thread identity, Human Workspace projection, and global Skill synchronization.

## 0.2.0 - 2026-07-10

- Made client-readable proposal structure and explicit client confirmation first-class, with fail-closed outline, language, visual, package, and send-readiness Gates.
- Hardened ThreadOps dispatch, worker identity, receipt adoption, bounded convergence, and cleanup evidence so incomplete or mismatched work cannot be reported as complete.
- Added immutable version-chain checks and FinalDelivery protection to prevent stale aliases, silent overwrites, and unsafe cleanup of user deliverables.
- Added a neutral DIRcreative specialist exchange with scoped handoff, receipt, adoption, authorization, host-integrity, and read-only return validation.
- Expanded installation, packaged-resource parity, diagnostics, support bundles, release checks, and post-install verification for non-developer operation.

- Added `goal-plan` command for durable goal iteration records.
- Added adversarial council Gate policy: clean Gates without council evidence downgrade to `PARTIAL_PASS`.
- Added Goal tab to the local dashboard.
- Added `tools/test_goal_workflow.py` regression checks.
- Added `tools/run_checks.py` unified verification entry point.
- Added open-source readiness files: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `ROADMAP.md`, `.gitignore`, `Makefile`, `requirements.txt`.
- Added GitHub Actions check workflow plus issue and pull request templates.
- Added `pyproject.toml` and console scripts: `adco`, `adco-init`, `adco-validate`, `adco-check`.
- Added source install guide.
- Added `make install-smoke` for editable install verification.
- Added public demo script and desktop/mobile dashboard screenshots.
- Added `adco sample` bundled sample project generator and regression check.
- Added `tools/test_gates.py` structured Gate regression coverage.
- Added GitHub release checklist with local and remote gates.
- Added real-world adoption pattern documentation.
- Added optional positive Gate fixtures for real PNG visual QA and editable PPTX client-pack PASS paths.
- Added generated first-run demo transcript and stale-check verification.
- Improved README public quickstart, value proposition, and safety model.
- Added `make release-check` local release gate.
- Added packaged runtime assets plus normal `pip install .` smoke verification.
- Updated project-local skill draft with installed CLI and release-check entry points.
- Added `adco doctor` install/resource/dependency/release diagnostic command.
- Added `adco --version` for issue reports and install diagnostics.
- Added `make dist-check` wheel content inspection for packaged templates, skill draft, metadata, and entry points.
- Upgraded GitHub Actions to run the full `make release-check` gate on Python 3.10 and 3.12.
- Hardened issue and pull request templates with version, doctor, reproduction, and release-gate evidence.
- Added `adco support-bundle` for sanitized bug-report diagnostics without client material text.
- Added `adco open-dashboard` to render and open the local operation dashboard directly.
- Added `adco demo` as a one-command sample project and dashboard demo.
- Updated the public roadmap to reflect current local release readiness and remote-release next steps.
- Added `adco validate` and `adco check` aliases for the existing validation and verification workflows.
- Updated public docs and templates to use `adco demo`, `adco validate`, and `adco check` as the primary paths.
- Added JSON output for `adco doctor`, `adco status`, and `adco validate`.
- Added `adco init` as the unified project initialization subcommand.
- Improved `adco status` with next action, active work, open gaps, and pending confirmations.
- Added `adco next` for a compact next safe action decision.
- Kept JSON diagnostics verified while reducing `adco check` output noise.
- Added `adco release-status` for local release readiness and remote blocker summaries.
- Added `adco docs` for local documentation paths and quickstart commands.
- Refreshed contributor, release, roadmap, and non-developer quickstart docs around the current `adco` CLI.
- Made wheel distribution inspection deterministic with no build isolation, a timeout, and a static manifest fallback.
- Added a docs command regression check to keep onboarding docs on the installed `adco` path.
- Published the public GitHub remote and verified Actions on Python 3.10 and 3.12.
- Verified a public clone trial from install to demo validation.
- Added GitHub-first onboarding, project URLs, repository topics, and status badges.
- Added `adco quickstart` for one-command first run, validation, dashboard opening, and next-step output.
- Added `adco quickstart --json` and covered it in source, editable install, and package install checks.
- Added `adco support-bundle --json` for machine-readable sanitized diagnostics.
- Added `adco audit-dashboard --json` for machine-readable dashboard usability checks.
