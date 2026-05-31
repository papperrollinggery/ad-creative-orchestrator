# Visual Quality Gate

status: PASS
visibility: internal_only
checked_at: 2026-05-22T19:26:03+08:00

## Evidence

- assets=1
- min_long_edge=720
- min_short_edge=480

## Blocking Issues

- 无

## Warnings

- 无

## Rules

- active 图片必须存在且可读取。
- selected / approved / done 图片必须 QA PASS。
- 生成图必须有 prompt_or_edit_ref。
- 客户可见生成图必须记录 `client_visibility_approved`。
- 客户可见图片不能是 contact sheet、低质拼贴、placeholder-only、假 logo。
- 默认最低尺寸：长边 720px，短边 480px。
