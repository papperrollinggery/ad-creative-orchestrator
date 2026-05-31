# Image Job Spec

image_job_id: IMGJOB-QLO-001
linked_work_id: W-QLO-004
linked_requirement_ids: R-QLO-003;R-QLO-006
linked_reference_ids: REF-QLO-001;REF-QLO-004
slot_id: OP1-F01
use_case: internal key frame visual exploration
visibility: internal_only
ratio: 16:9

## Objective

Prepare an internal visual exploration slot for OP1 opening mood.

## Locked Inputs

```text
Direction: OP1 emotional city-to-nature
Scene: morning window, jacket fabric moving in wind
Product: lightweight sun-protective shell jacket
Client visibility: internal_only until confirmed
```

## Blockers

```text
No official product image.
No logo usage rule.
No AI visibility approval for client review.
```

## Prompt

Use the normalized prompt in:

```text
AD-creative/image_jobs/image_prompt_pack.json / IMGJOB-QLO-OP1-F01
```

Generation state:

```text
ready_internal
Do not use in client-facing material unless Visual Review Gate passes and user approves AI image visibility.
```

## Negative Constraints

```text
No fake logo.
No fake packaging text.
No invented brand mark.
No unreadable text.
No contact sheet.
No internal note.
No hard mountain or climbing scene.
```

## QA Gate

Visual Review Gate required.

## Output Path

```text
AD-creative/visual_assets/raw/
```
