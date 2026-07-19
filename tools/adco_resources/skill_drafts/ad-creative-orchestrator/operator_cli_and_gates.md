# Operator CLI and Gate Reference

Read this file when invoking ADCO, choosing the next phase/Gate, building a non-developer handoff, or interpreting status.

## Non-developer entrypoints

The local launcher prompts for a project folder, materials, and goal, then opens `AD-creative/handoff/操作台.html`. Its default `run` path stops after evidence intake, fact/gap updates, handoff refresh, one dashboard render, and affected-scope validation. It must not auto-run Council, generate creative directions, dispatch a specialist, build a client outline/PPT/Client Pack, or run full delivery validation.

Installed and source CLI behavior must match. Core commands:

```text
adco init <project>
adco quickstart [project] [--json]
adco sample <project>
adco demo [project]
adco status <project> [--json]
adco next <project> [--json]
adco validate <project> [--json] [--strict-legacy]
adco check
adco run <project> --material <path> [--material <path> ...] [--max-total-chars <n>] [--json]
adco migrate-control-plane <project> [--dry-run] [--json]
adco agency-audit <project>
adco creative-brief <project> [--work-id <id>] [--json]
adco creative-import <project> --file <candidate.json> [--json]
adco creative-review <project> [--json]
adco creative-proposal <project> [--work-id <id>] [--json]
adco creative-quality-gate <project>
adco confirm-client-outline <project> --confirmed-by <human> --confirmed-at <iso> --evidence-ref <ref>
adco client-outline-gate <project>
adco client-language-gate <project>
adco preflight-asset <project> --work-id <id> --source-scope <scope>
adco browser-asset-intake <project> --work-id <id> --source <platform> --browser-evidence <ref>
adco asset-current-manifest <project>
adco search-quality-gate <project>
adco reference-pack-gate <project>
adco visual-quality-gate <project>
adco visual-layout-gate <project>
adco export-pptx <project>
adco check-pptx <project> --file <pptx>
adco client-pack-gate <project>
adco client-send-readiness-gate <project>
adco final-delivery-lock <project>
adco final-delivery-reconcile <project> --old-path <path> --new-path <path> --kind <rename|supersession> --confirmed-by <human> --confirmed-at <timezone-aware-iso> --evidence-ref <project-relative-structured-confirmation.json> [--version-id <id>]
adco dedupe-audit <project>
adco cleanup-plan <project>
adco handoff-readiness-gate <project>
adco profile-analyze <project> [--source-id <id>] --brand <brand> --company <company>
adco hygiene <project>
adco support-bundle <project> [--json]
adco open-dashboard <project>
adco audit-dashboard <project> [--render] [--json]
adco doctor [--json]
adco release-status [--json]
adco docs [--json]
adco install-skill [--target <dir>]
```

Thread and specialist commands are documented in their dedicated references.

`install-skill` owns only the current packaged files it writes. Its schema-v2 install manifest binds current managed paths to SHA-256 digests for parity checks, but a writable target-side manifest is never trusted as deletion authority. Stale, user-modified, and unrelated files are always preserved and reported for explicit cleanup; installation never auto-deletes them. A root symlink is accepted only for the canonical `~/.codex/skills/ad-creative-orchestrator` to `~/.skillshub/ad-creative-orchestrator` compatibility layout, checked before path resolution.

## Phase/Gate order

Do not merge immutable export, Client Pack binding, and send readiness into one stage.

| Phase | Required fact/evidence | Exit condition |
|---|---|---|
| P0 | sources, truth, gaps, schema, lifecycle, FinalDelivery inventory | current blockers explicit |
| P1 | customer-readable framework and outline | every client page decision-readable |
| P2 | explicit human/client confirmation bound to exact outline digest | `client-outline-gate` PASS |
| P3 | creative/reference/specialist outputs | domain Gates and adoption evidence |
| P4 | immutable versioned PPTX | no overwrite; current version registered |
| P5 | exact PDF/preview/text/editability, language, layout, asset authorization | all exact-current checks fresh |
| P6 | immutable Client Pack input manifest and binding digest | ready for independent review only |
| P7 | independent receipt plus separate send authorization on same digest | send-ready claim only; never sends |
| P8 | feedback map and next-version plan | old package invalidated; revision route explicit |

Creative/reference/search/visual/client-pack Gates downgrade a clean result when exact-target adversarial evidence is absent. Outline, language, layout, asset authorization, FinalDelivery, dedupe/cleanup safety, and send readiness hard-block on their own evidence rules.

`handoff-readiness-gate` means an operator can continue internally. It does not prove PPT, FinalDelivery, Client Pack, or send readiness.

