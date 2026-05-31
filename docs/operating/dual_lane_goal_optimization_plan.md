# 双泳道 Goal 优化执行方案

状态：已执行第一轮优化

依据来源：
- `README.md`
- `docs/operating/dual_lane_goal_delivery_workflow.md`
- `docs/operating/operating_manual.md`
- `docs/operating/first_real_project_runbook.md`
- `docs/operating/authorization_policy.md`
- `docs/operating/real_project_acceptance_criteria.md`
- `templates/project/AD-creative/orchestrator/WORKFLOW.md`

## 1. 优化目标

把“双泳道 Goal 交付工作流”从方案文档提升为可执行项目机制：

| 优化项 | 目标 | 验收证据 |
|---|---|---|
| 入口可见 | README、runbook、WORKFLOW 能直接找到双泳道与 goal 执行法 | 入口文档存在链接和使用口径 |
| 执行可控 | 每轮 goal 有计划、批次、门禁、执行记录、下一轮队列 | 新增 goal iteration template |
| 门禁强制 | 关键阶段 Gate 前必须有反驳性议会记录 | 授权策略与 WORKFLOW 写入规则 |
| 模式切换 | 一刀流/模块化可暂停、恢复、回退 | 执行方案绑定切换规则 |
| 可验证 | 每轮执行后能跑结构检查和示例项目验证 | 验证命令输出 PASS |

## 2. 执行批次

| 批次 | 范围 | 执行动作 | 状态 | 退出条件 |
|---|---|---|---|---|
| B1 文档入口优化 | README、runbook、WORKFLOW、授权策略 | 增加双泳道 goal 工作流入口、使用时机、硬规则 | DONE | 用户/执行者不看对话也能找到入口 |
| B2 执行模板优化 | project template | 新增 goal iteration plan template | DONE | 新项目能复制模板记录一轮 goal |
| B3 门禁机制优化 | Gate policy | 将反驳性议会写成关键阶段前置项 | DONE | 没有议会记录时 Gate 不得高于 PARTIAL_PASS |
| B4 验证闭环优化 | docs + validation | 运行字段/入口/示例项目验证 | DONE | 两个示例项目 validation PASS |
| B5 后续产品化 | operator/tooling | 将模板生成和 Gate 检查接入命令行 | QUEUED | 需要后续代码变更，当前任务不改代码 |

## 3. 执行路线

默认一刀流：

```text
读取双泳道工作流
→ 为本轮 goal 复制 goal_iteration_plan_template.md
→ 填写目标、范围、批次、门禁
→ 执行 B1-B4
→ 运行验证
→ 写执行记录和下一轮队列
```

模块化：

```text
只做文档入口：B1
只做执行模板：B2
只做风险门禁：B3
只做验证闭环：B4
```

切换规则：

| 条件 | 处理 |
|---|---|
| 用户只要流程设计 | 停在 `dual_lane_goal_delivery_workflow.md` |
| 用户要求执行方案并执行 | 执行 B1-B4 |
| 需要改 operator 代码 | 暂停，列入 B5，不在本文档任务内直接改代码 |
| 示例项目验证失败 | 回退到对应模板/文档入口修复后重跑 |
| 发现客户可见/权限/上传/安装动作 | 停止，写入 `待你确认.md` 或最终报告 |

## 4. 已执行内容

| 文件 | 动作 | 目的 |
|---|---|---|
| `docs/operating/dual_lane_goal_optimization_plan.md` | 新增 | 固化本轮优化规划、执行方案、执行记录 |
| `templates/project/AD-creative/orchestrator/goal_iteration_plan_template.md` | 新增 | 支持下一轮 goal 复制使用 |
| `README.md` | 更新 | 增加双泳道/goal 执行入口 |
| `docs/operating/first_real_project_runbook.md` | 更新 | 增加 goal 模式 prompt 和执行路径 |
| `docs/operating/authorization_policy.md` | 更新 | 增加反驳性议会前置门禁 |
| `templates/project/AD-creative/orchestrator/WORKFLOW.md` | 更新 | 将双泳道、goal iteration、反驳门禁写入模板项目 |

## 5. 反驳性议会演练

| 项目 | 内容 |
|---|---|
| 阶段 | 本轮优化 B1-B4 |
| 反对意见 | 只新增文档可能仍无法被真实项目执行者发现，入口不够强 |
| 反驳路径 | 检查 README、first_real_project_runbook、WORKFLOW 是否都指向双泳道和 goal iteration 模板 |
| 修订决议 | 将入口写入 README、真实项目 runbook、模板 WORKFLOW；将议会规则写入授权策略 |
| 门禁结论 | PASS；B5 命令行自动化作为后续队列，不阻塞本轮文档化执行 |

## 6. 验收方案

| 验收项 | 命令/方式 | 通过阈值 |
|---|---|---|
| 新增文档存在 | `test -f ...` | 文件存在 |
| README/runbook/WORKFLOW 入口 | `rg "双泳道|goal iteration|反驳性议会"` | 关键入口均可检索 |
| 示例项目结构 | `python3 tools/validate_project.py examples/moncler_protocol_dry_run` | `VALIDATION=PASS` |
| 示例项目结构 | `python3 tools/validate_project.py examples/simulated_qingling_outdoor_launch` | `VALIDATION=PASS` |
| 非 git 环境确认 | `git status --short` | 返回非 git 仓库 |

## 7. 下一轮队列

| 优先级 | 任务 | 类型 | 退出条件 |
|---|---|---|---|
| DONE | 在 `ad_creative_operator.py` 增加 `goal-plan` 命令，自动生成 goal 执行记录 | 代码 | 新项目能一键生成 goal iteration plan |
| DONE | 在 Gate 命令中检测 adversarial council 记录 | 代码 | 缺记录时 Gate 最高为 PARTIAL_PASS |
| DONE | 为两个示例项目补一份真实填好的 goal iteration plan | 示例 | 示例可直接作为学习样本 |
| DONE | 在操作台展示当前 goal 批次、门禁、下一步 | UI/HTML | 非开发者能看到 goal 状态 |
| DONE | 为 `goal-plan` 与 Gate 降级逻辑补脚本级回归测试 | 测试 | `python3 tools/test_goal_workflow.py` PASS |
| DONE | 将 `tools/test_goal_workflow.py` 纳入统一验证命令清单 | 文档 | 操作手册列出该测试 |
| DONE | 把 goal 状态接入真实项目启动 runbook 的验收清单 | 文档 | runbook 验收含 goal iteration plan 和 dashboard Goal tab |
| DONE | 补 README 当前验证状态，记录 goal-plan、Gate 降级、Goal Tab、回归测试 | 文档 | README 当前验证状态可见 |
| P1 | 终态验证：语法、回归测试、模板、两个示例项目、dashboard audit | 验证 | 全部 PASS |

## 8. 本轮结论

本轮执行到 B4。B5 需要代码改动，已排入下一轮；当前用户要求的优化规划、执行方案、文档化执行与验证闭环已完成。
