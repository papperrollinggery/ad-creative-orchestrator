# Goal Iteration Plan

goal_id: GOAL-MON-DUAL-LANE-001
goal_title: Moncler 双泳道连续执行样例
status: active
owner: Main Controller
created_at: 2026-05-31T20:59:56+08:00
updated_at: 2026-05-31T20:59:56+08:00

## Objective

按品牌深度研究与图片功能双泳道推进 Moncler protocol dry run，并在每个 Gate 前保留反驳性议会记录。

## Scope

- 使用双泳道：品牌深度研究 / 图片功能。
- 阶段完成后直接推进下一步低风险内部任务。
- 每个 Gate 前必须有反驳性议会记录。

## Non Scope

- 不自动发送客户稿。
- 不自动上传客户资料到外部平台。
- 不自动将 AI 图标记为客户可见。
- 不自动安装全局 Skill。

## Source Of Truth

- current_truth: `AD-creative/orchestrator/current_truth.md`
- requirements: `AD-creative/orchestrator/requirements.csv`
- gaps: `AD-creative/orchestrator/gaps.csv`
- work_items: `AD-creative/orchestrator/work_items.csv`
- gate_log: `AD-creative/orchestrator/gate_log.csv`
- handoff_board: `AD-creative/handoff/项目看板.md`
- pending_decisions: `AD-creative/handoff/待你确认.md`

## Execution Batches

| batch_id | objective | owner | inputs | outputs | gate | status | exit_condition |
|---|---|---|---|---|---|---|---|
| B1 | 建立本轮 goal 执行记录 | Main Controller | goal objective | goal iteration plan | Adversarial Council | done | plan written |
| B2 | 按双泳道推进下一阶段 | Main Controller | current_truth / work_items | updated artifacts | stage gate | queued | stage gate not BLOCKED |
| B3 | 验证并写入下一轮队列 | Operations Council | gate_log / artifacts | verification evidence | validation | queued | VALIDATION=PASS |

## Dual Lane Mapping

| phase | brand_research_lane | image_function_lane | dependency | exit_condition | next_phase |
|---|---|---|---|---|---|
| P0 | 需求、事实、缺口 | 图片/素材状态 | source_events | Brief Gate 非 BLOCKED | P1 |
| P1 | 搜索计划、stop condition | 图片路线、asset lock 条件 | P0 gaps | Research Plan Gate 非 BLOCKED | P2 |
| P2 | reference pack、visual DNA | asset slots、manifest skeleton | P1 plan | Reference/Slot Gate 非 BLOCKED | P3 |
| P3 | 创意方向、proposal structure | image job spec、prompt pack | P2 evidence | Creative/Image Job Gate 非 BLOCKED | P4 |
| P4 | 内部原型 | internal_only 图片探索 | P3 contract | Visual QA 非 BLOCKED | P5 |
| P5 | 客户审阅包 | visual review、client flags | P4 assets | Client Pack Gate 非 BLOCKED | P6 |
| P6 | final delivery | approved assets / PPT slots | P5 pack | Final Gate 非 BLOCKED，发送前人工确认 | P7 |
| P7 | 反馈合并 | asset/job supersede | feedback | next_version_plan | next goal |

## Adversarial Council

| stage | objection | rebuttal_path | revision_decision | gate_status |
|---|---|---|---|---|
| global | 自动连续执行可能跳过客户可见风险 | 检查授权策略、Gate 日志、待确认文件 | 只自动推进低风险内部动作；客户稿发送、AI 图客户可见、外部上传仍停 | PASS |

## Pause / Continue / Rollback Rules

continue_when: Gate 非 BLOCKED，且无客户可见/付费/上传/覆盖/安装风险。
pause_when: 客户/导演冲突、AI 图客户可见、客户稿发送、外部上传、全局安装、覆盖旧版本。
rollback_path: 回到产生断链的最近阶段，更新 affected artifacts 和 gate report。
resume_when: 阻塞项关闭，Gate report 和 decisions/resolutions 已更新。

## Verification

| check | method | threshold | result | evidence |
|---|---|---|---|---|
| goal plan exists | file check | exists | pending | `AD-creative/orchestrator/goal_iterations/GOAL-MON-DUAL-LANE-001.md` |
| project validation | validate_project.py | VALIDATION=PASS | pending | run after execution |

## Execution Log

| time | action | artifact | result | next |
|---|---|---|---|---|
| 2026-05-31T20:59:56+08:00 | created goal iteration plan | `AD-creative/orchestrator/goal_iterations/GOAL-MON-DUAL-LANE-001.md` | done | run next batch |

## Next Iteration Queue

| priority | task | owner | trigger | exit_condition |
|---|---|---|---|---|
| P1 | 执行下一阶段 work item | Main Controller | current gate non-blocked | next gate report written |
| P1 | 补充阶段反驳性议会 | QA / Review Council | before each Gate | objection chain recorded |