## Agent route mapping

The labels in this section are agent-level routes, not additional CLI
subcommands. Use these command mappings when operating through `adco`:

| Agent route | CLI entrypoint |
| --- | --- |
| `start` / `status` | `adco status <project>`; `start` means a read-only resume/status route. |
| `add-materials` | `adco run <project> --material <file_or_folder>`. |
| `next` | `adco next <project>`. |
| `gate` | The stage-specific Gate command, such as `adco film-quality-gate <project>`. |

### `run`

1. Initialize only missing template files without overwriting existing files.
2. Register materials as initial/supplement/change/feedback/approval/rejection/director note/unknown.
3. Parse supported formats into source-preserving evidence chunks without the old 12,000-character/16-line truncation path.
4. Update the fact inventory, requirements, true gaps/conflicts, handoff files, and all six human indexes.
5. Render the dashboard exactly once.
6. Run only validators affected by changed evidence/fact/requirement/gap artifacts and report the scoped plan plus phase timings.
7. Stop with the next safe command. Do not run Council, Specialist Exchange, creative generation/import, PPT, Client Pack, or full `adco validate` automatically.

### `start` / `status`

Read project.yml, current truth, work items, artifacts, versions, Gates, board, and pending confirmations. Report stage, active/blocked work, decisions, latest artifacts, current P0, grouped legacy debt, and next safe action. Do not create new creative output unless asked.

### `add-materials`

Register the source event, classify it, update requirements/gaps/truth/decisions/resolutions, mark conflicts/deprecated facts, update client questions, refresh human indexes, board, and pending confirmations.

### `next`

Stop when a human decision blocks. Otherwise plan search if needed, advance one work item, create a bounded specialist handoff if justified, run the required Gate, refresh indexes/board, and clean Thread state if used.

### `gate`

Review the exact stage/artifact without directly editing production output. Return report, status, blockers, revisions, questions, affected artifacts, and next state.

## Required control-plane files

The template must include at least:

```text
AD-creative/orchestrator/project.yml
AD-creative/orchestrator/control_plane_schema.json
AD-creative/orchestrator/events.jsonl
AD-creative/orchestrator/source_events.csv
AD-creative/orchestrator/evidence_chunks.jsonl
AD-creative/orchestrator/fact_inventory.jsonl
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
AD-creative/orchestrator/decisions.csv
AD-creative/orchestrator/resolutions.csv
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/orchestrator/version_map.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/orchestrator/thread_registry.csv
AD-creative/orchestrator/final_delivery_lock.csv
AD-creative/orchestrator/specialist_exchange/exchange_index.csv
AD-creative/visual_assets/asset_current_manifest.csv
AD-creative/visual_assets/asset_authorizations.csv
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

Migration manifests are written only when legacy evidence exists. They are immutable evidence, not a replacement for current control-plane rows.

## Gate semantics

- `creative-import`: structural and provenance validation for 2-3 post-Critic candidates; rejects stale/unbound evidence and duplicate mechanisms, and flags weak brand ownership.
- `creative-review`: deterministic structure/language lint; an independent creative Critic remains required.
- `creative-quality-gate`: downstream legacy proposal completeness and client-safety checks; it is not Sol generation, independent Critic judgment, or client approval.
- `client-outline-gate`: complete page framework plus explicit hash-bound human/client confirmation.
- `client-language-gate`: blocks prompts, execution/Thread language, internal notes, fake/unsupported claims.
- `search-quality-gate` and `reference-pack-gate`: source role, provenance, live evidence, borrow/do-not-copy boundary.
- `visual-quality-gate`: asset source, quality, authorization, and slot suitability.
- `visual-layout-gate`: exact PPTX plus real preview; distortion, crop, scale, crowding, report feel, copy/image mismatch, repeated-image misuse, orientation.
- `film-quality-gate`: scans exact active physical `film.*` artifact rows in the ADCO control plane, including path and hash; planned/pending rows are not current scan targets. Adopted specialist outputs are additionally resolved by exact artifact id/path/hash, while `domain.film_qa` remains receipt/QA evidence. Blocked creative or invalid exchange evidence blocks downstream advance.
- `client-pack-gate`: fresh exact-current input binding; ready for independent review only.
- `client-send-readiness-gate`: independent review and separate send authorization on the same fresh package digest; never sends.

Any bound input change invalidates previous Gate evidence and package digest.

## Stop points

Stop before client send, public release, paid/login/private-account actions, external upload of client materials, destructive changes, global skill install, AI asset client visibility without authorization, or any failed current/active validation.
