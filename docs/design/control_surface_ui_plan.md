# 广告创意控制面 UI 规划

状态：规划草案 / 非实现 / 用于 image_gen 生成 UI 预览

## 1. 参考对象

### Linear

可借鉴：

```text
Issue list / board
状态列
优先级
assignee
labels
project / cycle
display properties
filters
time in status
links / comments
```

不能照搬：

```text
Linear 面向软件 issue，不理解广告创意里的 reference、asset、slot、client visibility、Gate。
```

### Multica

可借鉴：

```text
人和 agent 在同一个 workspace
issue 可以直接 assign 给 agent
agent 执行后在 comments 里报告进度
local daemon 驱动本机 Codex / Claude Code / OpenClaw 等工具
```

不能照搬：

```text
Multica 仍偏通用任务协作，不直接管理广告创意资产链。
```

### Paperclip

可借鉴：

```text
agent control plane
org chart / roles
budgets / cost
governance / approvals
heartbeats
activity trail
persistent task context
audit log
```

不能照搬：

```text
Paperclip 面向 agent company，不是广告创意项目制交付。
预算、公司组织、长期自治不是 v1 核心。
```

### Symphony

可借鉴：

```text
issue-driven agent orchestration
isolated workspace / run
status sync
review packet
proof of work
policy file
stalled / retry / blocked
```

不能照搬：

```text
Symphony 面向代码任务和 PR，不面向客户稿、参考图、视频时间码、PPT、image slot、素材授权。
```

## 2. 我们自己的控制面定位

不是 Linear clone。

不是 Paperclip company dashboard。

不是 n8n 节点流。

它应该是：

```text
广告创意项目的本地 Agent Control Surface
```

核心对象：

```text
Project Timeline
Work Board
Decision Queue
Reference Pack
Visual Asset Board
SlideSpec / Slot Board
Gate Log
Agent Runs
Review Packet
```

## 3. UI 信息架构

### 左侧导航

```text
Project
Timeline
Work Board
References
Visual Assets
SlideSpec
Gates
Delivery
Skills
```

### 顶部项目状态栏

```text
Project: Moncler Visual Direction
Stage: Reference Research + Proposal Architecture
Gate: PARTIAL_PASS
Client Visibility: Internal Preview
Next Decision: Approve Official Search
```

### 中央主区

默认显示 Work Board。

列：

```text
Ready
Running
Blocked
Review
Done
```

卡片字段：

```text
work_id
title
agent
stage
priority
linked requirement
blocked by
next action
gate status
client visibility
```

### 右侧检查器

选中任务后显示：

```text
Work item details
Linked requirements
Source / references
Asset slots
Agent run history
Gate result
Review packet
Next action
```

### 底部决策抽屉

只放需要用户处理的事项：

```text
Waiting for you
Waiting for client
Waiting for director
```

每条必须有：

```text
问题
推荐
影响
不处理后果
可复制问法
```

## 4. 广告创意专属字段

每个 work item 不只记录任务，还要绑定：

```text
linked_requirement
linked_reference
linked_asset
linked_slot
linked_slide
client_visibility
qa_status
source_trace
```

这就是它和 Linear 的区别。

## 5. v1 UI 预览范围

本次 image_gen 只生成一张桌面端 UI 概念图。

画面必须表达：

```text
左侧导航
中间 Work Board
右侧任务详情
底部待确认
Moncler 项目状态
agent / gate / reference / asset slot 关系
```

不表达：

```text
完整 UI 交互
移动端
真实数据
真实 logo
真实品牌图
最终设计系统
```

## 6. UI 预览生成 Prompt

```text
Use case: ui-mockup
Asset type: desktop app product UI concept
Primary request: Create a polished desktop interface mockup for an advertising creative agent control surface. The product is a local orchestration dashboard for a Moncler-style visual proposal project.
Scene/backdrop: Full-screen desktop application, 16:9 canvas, no device frame.
Subject: A professional creative operations dashboard with four zones:
1. Left navigation with readable labels: Project, Timeline, Work Board, References, Visual Assets, SlideSpec, Gates, Delivery, Skills.
2. Top status bar: Project: Moncler Visual Direction, Stage: Reference Research + Proposal Architecture, Gate: PARTIAL_PASS, Visibility: Internal Preview.
3. Central kanban board with columns: Ready, Running, Blocked, Review, Done. Cards include readable short labels such as W-002 Official Search, W-003 Proposal Structure, W-004 Image Job Spec, W-005 SlideSpec Draft.
4. Right inspector panel for selected task: linked requirement, references, asset slots, agent run, gate result, next action.
5. Bottom decision drawer: Waiting for you: Approve Moncler official search.
Style/medium: high-fidelity SaaS product UI mockup, restrained editorial design, practical, dense but clean, no marketing hero.
Composition/framing: wide 16:9 desktop screenshot, crisp grid, no overlapping text, stable panels.
Lighting/mood: neutral professional workspace UI, calm, precise.
Color palette: off-white canvas, charcoal text, muted steel blue accents, amber for blocked, green for pass, red only for risk.
Materials/textures: flat UI, subtle hairline dividers, small status pills, clean typography.
Text: Use only the labels specified above. Text must be readable, not placeholder gibberish.
Constraints: no real Moncler logo, no fake brand marks, no decorative blobs, no sci-fi dashboard, no node graph, no cartoon agents, no stock photos, no unreadable microtext, no internal code screenshots.
Avoid: purple gradients, dark neon UI, rounded card overload, fake charts, cluttered analytics dashboard, landing page hero.
```

