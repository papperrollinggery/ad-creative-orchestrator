# Manual Review Checklist

status: ready_for_human_review
visibility: internal_only
created_at: 2026-05-22T19:26:04+08:00

## Search Sampling

- [ ] 随机打开 3 条客户可见候选参考，确认链接可访问。
- [ ] 确认每条客户可见参考不是 UGC 冒充官方来源。
- [ ] 确认 `do_not_copy` 限制已进入客户稿备注。

## Visual Taste

- [ ] 打开 `AD-creative/handoff/操作台.html` 的图片区，确认没有低质拼贴、contact sheet、假 logo。
- [ ] 对 selected 图片做审美判断：构图、光线、产品真实感、品牌气质、文字/标志风险。
- [ ] 客户可见生成图必须有 `client_visibility_approved` 记录。

## Client Pack

- [ ] 打开 `AD-creative/ppt/client_review_draft.pptx`，确认页面文本可编辑。
- [ ] 逐页读客户稿，确认没有内部注释、模拟标记、TODO/TBD、假案例。
- [ ] 最终发送前由负责人确认发送对象、附件、版本号。

## Rule

本清单是人工审阅入口，不替代 `client-pack-gate`、`visual-quality-gate`、`search-quality-gate`。
