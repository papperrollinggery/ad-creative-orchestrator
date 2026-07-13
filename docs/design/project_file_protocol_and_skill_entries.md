# Project File Protocol + Codex Skill 入口

状态：v0 设计锁定草案 / 非实现

> 归档说明（2026-07-13）：本文用于保存 v0 设计决策，其中 `ad-creative:*` 是已退役的概念路由名，不是可执行 CLI。当前操作入口以 `README.md` 与 `docs/operating/` 中的 `adco ...` 命令为准。

## 目标

解决两个问题：

```text
1. Codex 怎么稳定接住一个长期广告创意项目
2. 你怎么不用反复复制提示词
```

核心设计：

```text
少数用户入口
+ 项目文件事实源
+ 内部阶段路由
+ 明确 handoff / gate / version
```

## 总体原则

```text
Codex 会话负责执行
AD-creative/ 负责给 Agent 读写
中文+英文目录负责给你查资料和成果
UI / CLI 只读这些状态
```

控制面不是事实源。

事实源只有项目文件。

## 目录分层

### 你看的目录

命名原则：

```text
中文在前
英文在后
低密度
不放碎分析文件
只放资料、素材、参考、成果、交付
```

建议结构：

```text
00_项目资料_ProjectMaterials/
  01_客户资料_ClientMaterials/
  02_会议记录_MeetingNotes/
  03_导演组资料_DirectorNotes/
  04_客户反馈_ClientFeedback/

01_参考资料_References/
  01_官方参考_OfficialReferences/
  02_竞品案例_CompetitorCases/
  03_风格参考_StyleMood/
  04_视频参考_VideoReferences/

02_重要素材_KeyAssets/
  01_品牌素材_BrandAssets/
  02_产品素材_ProductAssets/
  03_人物素材_TalentAssets/
  04_授权可用_ApprovedForUse/

03_阶段成果_WorkInProgress/
  01_方向草案_DirectionDrafts/
  02_文案草案_CopyDrafts/
  03_视觉探索_VisualExploration/
  04_方案结构_ProposalArchitecture/

04_客户审阅_ClientReview/

05_最终交付_FinalDelivery/
```

规则：

```text
你主要看这些目录。
这些目录不放 agent 碎片思考。
客户可见内容只能从 04 / 05 出。
```

### Agent 读写目录

固定主目录：

```text
AD-creative/
```

建议结构：

```text
AD-creative/
  orchestrator/
  handoff/
  intake/
  requirements/
  references/
  creative/
  copywriting/
  proposal_architecture/
  visual_assets/
  image_jobs/
  slide_spec/
  gates/
  agents/
  delivery/
  skill_drafts/
```

规则：

```text
Codex 和 subagents 主要读写这里。
你不需要日常翻这里。
给你的汇报必须同步到 AD-creative/handoff/。
```

## 核心事实文件

### Orchestrator

```text
AD-creative/orchestrator/WORKFLOW.md
AD-creative/orchestrator/project.yml
AD-creative/orchestrator/events.jsonl
AD-creative/orchestrator/source_events.csv
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
AD-creative/orchestrator/decisions.csv
AD-creative/orchestrator/resolutions.csv
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/work_dependencies.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/orchestrator/version_map.csv
AD-creative/orchestrator/gate_log.csv
```

### Handoff

```text
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/本轮交付说明.md
AD-creative/handoff/客户追问话术.md
AD-creative/handoff/下一步建议.md
```

这几个是你主要看的 Agent 汇报文件。

## Source Event Contract

每次新增资料、会议、反馈，先变成 source event。

字段：

```text
source_event_id
received_at
source_owner
source_type
declared_semantics
file_paths
raw_summary
trust_level
affects_requirements
affects_artifacts
supersedes_event_ids
notes
```

source_owner：

```text
client
director
user
agency_internal
research
agent_inferred
```

declared_semantics：

```text
initial
supplement
change
feedback
approval
rejection
unknown
```

硬规则：

