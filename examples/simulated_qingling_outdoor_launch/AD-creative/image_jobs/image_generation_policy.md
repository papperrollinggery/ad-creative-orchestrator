# Image Generation Policy

artifact_id: ART-QLO-015
status: done
visibility: internal_only

## Route

```text
Default route: built-in image_gen.
Current simulation route: do not generate real images yet; create executable prompt jobs and QA rules.
Project-bound outputs must be moved into AD-creative/visual_assets before artifact references are marked active.
```

## Required Order

```text
1. Lock character design.
2. Lock product design or mark product as placeholder if official assets are missing.
3. Lock environment and lighting design.
4. Lock visual style and camera language.
5. Generate key frames only after the above are approved for internal use.
```

## Current Asset Lock

| Lock | Status | Decision |
|---|---|---|
| Character | ready_internal | Generic city-to-weekend young adult, no celebrity resemblance. |
| Product | placeholder_only | No official product image, no logo, no exact colorway. |
| Environment | ready_internal | City commute, office, greenway, light camping. |
| Style | ready_internal | Natural light, editorial lifestyle, low-saturation outdoor palette. |

## Prompt Conversion Rule

```text
User vague request:
“做一个城市到自然的轻户外感觉”

Converted image job:
Define use_case, asset_type, primary_request, scene, subject, style, composition, lighting, palette, constraints, avoid, output_contract.
```

## Brand Safety

```text
No fake logo.
No fake packaging text.
No invented brand mark.
No fake technology label.
No unauthorized celebrity.
No unreadable text.
No contact sheet.
No internal notes inside images.
```

## Client Visibility

```text
Current AI images: internal_only.
Client-visible use requires explicit user confirmation plus Visual Review Gate PASS.
```

## PPT Policy

```text
First PPT version uses placeholders for unapproved frame images.
PPT main visual design reference may be generated before deck production.
Storyboard key-frame images require character/product/environment locks first.
```
