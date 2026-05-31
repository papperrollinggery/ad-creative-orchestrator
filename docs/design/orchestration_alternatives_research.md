# 开源编排方案调研

日期：2026-05-13

状态：方案调研，不是实现定稿

## 核心结论

当前更好的办法不是选一个框架替代项目设计，而是做：

```text
广告创意本地控制面
+ Symphony-style 工作项状态机
+ CAO-style handoff/assign/send_message 操作语义
+ OpenSWE-style async run / sandbox / mid-run feedback
+ LangGraph-style checkpoint / interrupt 思想
+ OpenAI Agents SDK-style handoff / guardrail / tracing adapter
+ 广告创意专属 artifact / reference / asset / SlideSpec / Gate
```

原因：

```text
现成开源方案主要服务代码开发。
我们的核心对象是广告项目，不是 PR。
必须把 brief、客户反馈、导演反馈、参考图/视频、视觉资产、SlideSpec、PPT Gate 作为一等对象。
```

## 方案对比

| 方案 | 可借鉴 | 不适合直接采用 |
|---|---|---|
| OpenAI Symphony | issue tracker 作为控制面、WORKFLOW.md、reconciliation、per-work-item workspace、review packet | 面向 coding issue / PR，不懂创意资料、视觉资产、客户可见性 |
| AWS CLI Agent Orchestrator | handoff、assign、send_message、跨 provider agent profile、tool restriction | 偏 CLI/terminal agent 管理，不提供广告项目 artifact 模型 |
| LangChain OpenSWE | async agent、Linear/Slack/GitHub 触发、sandbox、mid-run message、subagent、middleware | 面向代码仓和 PR；引入成本高，早期会压过业务建模 |
| Composio Agent Orchestrator | plugin architecture、runtime/agent/session/lifecycle 分层 | 更像通用 agent 平台；不解决创意方案结构 |
| LangGraph | durable execution、checkpoint、interrupt、human-in-loop、resume | 适合后期做可运行 graph；现在直接上会过重 |
| OpenAI Agents SDK | handoff、guardrails、tracing、sessions | 适合作为未来 runtime adapter；不是项目控制面本身 |
| OpenHands | local GUI、agent server、workspace/session UI | 偏软件开发代理 UI，可参考 workspace/session 体验，不宜直接变成创意工具 |
| CrewAI / AutoGen | 多角色 agent 编排概念 | 容易退化成角色聊天，缺少项目状态、证据链、artifact gate |

## 采用策略

当前推荐：

```text
先做 Adapter-ready Local Control Plane
后续再接 Symphony / Linear / LangGraph / Agents SDK / Paperclip
```

不要现在做：

```text
直接复制 Linear
直接复制 Symphony
直接用 CrewAI/AutoGen 做核心
直接把 LangGraph 放在第一版
```

## 控制面最小内核

本地文件仍然是第一控制面：

```text
AD-creative/orchestrator/WORKFLOW.md
AD-creative/orchestrator/events.jsonl
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

原因：

```text
能被 Codex 直接读写
能被人快速查看
能保留时间线和证据
不依赖 SaaS
后面可迁移到 UI / CLI / Linear / Paperclip
```

## Adapter 切分

第一版就按 adapter 思维设计，但不急着实现 adapter：

```text
Tracker Adapter
本地 work_items.csv 先行；未来可接 Linear / Symphony issue tracker

Agent Runtime Adapter
Codex subagents 先行；未来可接 OpenAI Agents SDK / LangGraph / CAO

Workspace Adapter
项目文件夹先行；未来可接 git worktree / sandbox / cloud workspace

Artifact Adapter
Reference Pack / Asset Manifest / SlideSpec / PPT / HTML / image job

Review Adapter
Gate Report / Review Council / QA Packet

Notification Adapter
本地项目看板先行；未来可接 UI / Slack / 飞书 / Linear comment

Skill Mining Adapter
项目内 skill 草稿先行；人工确认后提升到 ~/.codex/skills
```

## 统一操作语义

吸收 CAO 和 Symphony 后，广告创意编排需要这些操作动词：

```text
create_work
assign_work
start_run
handoff_work
send_update
block_work
request_decision
resolve_decision
gate_artifact
retry_work
supersede_work
archive_work
propose_skill
```

这些动词比“Research Agent / Visual Agent / PPT Agent 聊天”更稳定。

## 状态模型

工作项状态：

```text
todo
ready
running
blocked
waiting_user
waiting_client
waiting_director
review
revision
accepted
rejected
superseded
done
```

Agent run 状态：

```text
created
started
working
needs_input
failed
completed
cancelled
reconciled
```

Artifact 状态：

```text
draft
internal_review
approved_internal
client_visible
client_sent
rejected
superseded
final
```

## 人工确认点

必须停下给用户看的节点：

```text
brief 边界不清
客户/导演需求冲突
是否需要联网搜索
关键参考方向
创意方向数量和取舍
主视觉方向
人物/产品/场景资产锁定
客户可见稿前 QA
PPT final handoff
Skill 提升到全局安装
```

不必每次问用户的节点：

```text
资料归档
需求提取
缺口初判
内部研究计划草稿
内部 work item 拆分
内部 Gate 检查
项目内 skill 草稿生成
```

## 对 UI 的影响

控制面不应只是任务列表。

需要三条主线：

```text
Decision Lane
待用户 / 客户 / 导演确认

Production Lane
Ready / Running / Blocked / Review / Done

Evidence Lane
Reference / Asset / SlideSpec / Gate / Source Trace
```

右侧 inspector 必须能看到：

```text
这个任务解决哪个需求
引用哪些资料
依赖哪些参考图/视频
产出哪个 artifact
是否客户可见
当前 Gate 卡在哪里
下一步由谁决定
```

## 近期建议

下一阶段不直接做完整系统。

先锁定一个 Orchestration Prototype v0：

```text
1. 用 Moncler 项目模拟真实输入
2. 生成 work_items.csv
3. 生成 agent_runs.csv
4. 生成 artifact_index.csv
5. 生成 项目看板.md
6. 模拟一次客户反馈变更
7. 检查需求时间线、work item、artifact 是否正确 supersede
```

验证目标：

```text
用户能看懂项目卡在哪里
主控能知道下一个 agent 做什么
agent 能知道输入/输出/Gate
旧需求不会污染新版本
参考、资产、方案、PPT 可以追溯
```

## 外部参考

```text
OpenAI Symphony
https://openai.com/zh-Hans-CN/index/open-source-codex-orchestration-symphony/
https://github.com/openai/symphony

Symphony SPEC
https://github.com/openai/symphony/blob/main/SPEC.md

AWS CLI Agent Orchestrator
https://github.com/awslabs/cli-agent-orchestrator

LangChain OpenSWE
https://github.com/langchain-ai/open-swe

Composio Agent Orchestrator
https://composiohq-agent-orchestrator.mintlify.app/concepts/architecture

LangGraph persistence / human-in-loop
https://docs.langchain.com/oss/python/langgraph/persistence
https://docs.langchain.com/oss/python/langgraph/human-in-the-loop

OpenAI Agents SDK
https://developers.openai.com/api/docs/guides/agents

OpenHands
https://github.com/OpenHands/OpenHands
```
