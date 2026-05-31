# Search Quality Gate

status: PARTIAL_PASS
visibility: internal_only
checked_at: 2026-05-22T19:26:03+08:00

## Evidence

- search_plans=1
- references=2
- plan=AD-creative/references/official_search_plan.md
- search_targets=1

## Blocking Issues

- 无

## Warnings

- AD-creative/references/official_search_plan.md 仍需用户批准或缩小范围。
- REF-MON-002 仍是搜索目标，尚无真实 URL。

## Rules

- 搜索计划必须说明 why / scope / platform / expected output / do_not_copy。
- `NEEDS_USER_INPUT` 或 `TBD` 只能内部推进，不能当成客户可见参考。
- role=search_target 的参考不能标记客户可见。
- 客户可见参考必须是真实 https URL 且来源归属可信。
