# Image Generation Policy

status: template
visibility: internal_only

## Route

```text
Default route: built-in image_gen.
Fallback CLI route: only when user explicitly asks for CLI/API/model controls.
Project-bound outputs must be moved into this project before any artifact references them.
```

## Required Order

```text
1. Lock character design.
2. Lock product design or mark product as placeholder if official assets are missing.
3. Lock environment and lighting design.
4. Lock visual style and camera language.
5. Generate key frames only after the above are approved for internal use.
```

## Prompt Format

```text
User vague language -> normalized JSON prompt pack.
Each image job must define use_case, asset_type, primary_request, input_image_roles, scene, subject, style, composition, lighting, palette, constraints, avoid, output_contract.
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
internal_only: allowed for thinking, mood, rough key frames.
client_visible_pending: requires user approval, rights/source check, and removal of internal notes.
client_visible: requires QA Gate PASS.
```

## PPT Policy

```text
First PPT build uses placeholders for not-yet-approved images.
PPT main visual design can be generated before deck production.
Script key-frame images must not be generated before character/product/environment locks.
```
