# Migration, Lifecycle, Human Workspace, and FinalDelivery Reference

Read this file before operating on a legacy project or changing lifecycle, migration, validation, Human Workspace, or FinalDelivery behavior.

## Control-plane schema

Current projects declare schema version in both:

```text
AD-creative/orchestrator/project.yml
AD-creative/orchestrator/control_plane_schema.json
```

`adco migrate-control-plane` is additive and evidence-preserving:

1. Resolve lexical/symlink aliases to one canonical project lock identity, open
   the owner-only lock directory and regular lock file with `O_NOFOLLOW`, take an
   exclusive ADCO migration lock, then hold an open project-directory binding for
   every relative snapshot and write. Build one read-only plan and hash the
   complete project input snapshot without following directory symlinks. A root
   rename/symlink swap is reported while the originally opened directory remains
   the only write root. Every managed parent is then reopened component by
   component with `O_NOFOLLOW`; CSV, truth, schema, and manifest updates use
   atomic dirfd-relative writes, so a managed-subdirectory swap blocks instead of
   redirecting a write outside the project.
2. If the plan has a blocker, return `blocked_before_write=true` and write nothing.
3. Re-hash immediately before the first project write; any concurrent delta
   returns `migration_inputs_changed` with no ADCO write or manifest attempt.
4. Apply the already computed plan without a second independent derivation.
   Safe template materialization is the first apply step. If a managed path
   changes after that step, the run writes no migration manifest and reports
   `blocked_before_write=true` only when no template file or surface changed;
   otherwise it reports `partial_apply=true` so a retry is explicit and honest.
5. Add required files/columns without deleting rows only after the plan is clear.
6. Normalize short CSV rows and classify artifact lifecycle using controlled values.
7. Backfill legacy Current Package only when it resolves to one version and one artifact per declared exact-current slot.
8. Quarantine pre-v2 ThreadOps rows with a hash of the raw row.
9. Capture only allowlisted low-risk legacy-row messages (for example old gate/work references) in the hash-bound baseline. Authorization, client visibility, send/readiness, path containment, current truth, and FinalDelivery errors can never downgrade; any later delta remains `P1/active` or `P0/current`.
10. Write the migration manifest and set schema versions only for an applied run.

The migration must be idempotent. A second run over unchanged migrated inputs must not rewrite the artifact index, registry, truth, or manifest.

## Structured migration blockers

Return P0/current blockers instead of choosing or inventing truth when:

- there are multiple Current Version Truth or Current Package sections;
- a legacy package value matches zero or multiple artifacts;
- the package version matches zero or multiple current version rows;
- the control schema is malformed;
- raw ThreadOps quarantine evidence cannot be bound.

A blocker is returned in the CLI/JSON result without creating or updating a
migration manifest. After an operator explicitly establishes one valid Current
Version Truth bound to `version_map` and the artifact index, a rerun may apply the
migration and record that successful attempt. A blocked preflight is not a state
change and is not persisted as an attempt. Do not add a blank Current Version
Truth to make validation appear cleaner.

## Artifact lifecycle

Controlled values:

```text
active
pending
superseded
withdrawn
archived
deprecated
rejected
removed
legacy_unresolved_tombstone
legacy_unknown
```

Lifecycle fields are backward-compatible additions:

```text
lifecycle_state
original_path
cleanup_ref
removed_at
removal_reason
superseded_by
status_reason
```

Rules:

- Preserve legacy `status` and reason text in `status_reason`/`removal_reason`.
- Preserve the actual original artifact path in `original_path` when known.
- A cleanup/dedupe/removal summary is evidence only; store it in `cleanup_ref`.
- Status families such as `cleaned_removed`, `cleanup_removed`, and `removed_by_cleanup` are unresolved tombstones when the only path is cleanup evidence.
- For unresolved tombstones, leave `original_path` blank. Never infer it from artifact id, filename, cleanup report, version, or neighboring rows.
- Reverse supersession links may populate `superseded_by`; never delete the old row.
- Invalid lifecycle values are diagnostics, not an invitation to drop the row.
- Fresh `internal_review` and `ready` artifacts are active current-view work; fresh `planned` artifacts are pending work. Neither is legacy debt.

Ordinary inactive rows are excluded from current views but preserved in compact history. An inactive row referenced by exact current truth becomes P0/current.

## ThreadOps migration

Do not decide a row is current merely because a previous migration appended empty proof columns.

Use the pre-migration schema boundary:

- Existing non-empty ThreadOps rows in a pre-v2 project become `schema_state=legacy_quarantined`.
- Bind each to `legacy_evidence_sha256`, `legacy_quarantine_reason`, and a `legacy_raw_ref` into the migration manifest.
- Keep related raw `agent_runs` evidence in the same manifest.
- Validator skips quarantined rows for current ThreadOps dispatch/receipt/matching checks and reports one grouped legacy-debt issue.
- Invalid or missing quarantine hash evidence is P0/current.
- New v2 rows use `schema_state=current` and remain under full ThreadOps validation.
- Every new planned or dispatched row writes `schema_state=current`; migration must not quarantine a row created by the current writer merely because it has not returned a receipt yet.

