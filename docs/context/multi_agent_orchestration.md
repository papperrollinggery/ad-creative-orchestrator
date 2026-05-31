# 多智能体编排上下文

目标：把广告创意流程做成 Codex 可运行的主控 + 专项 agent 编排系统。

## 基本结构

不把所有工作塞进一个会话。使用：

```text
1 个主控会话
+ 多个专项会话 / subagent
+ 同一个项目文件夹
+ 文件交接
+ Gate 验收
```

主控职责：

- 建项目目录
- 写 `current_truth.md`
- 拆任务
- 派发 agent 指令
- 收 `handoff.md`
- 合并结果
- 跑 Gate
- 决定下一阶段

专项 agent：

- Research：品牌 / 产品 / 参考视频
- Strategy：创意方向 / 传播策略
- Story：故事线 / 旁白 / 分镜
- Visual：prompt / moodboard / 生图资产
- HTML：客户可审样稿
- QA：审核，不覆盖主文件
- PPT：HTML 确认后转可编辑 PPT
- Delivery：最终打包

## 项目级文件

```text
00_orchestrator/
  current_truth.md
  task_board.csv
  agent_routes.yaml
  gates.yaml
  skill_opportunities.csv

01_research/
02_strategy/
03_story/
04_visual/
05_assets/
06_sample_html/
07_qc/
08_ppt/
09_feedback/
10_delivery/

agents/
  research.md
  strategy.md
  story.md
  visual.md
  html.md
  qa.md
  ppt.md
  skill_miner.md
```

## 运行方式

Codex 原生优先：

- `AGENTS.md` 固化项目规则
- `agents/*.md` 固化专项 agent 提示词
- `task_board.csv` 做任务板
- `gates.yaml` 做阶段门禁
- `handoff.md` 做每个 agent 的交付凭证

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
- 每个 agent 只写自己的目录
- QA agent 只审核，不直接改生产文件
- 客户可见稿不能出现内部注释、AI 标记、contact sheet
- HTML 先审，确认后再转可编辑 PPT
- PPT 不能用整页截图糊弄，文字、logo、表格、平台 UI 要可编辑

