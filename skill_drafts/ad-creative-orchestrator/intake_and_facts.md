# Intake and Fact Reference

Read this file only for material ingestion, evidence chunks, fact inventory,
requirements, conflicts, and gaps.

## Runtime boundary

The Content Surface parses and records evidence so the agent can reason from the
material. It does not invent creative directions, approve client claims,
dispatch a specialist, or infer that an image/video was understood when only its
file metadata was inspected.

Use:

```text
adco run <project> --material <file_or_folder> [--material <file_or_folder> ...]
adco intake <project>
```

Never run these commands on the ADCO or DIRcreative source repository.
All material paths and the character budget are checked before project creation.
Missing, empty/unsupported, recursive, or symlinked material fails with a nonzero
structured result and no project write.

## Material placement and organization

Treat every supplied material path as a reference to the existing physical
bytes. Register and inspect it in place. Do not copy the same deck, video,
reference library, or source folder into `AD-creative/`, a meeting package, a
concept folder, or `version_archive` merely to make it discoverable.

After intake produces a useful summary, `adco run` performs one read-only check
over the supplied material scope and project root. If it finds loose root files
or exact byte duplicates, surface one organization question. Do not interrupt
content work, create a report, or reorganize automatically. On request, use:

```text
adco organize-plan <project> [--deep] [--save] [--json]
```

Without `--save`, the command writes nothing. With `--save`, it atomically
replaces the single `AD-creative/orchestrator/storage_plan.json`; it never creates
numbered plan copies. Applying any move, rename, hardlink, or deletion remains a
separate explicitly confirmed action. FinalDelivery is always protected.

## Evidence flow

```text
source event
-> parser registry
-> source-preserving chunks
-> structured fact candidates
-> fact inventory with evidence refs
-> requirements + true gaps/conflicts/blocking unknowns
-> concise intake summary (not creative output) + affected-scope validators
```

The parser registry accepts Markdown/text, CSV, JSON, YAML, DOCX, PPTX, PDF,
SRT/VTT, images, and video files. Images and video are registered with metadata
and an explicit inspection status; metadata-only intake must not claim visual or
audio understanding. Media hashes are streamed once. Image metadata uses a small
technical allowlist and excludes camera identity, timestamps, GPS, comments, and
other unneeded EXIF fields.

Text is chunked by source structure with stable source path, parser kind,
ordinal, content hash, and source-event provenance. The default aggregate budget
is 2,000,000 characters. A budget overflow or parser failure is explicit; no
file is silently truncated to its first 12,000 characters and no 16-line fact
limit is used as the source of truth.

Repeated `run` reuses a source only after successful intake when the material's
file/tree fingerprint and character budget still match. It reads the bytes to
check their hash but skips parsing and duplicate evidence creation. File edits,
folder additions/removals, budget changes and failed parsing require intake
again. Replaced evidence invalidates its old inferred facts and unconfirmed
requirements; retained confirmations need rechecking against the new evidence.

An exported model-analysis request binds the complete current evidence snapshot.
Return `evidence_snapshot_sha256` unchanged with the response. Import rejects a
missing or stale binding before writing facts or gaps; export a new request after
source changes. The parser's extracted fields are candidates, so inspect the
actual source before creative reasoning even when intake checks pass.

External absolute material paths are not written to public project records.
`source_events.csv` and evidence use `local-source://<source_event_id>` aliases;
the absolute lookup stays only in owner-readable `.adco-local/source_paths.json`.
ADCO opens the project and `.adco-local` through stable directory descriptors,
atomically enforces the dedicated `.adco-local/.gitignore` as deny-by-default,
and verifies the same directory/file binding before returning. Symlink swaps,
non-regular files, malformed versions, unreadable maps, and concurrent map
replacement fail closed. Support diagnostics are not written while that private
state is invalid; a registered `local-source://` alias with a missing map is also
invalid. Client-pack manifests hard-exclude `.adco-local/**`, omit all inputs when
the map cannot be trusted, and open each candidate through a project-rooted,
component-by-component `O_NOFOLLOW` descriptor chain. Privacy scanning, hashing,
size capture, and final parent/file inode verification share that binding. One
root descriptor remains open across source-map, alias-reference, and candidate
reads so a real-directory project-root replacement also blocks. ZIP-based
formats add member-count, per-member, and total-uncompressed limits. PDFs scan
extracted visible text and metadata through a streaming output cap; the Python
fallback is process-isolated with an address-space limit. Timeout, limit,
unavailable parser, or invalid input fails closed. Specialist manifests hard-
exclude `.adco-local/**`.

## Fact and gap semantics

Facts are structured as present, missing, conflicting, or unknown and retain the
evidence chunk ids that support the state. A gap is created only for:

```text
missing fact
conflicting fact
unknown fact that blocks the current decision
```

Do not convert a present statement into a missing gap. For example, “客户已提供产品图”
is evidence that the product-image fact is present, not a request for a missing
product image. Conflicts preserve every competing evidence reference and remain
open until reconciled.

Missing product images, logo, or AI client-visibility permission is recorded as a
non-blocking follow-up on the Content Surface so unaffected internal reasoning can
continue. The same unresolved fact becomes blocking when the project enters a
client-visible Delivery Surface. Conflicting evidence remains blocking on either
surface. Closing a gap row cannot override an unresolved blocking fact: promotion
reopens the gap and Delivery readiness reads the fact inventory directly.

Primary records:

```text
AD-creative/orchestrator/source_events.csv
AD-creative/orchestrator/evidence_chunks.jsonl
AD-creative/orchestrator/fact_inventory.jsonl
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
```

`adco run --json` reports characters read, evidence chunks, parser errors,
budget overflows, the intake summary, phase timings, scoped validators, and the
read-only organization review. The
default Dashboard count is zero. Treat an overflow or parser error as `CHECK`;
inspect the intake evidence before advancing.
