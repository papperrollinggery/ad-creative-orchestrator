# 多智能体编排上下文

目标：把广告创意流程做成 Codex 可运行的主控线程 + 受控 worker/reviewer lane 编排系统。

## 基本结构

不把所有工作塞进一个会话。使用：

```text
1 个主控线程
+ 最多 3 个 active worker/reviewer
+ thread_lane_plan.md 控制面
+ thread_registry.csv 生命周期记录
+ 文件交接和 Gate 验收
```

主控职责：

- 建项目目录
- 写 `current_truth.md`
- 拆任务
- 生成 `thread_lane_plan.md`
- 生成 Agency staff selection 和 role brief
- 派发 worker/reviewer 指令
- 收 receipt / handoff
- 合并结果
- 跑 Gate
- 清理/归档已消费 worker
- 决定下一阶段

默认 lane：

- Research：品牌 / 产品 / 参考视频
- Strategy：创意方向 / 传播策略
- Story：故事线 / 旁白 / 分镜
- Visual：prompt / moodboard / 生图资产
- HTML：客户可审样稿
- QA：审核，不覆盖主文件，只回 receipt
- PPT Draft：只在 `AD-creative/workspaces/<work_id>/` 做草稿
- Delivery Review：只审核交付包，不导出最终文件

主控线程是唯一 integration / export / final status owner。worker 默认只读，除非 `thread_lane_plan.md` 明确写入范围。

## 项目级文件

```text
AD-creative/orchestrator/
  current_truth.md
  work_items.csv
  agent_runs.csv
  artifact_index.csv
  gate_log.csv
  version_map.csv
  thread_lane_plan.md
  thread_registry.csv
  agency_staff_selection_*.md

AD-creative/agents/role_briefs/
AD-creative/workspaces/<work_id>/
AD-creative/references/
AD-creative/creative/
AD-creative/client_review/
AD-creative/image_jobs/
AD-creative/visual_assets/
AD-creative/visual_review/
AD-creative/ppt/
AD-creative/feedback/
AD-creative/delivery/
AD-creative/handoff/

AD-creative/gates/
```

## 运行方式

Codex 原生优先：

- `AGENTS.md` 固化项目规则
- `thread_lane_plan.md` 做 lane 控制面
- `thread_registry.csv` 做线程生命周期表
- `agency_staff_selection_*.md` 记录 staff 选择/拒绝原因
- `agents/role_briefs/*.md` 固化项目专属 role brief
- `work_items.csv` 做任务板
- `gate_log.csv` 做阶段门禁记录
- handoff / receipt 做每个 worker 的交付凭证
- Codex Goal 只归主控会话所有；专项线程只拿 scoped work item
- Codex thread 适合承载 explorer / worker / reviewer lane，但不能替代项目文件里的 truth、gate 和 evidence

外部编排只预留接口：

- Paperclip / Hermes / LangGraph 暂不直连
- V1 只写 `aco/adapters/runner_protocol.md`
- 后续再把 `claim_task / run_agent / return_evidence / verify_gate` 接到外部 runtime

## Gate 顺序

```text
Brief Gate
-> Research Gate
-> Strategy Gate
-> Story Gate
-> Visual Gate
-> HTML Gate
-> PPT Gate
-> Final Gate
```

每个 Gate 输出：

- `PASS`
- `BLOCKED`
- `REGEN`
- `NEEDS_USER_INPUT`

## 核心原则

- `current_truth.md` 优先于聊天记忆
- 未过 Gate 不进入下一阶段
- 每个 worker 只写 `thread_lane_plan.md` 授权的 receipt/workspace
- 非 git PPT/素材项目使用 `AD-creative/workspaces/<work_id>/`，不假装有 git worktree
- QA worker 只审核，不直接改生产文件
- 最终 PPT/PDF 只允许主控线程导出
- 客户可见稿不能出现内部注释、AI 标记、prompt、线程安排、contact sheet
- HTML 先审，确认后再转可编辑 PPT
- PPT 不能用整页截图糊弄，文字、logo、表格、平台 UI 要可编辑
