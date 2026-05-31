---
name: ad-visual-review-gate
description: Use for advertising creative projects when generated images, reference boards, moodboards, storyboard frames, or PPT visuals need QA before they can move from raw to selected or become client-visible. Checks brand safety, product truth, visual consistency, prompt/source traceability, and client visibility.
---

# Ad Visual Review Gate

## Inputs

Read:

```text
AD-creative/visual_assets/asset_manifest.csv
AD-creative/visual_assets/raw/
AD-creative/visual_assets/selected/
AD-creative/visual_assets/rejected/
AD-creative/image_jobs/
AD-creative/visual_review/client_visibility_matrix.csv
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/artifact_index.csv
```

## Gate Checks

Reject or block any asset with:

```text
fake logo
fake packaging text
invented brand mark
fake product technology label
unauthorized celebrity
unreadable text
contact sheet
internal notes inside the image
low-quality collage
untraced source
off-brief scene
product detail without official asset or approval
```

## Decisions

Use these states:

```text
raw -> selected
raw -> rejected
raw -> revise
selected -> client_visible_pending
client_visible_pending -> client_visible
```

Rules:

```text
Raw assets never enter client review.
Selected assets are still internal unless client visibility is approved.
Client-visible assets must have asset_manifest row, prompt/source trace, and Gate PASS.
Product-detail frames require official product asset or explicit placeholder approval.
```

## Outputs

Update or create:

```text
AD-creative/visual_review/review_matrix.csv
AD-creative/visual_review/client_visibility_matrix.csv
AD-creative/gates/<gate_id>_report.md
AD-creative/orchestrator/gate_log.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

## Stop Points

Stop and ask the user before:

```text
showing AI-generated imagery to client
using placeholder product images in a client deck
using real brand logo without logo rules
promoting a risky visual to selected
deleting rejected evidence
```