## 7. Linear 实际 UI 研究后的修正

上一版问题：

```text
像低质企业后台
左侧导航太重
顶部状态栏太像表单
大卡片看板密度低
右侧详情像上传表单堆叠
底部审批条太大
整体没有 Linear 的轻、快、密、可扫描
```

Linear 实际 UI 特征：

```text
主视图常用 list / board 双模式切换
顶部是 breadcrumb / view title / filter / display options
信息主要靠行、chip、icon、assignee、status group 扫描
右侧 inspector 是上下文抽屉，不是固定表单墙
状态色克制，用小图标、小圆点、小 chip，不用粗色块
列表行密度高，行高约 44-56px
卡片在 board 中也相对克制，少文案，少按钮
左侧导航更像 workspace tree，不是大号 app menu
决策与通知融入 issue/comment/activity，不做巨型横幅
```

修正后的默认第一屏：

```text
Project View: Moncler Visual Direction
主区：Grouped Issue List
分组：Waiting for You / Running / Blocked / Review / Done
右侧：Selected Work Inspector
顶部：breadcrumb + view tabs + filters + display
底部：不放大横幅，只放 40-48px slim decision rail
```

看板用途：

```text
Board 是第二视图
适合阶段排期和创意方向拖拽
不作为默认控制面
```

广告创意专属增强：

```text
Linear issue row + creative artifact binding
每行右侧显示 reference_count / asset_slot / gate / visibility / owner
Inspector 展示 Requirement、Evidence、Assets、SlideSpec、Gate、Run Log
```

## 8. UI v2 Prompt

```text
Use case: product-ui-mockup
Asset type: desktop app UI concept
Primary request: Create a high-fidelity desktop interface mockup for an advertising creative agent control surface inspired by the actual Linear app UI patterns, not a generic SaaS dashboard.

Canvas: full-screen 16:9 desktop app screenshot, no device frame.

Overall style:
Dark graphite Linear-like product UI, dense, quiet, fast to scan, precise typography, thin dividers, subtle borders, restrained accent colors. No marketing visuals. No oversized cards. No large approval banner. No fake analytics charts.

Layout:
1. Compact left workspace sidebar, 220px max, dark surface. It shows a workspace name "AD Creative", then small grouped nav items: Inbox, Projects, References, Assets, Gates, Delivery, Skills. Use small icons and compact labels.
2. Top bar, 48px high. It shows breadcrumb: Projects / Moncler Visual Direction. Then tabs: List, Board, Timeline, Assets. Right side has small controls: Filter, Display, Search, New.
3. Main content is a grouped issue list, not a kanban board. Groups are:
   Waiting for You 2
   Running 3
   Blocked 1
   In Review 2
   Done 4
4. Each row is compact, 48-56px high, with fields:
   W-002 Official brand search
   W-003 Proposal structure
   W-004 Image direction lock
   W-005 SlideSpec draft
   W-006 Reference board
   Include tiny status icons, priority dot, agent initials, gate chip, visibility chip, reference count, asset slot count.
5. Right inspector drawer, 360-420px wide, open for W-002 Official brand search. It has a title, small status chip "Running", tabs: Overview, Evidence, Assets, Gate, Run. Show compact property rows:
   Requirement: R-002 Brand research
   References: 12
   Asset slots: 3
   Gate: Partial pass
   Visibility: Internal
   Owner: Research Agent
   Next: Review source shortlist
6. Bottom slim decision rail, only 44px high. It says: Waiting for you · approve official source scope. Buttons are small: Approve, Changes.

Text:
All visible text must be real and readable. Use only the labels above. No placeholder gibberish.

Visual constraints:
Use compact row density, subtle hover highlight, thin section separators, small chips, small monochrome icons. Accent colors: muted blue for selected, amber for blocked, green for passed, red only for risk. Cards should be minimal and only appear inside inspector, not as the whole layout.

Avoid:
Generic enterprise dashboard, Microsoft Teams style, huge kanban cards, large blue buttons, giant bottom approval panel, decorative gradients, fake charts, fake logos, cartoon agents, node graphs, glossy sci-fi UI, white empty board, crowded upload boxes.
```