`--strict-legacy` makes grouped legacy debt blocking; it does not change classification or mutate data.

`current_version_id` may intentionally point to an internal `draft`, `internal_review`, or `ready` version. These current-view states are valid for ordinary work but are not FinalDelivery authorization. Explicit inactive/unknown states remain P0 when selected as current. FinalDelivery supersession is stricter: its version must be the exact `current` row bound through Current Version Truth.

## Human Workspace v2 algorithm

For each of the six top-level human folders:

1. Read relevant registered rows.
2. Read exact-current ids from the single Current Version Truth section.
3. Resolve the exact current version through `version_map.csv`.
4. Canonicalize every project-local path to normalized project-relative form.
5. Deduplicate by canonical path with deterministic ordering.
6. Scan actual physical files recursively.
7. Merge registered/physical collisions into the registered row; physical scan only proves existence.
8. Add unmatched physical files as `LOCAL/UNREGISTERED`.
9. Render existing local targets as relative Markdown links; percent-encode destinations so Unicode, spaces, and parentheses resolve.
10. Render exact-current rows first, then active registered rows, then local/unregistered rows.
11. Render inactive rows in compact history.

Never silently filter an exact-current row. Unknown artifact id, any lifecycle other than `active` (including pending/legacy_unknown), empty path, missing file, ambiguous version row, or non-current-view version status is a prominent P0 note.

Excluded physical entries:

```text
README.md
目录索引.md
.DS_Store
hidden/managed metadata
```

FinalDelivery current view excludes Gate reports, checklists, previews, text extracts, editability reports, manifests, and locks. It still inventories them as metadata where needed, but never labels them user final. Metadata classification uses explicit artifact types and precise tokens; real office/media deliverable suffixes default to deliverable, so names such as `Brand_Manifesto_Final.pdf` are not excluded merely because they contain `manifest` as a substring.

The renderer writes only the six index files. It must not copy, move, rename, symlink, hardlink, or create aliases.

## FinalDelivery inventory

`final_delivery_lock.csv` keeps immutable baseline fields plus reconciliation metadata:

```text
path, sha256, size_bytes, mtime, registered_at
inventory_state, reconciliation_state, reconciliation_kind
reconciles_lock_id, supersedes_lock_id
confirmed_by, confirmed_at, evidence_ref, evidence_sha256
host_attestation_ref, host_attestation_sha256
version_id, supersedes_version_id, status_reason
```

Inventory algorithm:

1. Read existing baselines without refreshing path/hash/size/time.
2. Check every protected baseline.
3. Scan new physical files even when an old baseline is missing or changed.
4. Persist new deliverables as `pending_reconciliation` before returning the old-baseline blocker.
5. Record generated metadata as `metadata_excluded`, `protected=no`.
6. If a pending row was created during a prior blocker, re-evaluate it and promote it only after every old-baseline violation is resolved.
7. If there is no old-baseline violation, promote newly inventoried deliverables to immutable protected baselines.
8. Never touch the physical files.

## Rename and supersession reconciliation

Reconciliation requires a declared human identity (automation/agent identities are rejected), an explicit timezone-aware confirmation time, and an existing project-relative structured JSON receipt. The receipt binds protocol/version, decision, confirmer/time, kind, old lock/path/hash, new path/hash/artifact, new and superseded version ids, and one confirmed user/client `source_event_id`. A separate host-only attestation under `AD-creative/orchestrator/host_attestations/` binds that receipt's path/hash to the real `codex_app.read_thread` readback (`thread_id`, `user_message_id`, user-message hash, authority, verified time/status). Both files must be non-symlink, non-hardlinked, and independently SHA-bound in the lock row. Project files alone cannot cryptographically prove a person: only the host main thread may create the attestation after live readback; a worker-authored attestation is rejected during scope adoption. Paths must remain physically inside FinalDelivery and may not traverse symlinks.

Rename:

```text
old path missing
new path exists and is already inventoried
old and new sha256 are identical
kind=rename
```

Supersession:

```text
old path missing
new path exists and is already inventoried
old and new sha256 differ
kind=supersession
new version_id is mandatory
new row supersedes the old lock id
version_id is the exact current version and its artifact_id equals the new path's unique active artifact
supersedes_version_id resolves through the old path's unique artifact/version and matches the new version's supersession chain; ambiguity blocks
```

Never change the old baseline row. Reconciliation is recorded on the new inventory row through `reconciles_lock_id`/`supersedes_lock_id`. A same-hash replacement should not be mislabeled as a new version; a different hash can never be accepted as a rename.

## Validator ordering

Structured issues contain:

```text
severity: P0/P1/P2/P3
scope: current/active/legacy
code
message
evidence
```

Sort current FinalDelivery and exact-current P0 first. Then active findings. Then grouped legacy debt. Backward-compatible callers still receive `list[str]` containing blocking current/active messages; structured CLI/JSON exposes all issues.

Detect without deleting:

- malformed CSV/JSON/control schema;
- invalid lifecycle values;
- unresolved or malformed tombstones;
- stale/missing exact-current artifacts;
- pending/uninventoried/changed FinalDelivery files;
- invalid rename/supersession receipts;
- unbound legacy ThreadOps quarantine;
- migration manifest blockers.
