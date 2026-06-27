# Virtual ThreadOps Trial Review 2026-06-27

## Verdict

结论：第二轮虚拟项目跑通，当前产物适合作为内部方向草稿和 ThreadOps 控制面验证，不适合客户发送。

主线程采纳：

- ADOPT: 修复 proposal 证据抽取，优先使用 source brief，避免把 asset gap 写成创意主张。
- ADOPT: 保留 humanized display phrase，让证据原文留在 Proposal Inputs，创意句子使用更自然的中文短语。
- PARTIAL_ADOPT: ThreadOps 契约产物覆盖 harness + loop + helper 字段，但虚拟项目内 worker lanes 仍是 planned，不代表生产 worker 已完成。
- REJECT: 不把 `VALIDATION=PASS`、`CREATIVE_PROPOSAL=PASS` 或 `CREATIVE_QUALITY_GATE=PARTIAL_PASS` 解释为客户可发送。

## Virtual Project Paths

- First run with defect: `/Users/jinjungao/work/ad-creative-orchestrator/tmp/virtual-threadops-trial-20260627-191929/project`
- Fixed rerun: `/Users/jinjungao/work/ad-creative-orchestrator/tmp/virtual-threadops-trial-20260627-192407-fixed/project`
- Input brief: `/Users/jinjungao/work/ad-creative-orchestrator/tmp/virtual-threadops-trial-20260627-191929/briefs/nova-trail-launch-brief.md`
- Fixed dashboard: `/Users/jinjungao/work/ad-creative-orchestrator/tmp/virtual-threadops-trial-20260627-192407-fixed/project/AD-creative/handoff/操作台.html`
- Fixed creative draft: `/Users/jinjungao/work/ad-creative-orchestrator/tmp/virtual-threadops-trial-20260627-192407-fixed/project/AD-creative/creative/creative_directions.md`
- Fixed ThreadOps lane plan: `/Users/jinjungao/work/ad-creative-orchestrator/tmp/virtual-threadops-trial-20260627-192407-fixed/project/AD-creative/orchestrator/thread_lane_plan.md`

## What The Run Proved

First run exposed a real quality defect. The generated creative proposal used open gaps such as missing logo/font/package as creative direction inputs. That was structurally valid but not satisfying.

Fixed run result:

- `creative_directions.md` now keeps raw source evidence in Proposal Inputs.
- Direction copy now uses concrete display phrases such as `24-36 岁城市职场人`, `3 层防水面料`, and `他们不相信夸大的户外性能话术，只接受具体使用瞬间`.
- Asset and AI visibility gaps remain blockers instead of becoming creative claims.
- The dashboard, support bundle, and validation still render cleanly.

## Gate Status

- `VALIDATION=PASS`
- `DASHBOARD_AUDIT=PASS`
- `SUPPORT_BUNDLE=PASS`
- `CREATIVE_QUALITY_GATE=PARTIAL_PASS`
- `VISUAL_QUALITY_GATE=PARTIAL_PASS`
- `SEARCH_QUALITY_GATE=PARTIAL_PASS`
- `FILM_QUALITY_GATE=BLOCKED`
- `REFERENCE_PACK_GATE=BLOCKED`
- `CLIENT_PACK_GATE=BLOCKED`
- `HANDOFF_READINESS_GATE=BLOCKED`

Reason for not client-ready:

- Missing brand logo, fonts, packaging, and product exposure rules.
- AI image client visibility is not confirmed.
- Reference pack is empty.
- No PPTX/PDF/preview/text extract/version_map/current_truth chain exists.
- Creative gate reports open evidence gaps.

## Code Change

Changed files:

- `/Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py`
- `/Users/jinjungao/work/ad-creative-orchestrator/tools/test_gates.py`

Change summary:

- Added source-material evidence extraction that skips markdown headings.
- Changed proposal evidence matching to prefer stronger pattern matches over first text occurrence.
- Split source/requirement evidence from gap evidence so gaps are fallback risks, not primary creative inputs.
- Added proposal display phrasing for common brief facts so generated direction copy reads more naturally.
- Added regression coverage for source brief priority over asset gaps.

## Test Evidence

Focused regression:

```text
PYTHONDONTWRITEBYTECODE=1 python3.12 tools/test_gates.py
TEST_GATES=PASS
optional skips: PIL, pptx
```

End-to-end fixed virtual project:

```text
run: VALIDATION=PASS
profile-analyze: VALIDATION=PASS
creative-proposal: CREATIVE_PROPOSAL=PASS, VALIDATION=PASS
goal-plan: VALIDATION=PASS
thread-plan: THREAD_PLAN=PASS, VALIDATION=PASS
goal-run: STOP_REASON=WAITING_FOR_CONFIRMATION
support-bundle: PASS
audit-dashboard: PASS
validate: VALIDATION=PASS
status: completion_readiness.status=NOT_READY
```

## Real Codex Thread Receipts

Created and archived real Codex Threads:

| thread_id | thread_class | verdict | cleanup |
|---|---|---|---|
| `019f08d5-dbeb-7ee2-8daf-8fff6b6a39ad` | read_only_cold_review | IMPROVED_INTERNAL_DRAFT_NOT_CLIENT_READY | archived |
| `019f08d6-07ab-7bc0-921c-a0cfc2c6a29e` | read_only_contract_review | PARTIAL_PASS | archived |
| `019f08d6-29eb-7b32-be5a-14ebe251b2e1` | read_only_engineering_review | PASS_WITH_NON_BLOCKING_RISK | archived |

Receipt adoption:

- Creative cold review adopted. It confirmed the fixed draft is usable for internal direction discussion, but not client-ready.
- ThreadOps contract review adopted. It confirmed field coverage for `action_space`, `observation_contract`, `error_recovery_contract`, `context_budget`, `iteration_budget`, `eval_gate`, `adoption_decision`, `rejection_reason`, `loop_state`, `replay_trigger`, `freeze_trigger`, and helper evidence fields. It also correctly flagged that virtual project worker ids remain `planned:*` and receipts remain pending.
- Engineering review adopted. It found no blocking issues and confirmed `TEST_GATES=PASS`; the remaining risk is that `proposal_display_phrase` is intentionally conservative and may fall back to raw source phrasing for unfamiliar briefs.

## Satisfaction Check

满意的部分：

- The workflow now produces a visible virtual project, dashboard, proposal draft, ThreadOps plan, gates, and support bundle.
- The defect found by the virtual run was fixed and covered by a regression test.
- Real Codex Threads were used for cold review and then archived.

不满意或仍 blocked 的部分：

- The virtual project does not have real client brand assets, references, images, or deck exports.
- The project is still in `WAITING_FOR_CONFIRMATION`.
- The ThreadOps lane plan is contract-complete, but the planned production worker lanes were not executed as real writable worker threads in this trial.

Final status: product workflow improved and verified, but the fictional project is intentionally not client-send complete.
