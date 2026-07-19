# Adoption Patterns

Status: usable patterns

## Pattern 1: Creative Strategist Intake

Use when the first client brief is messy and incomplete.

```bash
adco demo /tmp/adco-sample --no-open
adco run <project_dir> --material <brief_file_or_folder>
adco status <project_dir>
adco status <project_dir> --json
adco next <project_dir>
adco docs
```

Expected output:

```text
requirements.csv
gaps.csv
current_truth.md
evidence_chunks.jsonl
fact_inventory.jsonl
待你确认.md
NEXT_ACTION
NEXT_STATUS
DOCS_MODE
```

The default route emits a content answer and runs affected-scope validators only.
It renders no dashboard unless requested and does not run Council, create a
Thread, dispatch a specialist, create a client outline/PPT/Client Pack, or run
full validation.

No Gate is required for an internal intake answer. Add a Gate only when the
requested output crosses the corresponding delivery boundary.

## Pattern 2: Brand Research Lane

Use when the team needs traceable references before creative direction.

```bash
adco goal-plan <project_dir> --title "Brand research lane" --objective "Build a traceable reference pack before creative proposal."
adco search-quality-gate <project_dir>
adco reference-pack-gate <project_dir>
```

Required evidence:

```text
reference_cards.csv
reference_shortlist.md
do_not_copy.md
gate reports
adversarial council row
```

## Pattern 3: Image Workflow Lane

Use when AI/image work must stay internal until approved.

```bash
adco add-asset <project_dir> --file <image_file> --slot-id <slot_id> --requirement-id <requirement_id>
adco visual-quality-gate <project_dir>
```

Default rule:

```text
AI/generated images stay internal_only until visual QA and an independent authorization receipt bind the exact asset hash, use scope, approver, time, and evidence. `approval=PASS` or a notes token is not authorization.
```

## Pattern 4: Client Review Pack

Use when preparing an editable PPT review package.

```bash
# First produce and review an exact client_outline.csv as an explicit project task.
adco confirm-client-outline <project_dir> --confirmed-by "<human/client>" --confirmed-at <iso_time> --evidence-ref "<user_confirmation:id|client_confirmation:id>"
adco client-outline-gate <project_dir>
adco export-pptx <project_dir>
adco check-pptx <project_dir> --file <project_dir>/AD-creative/ppt/exports/client_review_vNNN.pptx
adco client-pack-gate <project_dir>
```

Gate:

```text
`client-pack-gate` only creates a package digest that is ready for independent review. Any exact-current input change invalidates it.
```

Only when preparing an actual send, collect an independent review receipt and explicit send authorization bound to that same fresh digest, then run:

```bash
adco client-send-readiness-gate <project_dir>
```

The command never sends.

## Pattern 5: Non-Developer Handoff

Use when the operator wants a read-only project surface.

```bash
adco audit-dashboard <project_dir> --render
adco handoff-readiness-gate <project_dir>
```

Primary files:

```text
AD-creative/handoff/操作台.html
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/delivery/manual_review_checklist.md
```

This Gate proves internal operator continuity only. It does not require or prove PPT, Client Pack, FinalDelivery, or send readiness.

## Pattern 6: DIRcreative Specialist Exchange

Use when film-preproduction judgment is needed without coupling ADCO to DIR internals.

```bash
adco specialist-handoff <project_dir> --work-id <WORK-ID> --profile-id dircreative.film-preproduction --objective "<objective>" --input-artifact <ART-ID> --expected-output film.story_package --descriptor <descriptor.json>
adco specialist-adopt <project_dir> --handoff <handoff.json> --receipt <receipt.json> --decision partial_adopt --reason "<reason>" --map-output <PROVIDER-ID=AD-creative/film/output.md>
```

ADCO selects the highest contract version supported by both sides. V2 is preferred and uses a minimal inline-only handoff/receipt; it rejects nested dispatch and provider claims about client/PPT/FinalDelivery/send/project readiness. A provider supporting only `1.0` falls back to the unchanged v1 descriptor/extension/authorization/ThreadOps/receipt contract. ADCO always keeps adoption, version, PPT, FinalDelivery, and send authority.

## Stop Rules

Pause before:

- sending client-facing files
- uploading client material to external services
- paid/login/private account actions
- marking generated images client-visible
- installing global skills
- destructive overwrite or deletion