```text
未声明语义时，Codex 可以推断，但必须写 unknown / inferred。
客户明确变更优先于旧需求。
导演组需求更接近执行，但不能自动覆盖客户需求。
用户判断可以进入 internal truth，但不能伪装成客户事实。
```

## Requirement Contract

字段：

```text
requirement_id
source_event_id
owner
statement
requirement_type
priority
status
confidence
scope
affected_stage
linked_artifacts
supersedes_requirement_id
open_questions
```

status：

```text
missing
inferred
researched
confirmed
conflicted
changed
deprecated
locked
```

requirement_type：

```text
brief
brand
product
talent
creative
copy
visual
reference
timeline
delivery
legal_risk
client_preference
director_execution
```

## Work Item Contract

每个 Agent 任务必须变成 work item。

字段：

```text
work_id
stage
title
objective
owner_agent
status
priority
input_refs
output_artifacts
linked_requirements
linked_source_events
linked_references
linked_assets
linked_slides
blocked_by
gate_required
client_visibility
created_at
updated_at
supersedes_work_id
```

status：

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

client_visibility：

```text
internal_only
client_visible_candidate
client_visible_approved
client_sent
do_not_send
```

硬规则：

```text
没有 work item，不派 agent。
没有 linked_requirements，不进入客户稿。
没有 gate_required，不进入下一阶段。
superseded 的 work item 不能继续被下游引用。
```

## Agent Handoff Packet

每次派发专项 Agent，必须生成 handoff packet。

路径：

```text
AD-creative/agents/runs/<run_id>/handoff.md
```

内容：

```text
run_id
work_id
agent_role
task_objective
input_files
required_outputs
allowed_actions
forbidden_actions
linked_requirements
linked_references
linked_assets
gate_to_pass
client_visibility_rule
handoff_back_format
```

必须写清：

```text
这个 agent 看什么
不看什么
产出到哪里
不能做什么
什么时候停下来
怎么交回主控
```

常见 forbidden_actions：

```text
不能把内部注释写进客户稿
不能编造 logo / 包装 / 案例
不能把无来源参考冒充真实案例
不能覆盖旧版本
不能私自升级为 client_visible
不能删除用户资料
```

## Gate Report Contract

路径：

```text
AD-creative/gates/<gate_id>_report.md
```

字段：

```text
gate_id
stage
checked_artifacts
checked_requirements
review_roles
status
score
blocking_issues
revision_items
questions_for_user
questions_for_client
questions_for_director
search_needed
affected_artifacts
next_state
evidence
owner
due
```

status：

```text
PASS
PARTIAL_PASS
REVISE
NEEDS_USER_INPUT
NEEDS_CLIENT_INPUT
NEEDS_DIRECTOR_INPUT
NEEDS_SEARCH
BLOCKED
```

硬规则：

```text
Gate 不直接改稿。
Gate 只判定、列问题、给下一步。
BLOCKED 必须说明回退到哪个 stage。
PARTIAL_PASS 必须说明哪些内容可以继续，哪些不能客户可见。
```

## Artifact Index Contract

所有重要产物都必须进 artifact_index。

字段：

```text
artifact_id
artifact_type
path
stage
version
status
visibility
source_event_ids
linked_requirements
linked_work_items
linked_references
linked_assets
gate_status
supersedes_artifact_id
created_at
updated_at
```

artifact_type：

```text
intake_report
search_plan
reference_pack
creative_direction
copy_draft
proposal_structure
moodboard
storyline
storyboard
mockup
kv
image_job_spec
generated_image
visual_review_report
slide_spec
html_preview
pptx
delivery_note
skill_draft
```

## 用户入口命令

用户不应该记十几个命令。

第一版只保留 6 个用户入口。

### 1. ad-creative:start

用途：

```text
启动或恢复一个广告创意项目
读取项目文件
生成项目看板
告诉用户当前卡点
```

适合用户说：

```text
开始这个项目
继续这个项目
看下现在到哪了
```

