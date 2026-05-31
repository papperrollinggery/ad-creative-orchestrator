# Codex-first 架构判断

状态：office-hours 方向诊断 / 非实现

## 结论

最佳方向不是纯 Codex，也不是控制面板产品。

最佳方向是：

```text
Codex-native Skill
+ Project File Protocol
+ Optional Control Views
```

一句话：

```text
Codex 负责思考和执行。
项目文件负责记忆和交接。
控制面只负责显示和少量操作。
```

## 为什么纯 Codex 不够

纯 Codex 会话适合短任务，不适合广告创意长项目。

问题：

```text
客户资料会分批到
需求会被补充、修改、推翻
导演组/客户/你自己的需求会并行存在
参考图和视频必须溯源
视觉资产有 raw / selected / rejected / client-visible
PPT、HTML、图像、文案会互相影响
Gate 不能靠聊天记忆
Skill Mining 需要 evidence
```

如果只靠会话：

```text
上下文容易丢
agent 交接不稳定
客户反馈难追踪
旧需求容易污染新版本
视觉审核没有证据链
你会继续反复复制提示词
```

## 为什么控制面板优先也不对

控制面板优先会把项目带偏。

它会变成：

```text
先设计 UI
再设计任务状态
再设计数据结构
最后才想 Codex 怎么跑
```

这对当前目标不划算。

你的真实需求不是“做一个 Linear for Ads”。

你的真实需求是：

```text
我把乱资料交给 Codex
Codex 能稳定理解、拆解、追踪、创作、审核、交付
并且把重复通路沉淀成 Skill
```

控制面可以提高可视化，但不应该成为系统核心。

## 正确分层

### Layer 1：Codex Skill

核心执行层。

职责：

```text
读取项目状态
识别当前阶段
判断缺口
提出是否搜索
拆 work item
调用 subagents
合并 handoff
生成创意/文案/视觉任务
运行 Gate
生成待确认问题
提出 Skill Mining
```

这是产品的脑和手。

### Layer 2：Project File Protocol

事实源。

职责：

```text
保存 timeline
保存 current truth
保存 requirements
保存 work items
保存 agent runs
保存 references
保存 asset manifest
保存 gate log
保存决策和版本
```

这是产品的记忆。

### Layer 3：Human-facing Files

你看的东西。

只保留少数清晰入口：

```text
项目看板.md
待你确认.md
交付索引.md
客户资料/
重要素材/
参考资料/
阶段成果/
最终交付/
```

这些文件要中文+英文命名，少而清楚。

### Layer 4：Optional Control Views

未来视图。

可以是：

```text
Markdown 看板
CLI status
轻 UI
Linear adapter
Paperclip adapter
```

它们都只读取 Project File Protocol。

## 四个可选路线

### A. 纯 Codex Skill

最快。

优点：

```text
上手快
最贴近你现在的使用方式
不用开发 UI / CLI
适合马上跑 Moncler 验证
```

缺点：

```text
长项目状态仍然容易散
多 agent 交接靠提示词
缺少强约束 schema
后续迁移 UI / CLI 较乱
```

适合：

```text
第一轮工作流验证
不适合作为最终形态
```

### B. 控制面板优先

最直观，但风险最大。

优点：

```text
项目状态可视化强
你能一眼看到卡点
未来像产品
```

缺点：

```text
开发成本高
容易变成 dashboard 项目
会推迟真正的 Codex 工作流
视觉审核、创意议会、PPT Gate 仍要另做
```

适合：

```text
后期产品化
不适合现在
```

### C. Codex Skill + File Protocol

当前最佳。

优点：

```text
Codex 原生
可立即验证
每一步可落盘
agent 交接稳定
能支持动态需求变化
后续可接 CLI / UI / Linear / Paperclip
```

缺点：

```text
第一版不够酷
没有强可视化
需要先把文件协议设计清楚
```

适合：

```text
当前阶段
Moncler 验证
后续沉淀 Skill
```

### D. LangGraph / Agents SDK / Symphony-first

更工程化，但现在过重。

优点：

```text
状态机更强
可恢复执行
可接 tracing / guardrails
长期更像系统
```

缺点：

```text
早期会被框架牵着走
广告创意 artifact 模型还没锁定
会把问题变成 agent infra 项目
```

适合：

```text
File Protocol 稳定之后
第二阶段或第三阶段
```

## 推荐方案

选 C。

```text
先做 Codex Skill + File Protocol。
控制面只做投影。
```

原因：

```text
你现在最缺的不是 UI。
你最缺的是一套 Codex 能反复执行的广告创意操作系统。
```

这个操作系统必须先回答：

```text
收到资料后怎么判断缺什么
什么时候搜索
搜索什么平台
怎么给你客户追问话术
怎么拆创意方向
怎么确定 moodboard / storyboard / KV / mockup / BTS
怎么用 image_gen
怎么审核视觉
怎么转 PPT
怎么合并客户反馈
怎么沉淀 Skill
```

这些不需要 UI 才能跑。

## 控制面应该降级

控制面不删，但降级为：

```text
View, not brain
```

v0：

```text
项目看板.md
待你确认.md
```

v1：

```text
aco status
aco gate
aco propose-skill
```

v2：

```text
轻 UI
```

v3：

```text
Linear / Paperclip / Symphony adapter
```

## 下一步真正该锁的东西

不是继续画 UI。

下一步应锁：

```text
Codex Skill 的入口命令
Project File Protocol
Work Item Contract
Agent Handoff Packet
Gate Report Contract
Human-facing folder structure
Moncler 验证流程
```

## Skill 入口建议

未来 Skill 可以是：

```text
ad-creative:start
ad-creative:intake
ad-creative:diagnose
ad-creative:research-plan
ad-creative:dispatch
ad-creative:creative-council
ad-creative:visual-plan
ad-creative:image-job
ad-creative:visual-review
ad-creative:slide-spec
ad-creative:ppt-gate
ad-creative:feedback-merge
ad-creative:delivery
ad-creative:mine-skill
```

## 最小验证

用 Moncler 做一次非 UI 验证：

```text
1. 输入模拟客户资料
2. 生成 Intake Report
3. 生成 requirements / gaps / search_plan
4. 生成 work_items
5. 模拟 Research Agent handoff
6. 生成 Reference Pack
7. 生成 Proposal Architecture
8. 生成 Image Job Spec
9. 运行 Visual Review Gate
10. 输出 项目看板.md 和 待你确认.md
```

验证标准：

```text
不看 UI，也能知道项目卡在哪里
不复制长 prompt，也能继续下一步
换一个 agent，也能读文件接着做
客户需求变化后，旧版本不会污染新版本
每个视觉资产都能追溯到 requirement / reference / slot / Gate
```

## 结论

当前产品定义应该是：

```text
Codex 内的广告创意编排 Skill
```

不是：

```text
广告创意项目管理 UI
```

UI 以后有价值，但现在不是主线。

现在主线：

```text
把你的广告创意方法变成 Codex 能稳定执行、可保存、可复用、可审核、可沉淀 Skill 的工作流。
```
