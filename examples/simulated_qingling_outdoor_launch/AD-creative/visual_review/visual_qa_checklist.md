# Visual QA Checklist

artifact_id: ART-QLO-018
status: done
visibility: internal_only

## Required Checks

| Check | Pass Rule | Reject Rule |
|---|---|---|
| Brief match | Matches OP1/OP2 direction and key-frame slot. | Looks like unrelated fashion / outdoor stock image. |
| Reference match | Uses approved internal reference logic without copying. | Directly copies composition or recognizable frame. |
| Product truth | Uses official asset or approved placeholder. | Invents logo, technology label, waterproof claim, or wrong product. |
| Character consistency | Generic and consistent; no celebrity likeness. | Looks like unauthorized celebrity or changes person identity across frames. |
| Environment consistency | Matches city commute / office / greenway / light camp. | High mountain, climbing, skiing, tactical expedition. |
| Text safety | No text unless explicitly required. | Unreadable text, fake label, internal note, watermark. |
| Output quality | Clean photographic image, coherent lighting, no collage artifacts. | Contact sheet, low-quality collage, broken hands/garments, warped product. |
| Client visibility | Visibility tag is explicit. | Any raw/internal image placed in client review. |

## Promotion Rules

```text
raw -> selected:
All required checks pass; source prompt exists; asset manifest updated.

raw -> rejected:
Any legal, brand, product-truth, or visible internal-note failure.

selected -> client_visible_pending:
User approves AI image visibility and asset has no unresolved brand/product risk.

client_visible_pending -> client_visible:
Visual Review Gate PASS and Delivery Gate PASS.
```

## Automatic Reject List

```text
fake logo
fake packaging text
invented brand mark
fake technology label
unauthorized celebrity
unreadable text
contact sheet
internal notes in image
hard mountain expedition
skiing / climbing
low-quality collage
```