### 2. ad-creative:add-materials

用途：

```text
接收新资料 / 会议记录 / 客户反馈 / 导演组意见
登记 source event
判断是补充、变更、反馈还是冲突
更新 current truth
输出缺口和追问建议
```

适合用户说：

```text
客户又发了这些
这是会议记录
导演组补充了一些意见
这是客户反馈
```

### 3. ad-creative:next

默认主入口。

用途：

```text
读取当前状态
判断下一步
如果不需要用户决策，继续推进
如果需要用户决策，更新 待你确认.md 并停下
```

这是最重要的入口。

用户可以只说：

```text
继续
下一步
推进
```

### 4. ad-creative:status

用途：

```text
输出项目当前状态
显示卡点
显示待确认
显示最近产物
显示下一步建议
```

只读，不推进。

### 5. ad-creative:gate

用途：

```text
对指定阶段或产物运行 Gate
生成 gate report
更新 work item / artifact / handoff
```

典型：

```text
跑视觉审核
检查 PPT
检查客户稿能不能发
```

### 6. ad-creative:mine-skill

用途：

```text
检查当前项目中是否出现可复用通路
生成项目内 skill 草稿
附 evidence
不自动安装
```

## 内部阶段路由

这些不需要用户直接记。

由 `ad-creative:next` 内部调用：

```text
intake
diagnose
research_plan
reference_research
creative_council
copywriting
proposal_architecture
visual_plan
image_job
visual_review
slide_spec
html_preview
ppt_gate
feedback_merge
delivery
skill_mining
```

## 人工确认规则

必须停下来问用户：

```text
brief 边界不清
客户/导演/用户需求冲突
是否联网搜索
搜索范围会影响方向
创意方向数量和取舍
主视觉方向
人物/产品/场景资产锁定
客户可见图是否允许 AI 生成
客户稿发送前
Skill 是否提升到 ~/.codex/skills
```

可以自动推进：

```text
资料归档
source event 登记
需求提取
缺口初判
内部 work item 拆分
内部 handoff packet
内部 Gate 初检
低质图 rejected
项目内 skill 草稿生成
```

## Search Policy

搜索不能随便做。

先输出：

```text
为什么需要搜索
搜索解决哪个缺口
建议搜哪些平台
不搜会影响什么
搜索结果会进入哪个产物
```

平台路由：

```text
国内品牌 / 国内投放：
新片场、B站、小红书、抖音、微博、品牌官网、官方公众号

国外品牌 / 国际参考：
YouTube、Vimeo、Instagram、TikTok、品牌官网、官方 campaign archive、Behance、Pinterest

导演 / 制作风格：
新片场、Vimeo、YouTube、导演官网、制作公司官网

PPT / 视觉系统：
品牌官网、campaign archive、Behance、设计案例库
```

## 最小可运行闭环

第一轮只验证非 UI 流程：

```text
ad-creative:start
→ ad-creative:add-materials
→ intake report
→ requirements / gaps / search plan
→ ad-creative:next
→ work items
→ research handoff
→ reference pack
→ proposal architecture
→ image job spec
→ visual review gate
→ 项目看板.md
→ 待你确认.md
```

验收标准：

```text
不看 UI，也知道项目卡在哪里
不复制长 prompt，也能继续下一步
换一个 Agent，也能读 handoff 接着做
新增客户反馈后，旧版本不会污染新版本
每个视觉资产能追溯到 requirement / reference / slot / Gate
```

## 当前锁定

锁定：

```text
第一版做 Codex Skill + Project File Protocol
不先做 UI
不先上 LangGraph / Agents SDK
不自动安装全局 skill
不把客户资料沉淀进 skill
```

仍待确认：

```text
实际项目目录是否直接采用这套结构
用户入口命令命名是否采用 ad-creative:*
Project File Protocol 是否先用 CSV/MD/JSONL，还是一部分改 YAML/JSON
Moncler 验证是否下一步开始
```
