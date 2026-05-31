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
```

Expected output:

```text
requirements.csv
gaps.csv
current_truth.md
待你确认.md
操作台.html
NEXT_ACTION
NEXT_STATUS
```

Gate:

```text
Brief Gate must be non-BLOCKED before reference planning.
```

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
AI/generated images stay internal_only until visual QA and explicit client visibility approval.
```

## Pattern 4: Client Review Pack

Use when preparing an editable PPT review package.

```bash
adco export-pptx <project_dir>
adco check-pptx <project_dir> --file <project_dir>/AD-creative/ppt/client_review_draft.pptx
adco client-pack-gate <project_dir>
```

Gate:

```text
Client Pack Gate must PASS before any human sends material externally.
```

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

## Stop Rules

Pause before:

- sending client-facing files
- uploading client material to external services
- paid/login/private account actions
- marking generated images client-visible
- installing global skills
- destructive overwrite or deletion
