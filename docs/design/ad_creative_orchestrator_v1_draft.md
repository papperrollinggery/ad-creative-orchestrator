# 广告创意多智能体编排 v1 讨论草案

状态：讨论草案 / 非定稿 / 待真实项目验证

本文件用于保存与用户共同推导出的工作流设计。后续构思阶段每锁定一个阶段，都应同步更新本文件，避免只停留在对话上下文里。

## 1. 核心判断

本项目核心不是“多个 agent 聊天”，而是：

```text
项目状态机
+ 当前需求真相表
+ 参考图/视频证据链
+ 创意/文案/方案架构
+ 视觉资产系统
+ HTML/PPT 同源输出
+ Gate 审核
+ Skill 沉淀
```

多智能体只是执行层。主控 Agent 负责维护项目状态、派发任务、合并 handoff、跑 Gate、更新 current truth。

V1 默认采用：

```text
文件驱动主控 + Codex/subagents 执行 + 项目内结构化状态文件
```

不直接依赖 LangGraph / CrewAI / ORCH，但预留后续 adapter。

## 2. 主流程

```text
Intake Gate
→ Reference Research
→ Creative Council
→ Creative Direction
→ Copywriting
→ Proposal Architecture
→ Visual Asset OS
→ SlideSpec / HTML
→ PPT Bridge
→ Review Council / QA
→ Delivery
→ Retro / Skill Mining
```

流程必须动态调整。不同项目不固定产出 moodboard、storyboard、mockup、BTS、KV，而是根据客户当前要做的决策配置模块。

## 3. Intake Gate v1

目标：客户乱资料进入后，先判断现状、缺口、问题和下一步，不直接开始创意生产。

输入：

```text
客户 brief / 会议记录 / 音频 / 视频 / PPT / PDF / 图片 / 链接 / 后续补充 / 客户反馈 / 导演组需求
```

默认推进方式：

```text
诊断缺口 + 给行动路径 + 标记可推进范围
```

输出：

```text
一页行动简报
current_truth
requirements
gaps
resolutions
search_plan
```

一页行动简报顺序：

```text
1. 必须问谁什么
2. 当前能先做什么
3. 缺口影响等级
4. 是否建议搜索
5. 当前有效需求
6. 冲突/失效信息
7. Gate 状态
8. 下一阶段建议
```

资料批次规则：

```text
用户声明优先：首次资料 / 补充 / 变更 / 反馈
未声明时系统推断并标待确认
```

需求状态：

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

缺口影响等级：

```text
blocking
high_impact
medium
low
obsolete
```

Gate 状态：

```text
PASS
PARTIAL_PASS
NEEDS_CLIENT_INPUT
NEEDS_STAKEHOLDER_INPUT
NEEDS_SEARCH
BLOCKED
```

允许内部假设，但必须标明假设、风险、待确认点，不能进入客户稿。

## 4. Timeline / Requirement / Resolution

整个项目必须有时间线，而不是只记录最终 brief。

Timeline 记录：

```text
客户给资料
客户补充
客户反馈
导演/制片/艺人/平台需求
用户判断
系统输出版本
Gate 结果
交付给下一次会议的版本
```

Requirement Node 记录：

```text
谁提出
要求什么
绑定哪个交付物
状态是什么
证据来自哪里
是否覆盖旧信息
```

Resolution Track 记录：

```text
问题是什么
影响什么
当前建议怎么解决
为什么现在这么做
谁确认
确认后改哪些产物
状态
```

核心原则：客户/导演常常只提出问题，系统要形成解决路径。

## 5. Search Plan Contract v1

搜索不是泛泛找资料，而是解决明确缺口或启发创意。

搜索前先出计划，不默认搜索。

字段：

```text
search_id
trigger_stage
search_goal
linked_gap
linked_requirement
linked_decision
platforms
keywords
expected_outputs
client_visibility
stop_condition
```

搜索类型：

```text
补缺型：品牌最新campaign、产品信息、平台规格
启发型：创意、视觉、拍法、节奏、参考视频
验证型：检查方向是否撞车、是否太常见、是否和品牌调性冲突
```

平台分流：

```text
国内品牌/国内传播：品牌官网、天猫/京东官方店、小红书、抖音、B站、新片场
TVC/广告片：新片场、B站、YouTube、Vimeo、导演官网
海外品牌/奢侈品：品牌官网、Instagram、YouTube、Vimeo、campaign archive、Vogue、Hypebeast
KV/视觉提案：品牌官网、官方社媒、Behance、Pinterest、campaign archive
社媒种草：小红书、抖音、TikTok、Instagram
```

硬规则：

```text
没有 linked_gap 或 linked_requirement，不搜索
搜索结果必须能进入 Reference Card
不能把搜索结果直接当最终创意
```

## 6. Reference Pack v1

参考图/视频是客户很看重的证据链，不是素材堆。

作用：

```text
启发创意
支撑视觉方向
帮助客户快速理解方案
```

搜索分类：

```text
Brand Official Reference
Category Reference
Platform Reference
Director / Cinematography Reference
Visual Style Reference
Product Moment Reference
Talent / Performance Reference
```

Reference Card 字段：

```text
reference_id
type
source_platform
source_url
source_owner
capture_date
linked_requirement
linked_direction
linked_module
linked_slot_or_slide
client_decision_supported
why_it_matters
what_to_borrow
what_not_to_copy
client_visibility
rights_note
quality_score
status
```

视频额外字段：

```text
timecode_start
timecode_end
motion_reference
editing_reference
performance_reference
sound_reference
```

图片额外字段：

```text
composition_reference
lighting_reference
color_reference
material_reference
layout_reference
```

客户稿呈现方式：

```text
参考图 / 视频帧
标题：我们借鉴什么
一句解释：这条参考帮助客户理解什么
绑定：OP1 / OP2 / 某个镜头 / 某个页面
可借鉴：光线 / 构图 / 节奏 / 产品露出
不复制：人物 / 品牌元素 / 具体画面
来源：平台 + 链接
```

硬规则：

```text
无来源不进 Reference Pack
视频无时间码不进客户稿
没有 why_it_matters 不进客户稿
client_visibility 未确认只能 pending/internal
竞品/他牌参考必须写 what_not_to_copy
```

## 7. Creative Council v1

目标：做方案前进行结构化反思，避免直接套模板出 OP。

输入：

```text
Current Truth
Requirement Nodes
Resolution Tracks
Reference Cards
客户/导演/用户的关键问题
项目阶段
交付目标
禁区
```

议会角色：

```text
Strategy Voice：品牌、客户需求、商业目标是否成立
Creative Voice：创意是否有记忆点、是否能形成独特表达
Execution Voice：能不能拍、能不能做、成本和时间是否现实
Client Voice：客户是否理解、是否买单、会质疑什么
Critic Voice：挑俗套、空泛、AI感、逻辑漏洞
```

输出：

```text
项目真实问题
创意判断标准
可行方向池
推荐方向
备选方向
不建议方向
需要补充参考/搜索
需要客户或导演确认的问题
给文案阶段的输入
```

方向池格式：

```text
方向名
一句话命题
客户价值
画面机制
产品/品牌/人物进入方式
参考支撑
优点
风险
是否适合当前阶段
```

## 8. Copywriting v1

目标：把创意方向转成客户能读懂、愿意继续看的表达。

文案不是最后润色，是方案结构的一部分。

输出：

```text
方案总标题
核心命题
方向命名
方向一句话
方向阐述
客户价值说明
片子 logline
故事线文案
旁白 / 字幕初稿
PPT 页面标题
参考图说明文案
推荐理由
修改说明
```

文案分层：

```text
L1 内部判断文案
L2 方案草案文案
L3 客户可读文案
L4 精修提案文案
L5 执行文案
```

原则：

```text
先讲客户问题，再讲创意解决
先有画面机制，再有漂亮词
每页标题最好是判断句，不是栏目名
OP 命名要能区分方向
方向阐述不能只写情绪词
参考图说明必须告诉客户“看什么”
文案要能被 PPT 页面承载
```

禁区：

```text
不写空词堆叠
不虚构品牌事实
不夸大产品功能
不把内部分析写进客户稿
不写 AI 口吻万能段落
```

## 9. Proposal Architecture v1

目标：正式做 HTML/PPT 之前，决定本轮方案“做什么、不做什么、做到什么颗粒度”。

核心问题：

```text
这次客户需要看什么，才会推进下一步？
```

输入：

```text
项目类型
当前阶段
客户当前要做的决定
利益相关方
资料成熟度
时间压力
视觉资产成熟度
```

输出：

```text
项目阶段
本轮目标
客户/导演当前要判断
推荐方案结构
推荐原因
需要参考图
需要参考视频
需要生图资产
需要文案资产
暂时不做
下一版升级
风险
需要用户确认
```

模块库：

```text
Brief Boundary
Brand / Product / Talent Insight
Creative Platform
OP Matrix
Concept Card
Copy Direction
Storyline Board
Shot Table
Storyboard
Moodboard
Reference Image Pack
Reference Video Pack
KV Direction
Mockup
BTS / Shooting Approach
Product Moment
Social Crop / Platform Adaptation
Execution Plan
Final Recommendation
```

模块深度：

```text
L1：文字说明
L2：文字 + 参考
L3：文字 + 参考 + 生图探索
L4：客户可见精修图 / 可审版
L5：执行级确认稿
```

判断规则：

```text
客户还没选方向：少做分镜，多做 OP / moodboard / reference
客户已经选方向：减少 OP 发散，进入 storyline / visual system
客户问能不能拍：补 shot table / BTS / production approach
客户问好不好看：补 KV / master visual / mockup / reference image
客户问像不像品牌：补 brand visual DNA / official reference / competitor contrast
客户问传播怎么用：补 social crop / platform adaptation / campaign asset
```

Moncler 类项目默认重点：

```text
Brand Visual DNA
Master Scene
KV Direction
Product / Detail Mockup
BTS Texture
Reference Image / Video
Asset Pack
```

晨光刘宇 TVC 类项目默认重点：

```text
Talent × Brand Insight
Creative Platform
OP1 / OP2
Storyline Board
Moodboard
Photography / Video Reference
后续升级到 Shot Table / Storyboard
```

## 10. Visual Asset OS v1

生图作为独立系统，不是临时工具。

主链路：

```text
确认要探索的内容
→ 系统联想 2-4 个视觉方向
→ 搜索/参考计划
→ 官方素材/品牌店铺/官方社媒优先
→ 视觉探索图
→ 选定方向
→ 资产锁
→ slot 清单
→ 独立生图
→ Image QA
→ 进入 HTML / PPT
```

资产锁包括：

```text
人物设计
产品/包装/logo边界
场景环境
道具
光线/色彩
镜头语言
客户可见性
禁止项
```

真实品牌/产品素材优先级：

```text
客户给的素材
> 官网/官方店铺/官方社媒
> 公开参考图
> imagegen 内部探索
```

官方来源素材可进入客户可见参考稿，但必须标源、标用途、标参考性质。

## 11. Image Job Spec v1

作用：把用户的模糊生图需求转成稳定任务。

字段：

```text
job_id
job_type
linked_slot_id
linked_requirement
linked_direction
asset_type
asset_role
primary_request
input_references
visual_locks
composition
lighting_mood
color_palette
materials_textures
text_verbatim
constraints
avoid
client_visibility
qa_checklist
```

job_type：

```text
exploration
ppt_design_reference
key_visual
character_asset
environment_asset
product_asset
storyline_frame
storyboard_frame
mockup
edit
variant
```

硬规则：

```text
正式图必须绑定 slot
探索图可以不绑定 slot，但必须标 internal
分镜批量图必须有 Asset Lock
含文字的图必须写 text_verbatim
生成后必须进入 asset_manifest
```

## 12. PPT / HTML Bridge v1

不做“HTML 硬转 PPT”。

采用同源结构：

```text
SlideSpec
├─ HTML Renderer
└─ PPT Renderer
```

规则：

```text
HTML 审阅稿固定 16:9 slide canvas
PPT 从同一个 SlideSpec 渲染，不重新理解 HTML DOM
PPT 初版使用图片占位符和 slot
每个 slot 独立生成、独立 QA、独立替换
PPT 主视觉设计方案图在正式做 PPT 前完成，默认 2-3 版
```

一致性 Gate：

```text
HTML 截图 vs PPT 渲染图逐页对比
检查文字、图片 slot、表格、图标是否可编辑
不允许整页截图冒充可编辑 PPT
截图降级只能作为特殊例外并明确标注
```

## 13. SlideSpec Minimum Schema v1

作用：HTML 和 PPT 的同源结构，避免二次理解造成漂移。

最小字段：

```text
deck_id
version
project_name
canvas
slides[]
```

canvas：

```text
ratio: 16:9
width: 1920
height: 1080
safe_margin
theme_id
```

slide：

```text
slide_id
page_no
module_type
claim
purpose
linked_requirements
layout_type
content_blocks
image_slots
reference_blocks
notes_internal
client_visibility
status
```

硬规则：

```text
HTML 和 PPT 都只读 SlideSpec
PPT 不从 HTML DOM 猜布局
每页必须有 claim
客户可见页不能显示 notes_internal
所有图片都必须来自 image_slot
所有参考都必须来自 reference_block
```

## 14. Slot Contract Schema v1

作用：让图片生成和 PPT 替换稳定，不互相污染。

字段：

```text
slot_id
slide_id
module_type
purpose
linked_requirement
linked_direction
needed_asset_type
visual_role
ratio
size_hint
reference_ids
asset_lock_id
prompt_job_id
selected_asset_id
client_visibility
qa_status
status
```

needed_asset_type：

```text
ppt_design_reference
key_visual
moodboard_image
storyline_frame
storyboard_frame
mockup
bts_reference
product_closeup
reference_thumbnail
video_frame
background_texture
```

status：

```text
waiting_reference
waiting_prompt
waiting_generation
generated
selected
rejected
client_safe
inserted
superseded
```

硬规则：

```text
没有 slot，不生成正式图
没有 qa_status=pass，不进入客户稿
slot 改变必须更新 SlideSpec
一个 asset 可以服务多个 slot，但必须显式登记
```

## 15. Freeze Points v1

冻结点用于防止后续漂移。

### Asset Lock

触发：

```text
正式分镜生图前
客户可见主视觉前
PPT正式替换图片前
```

控制：图像内容一致。

### Slot Contract

触发：

```text
Proposal Architecture 通过后
进入 HTML / PPT 前
```

控制：图片服务哪个页面/需求。

### SlideSpec Lock

触发：

```text
HTML 客户审阅版确认后
进入 PPT Bridge 前
```

控制：HTML 和 PPT 不漂。

失败回退：

```text
人物/场景漂移 → 回 Asset Lock
图片不知道放哪 → 回 Slot Contract
HTML/PPT不一致 → 回 SlideSpec Lock
客户反馈改结构 → 回 Proposal Architecture
客户反馈改视觉 → 回 Asset Lock / Slot Contract
```

## 16. Review Council / QA v1

目标：每个关键阶段都有反思和建议，不等到 PPT 做完才发现问题。

适用 Gate：

```text
Creative Gate
Copywriting Gate
Proposal Architecture Gate
Reference Gate
Visual Asset Gate
HTML Gate
PPT Gate
Final Gate
```

审核角色：

```text
Requirement Reviewer
Strategy Reviewer
Creative Reviewer
Copy Reviewer
Visual Reviewer
Execution Reviewer
Client Reviewer
Risk Reviewer
```

每次输出：

```text
结论：PASS / REVISE / BLOCKED
主要问题
为什么影响客户判断
建议怎么改
需要谁确认
改动会影响哪些产物
是否需要补搜索/补参考
是否需要重新生成图
```

硬性 BLOCKED：

```text
客户稿出现内部注释
假logo / 假包装字 / 假案例
无来源参考冒充真实案例
contact sheet 直接进客户稿
HTML/PPT严重不一致
PPT不可编辑但未声明
客户关键需求未处理
品牌/产品事实错误
```

## 17. Gate Output Contract v1

统一 Gate 输出：

```text
gate_id
stage
status
score
decision
blocking_issues
revision_items
questions_for_user
questions_for_client
questions_for_stakeholder
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
NEEDS_STAKEHOLDER_INPUT
NEEDS_SEARCH
BLOCKED
```

硬规则：

```text
Gate 不只打分，必须给下一步
Gate 不直接改稿，只给判定和修改项
硬性禁区直接 BLOCKED
PARTIAL_PASS 必须列清带着哪些修改项进入下一阶段
BLOCKED 必须说明回退到哪个状态
```

## 18. Project State Machine v1

主状态：

```text
S0 Intake
S1 Reference Research
S2 Creative Council
S3 Copywriting
S4 Proposal Architecture
S5 Visual Asset OS
S6 SlideSpec / HTML
S7 PPT Bridge
S8 Final QA / Delivery
S9 Retro / Skill Mining
```

状态机总规则：

```text
没有 current_truth，不进入 S2
没有 Reference Card，不进入客户可见参考页
没有 Asset Lock，不进入正式分镜批量生图
没有 Slot Contract，不进入 PPT 替换
没有 locked SlideSpec，不进入 PPT Bridge
没有 Gate PASS / PARTIAL_PASS，不进入客户审阅
```

## 19. Agent Handoff Contract v1

每个 Agent 必须拿任务包、交接证据。

任务包：

```text
task_id
agent
stage
goal
input_files
current_truth_summary
linked_requirements
linked_resolutions
allowed_outputs
forbidden_outputs
gate
deadline_context
```

handoff：

```text
handoff_id
task_id
agent
stage
status
outputs
decisions_made
assumptions
open_questions
risks
evidence
recommended_next_state
```

硬规则：

```text
handoff 不能只写“完成”
assumption 不能升级为 truth
没有 evidence 的内容不能进入客户稿
QA / Review Council 只审核，不直接改生产稿
只由 Main Controller 更新 current_truth
```

## 20. Client-facing Report v1

用户看到的是能决策的简报，不是系统内部文件堆。

固定输出：

```text
本轮状态
关键判断
必须用户确认
需要问客户/导演
建议搜索
当前可推进
主要风险
下一步动作
```

规则：

```text
先说结论
只放用户需要判断的信息
系统细表不直接塞给用户
所有“待确认”集中列出
所有“问客户/导演”的话术直接写成可复制问题
```

## 21. Decision Queue v1

目标：只在真正需要用户决策时打断。

需要用户决策：

```text
选择创意方向
确认是否搜索
确认是否采用某个假设
确认客户可见性
确认是否进入客户稿
确认是否改方案结构
确认是否升级到分镜/执行稿
确认是否安装 Skill
```

系统可继续：

```text
整理资料
抽取需求
生成缺口
提出搜索计划
生成内部假设
整理参考卡片
做初步文案
做方案结构建议
建立 slot
生成 QA 问题
提出修改建议
```

打断规则：

```text
低风险内部工作：继续
影响客户稿：停
影响真实搜索/外部动作：停
影响方向选择：停
影响安装/持久化：停
```

## 22. Feedback Merge v1

客户/导演反馈进入系统后，不直接改稿，先拆解。

字段：

```text
feedback_id
source
event_time
raw_feedback
feedback_type
priority
linked_requirement
linked_artifact
action
status
```

feedback_type：

```text
must_change
suggestion
question
preference
conflict
new_requirement
scope_change
approval
rejection
```

规则：

```text
客户明确覆盖旧需求 → 旧需求 deprecated，新需求 changed/confirmed
客户只是补充 → 原需求保留，新增 requirement
导演执行建议 → 进入 Resolution Track，不直接覆盖客户需求
用户判断 → internal，不能自动升级为客户事实
```

输出：

```text
Change Map
Revised Current Truth
Affected Artifacts
Questions to Ask
Next Version Plan
```

## 23. File Naming / Versioning v1

人类目录命名：

```text
日期_项目_内容_版本
2026-05-13_Moncler_客户资料_V1
2026-05-13_Moncler_方向提案_内部版_V1
2026-05-14_Moncler_客户审阅版_V2
```

Agent 文件命名：

```text
stage_artifact_version
intake_brief_v001.md
reference_cards_v001.csv
proposal_structure_v002.md
slide_spec_v003.json
ppt_fidelity_report_v001.md
```

版本状态：

```text
draft
internal_review
needs_user_confirm
client_review
approved
superseded
final
```

硬规则：

```text
客户反馈后不覆盖旧版本
每个客户审阅版必须能追溯到 source event
每次 SlideSpec 改结构都升版本
每次 Asset Lock 改视觉一致性都升版本
```

## 24. State / File System v1

目录原则：

```text
给用户看的：低密度、中文+英文、放资料/素材/参考/成果
给 Agent 看的：AD-creative，高密度、结构化、可追溯
```

人类可看目录：

```text
00_项目资料_Project/
  01_客户资料_ClientMaterials/
  02_重要素材_KeyAssets/
  03_参考资料_References/
  04_客户审阅版本_ClientReview/
  05_最终交付_FinalDelivery/

01_内部工作台_Workbench/
  01_方向草案_Directions/
  02_文案草案_Copy/
  03_视觉探索_VisualExploration/
  04_方案结构_ProposalArchitecture/
```

Agent 主目录：

```text
AD-creative/
  handoff/
  orchestrator/
  requirements/
  resolutions/
  references/
  creative/
  copywriting/
  proposal_architecture/
  visual_assets/
  image_jobs/
  slide_spec/
  gates/
  agents/
  skill_drafts/
```

核心状态文件：

```text
AD-creative/handoff/当前项目状态.md
AD-creative/handoff/要问谁什么.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/本轮交付说明.md
AD-creative/orchestrator/timeline.csv
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
AD-creative/orchestrator/resolutions.csv
AD-creative/orchestrator/decisions.csv
AD-creative/orchestrator/task_board.csv
AD-creative/orchestrator/artifact_versions.csv
```

## 25. Skill Mining v1

V1 只生成项目内 Skill 草稿，不自动安装。

触发条件：

```text
同类流程重复出现 >= 2 次
输入输出稳定
有 evidence
有明确 Gate
不含客户机密
能减少下次提示词复制成本
```

首批候选：

```text
Brief Gate
Search Plan Gate
Client Feedback Merge
Visual Asset Manifest
Image Slot QA
HTML→PPT Fidelity Gate
PPT Editable Check
Reference Pack
Proposal Architecture
```

草稿目录：

```text
AD-creative/skill_drafts/<skill-slug>/
  SKILL.md
  evidence.md
  install_request.md
```

硬规则：

```text
不自动安装到 ~/.codex/skills
必须有用户确认
必须有 evidence
必须去除客户机密
```

## 26. Minimum Validation Chain v1

目标：先验证一条最小闭环能否稳定跑通。

最小链路：

```text
乱资料输入
→ Intake 一页行动简报
→ Reference Search Plan
→ Reference Cards
→ Creative Council
→ Proposal Architecture
→ Slot Contract
→ 3页 SlideSpec
→ HTML 固定画布预览
→ PPT Bridge 规则检查
→ Gate Report
```

先验证 3 页：

```text
P1 封面 / 主视觉方向
P2 创意方向页
P3 参考图/视频支撑页
```

每页验证：

```text
claim 是否成立
文案是否客户可读
参考是否有来源
图片是否来自 slot
是否有客户可见性
HTML/PPT 结构是否一致
是否能继续扩展成完整方案
```

待用户决策：选择 Moncler 或 晨光刘宇 TVC 作为最小闭环演练基准。

## 27. 持续保存规则

后续构思阶段默认执行：

```text
每完成一个阶段设计，即更新本设计草案
每出现用户确认的关键决策，即写入对应章节
每出现未决问题，即写入“待用户决策”
不把草案标成定稿
不写代码、不初始化项目，除非用户明确要求
```

当前待决策：

```text
1. 最小闭环演练已选择 Moncler，并已生成 docs/design/validation_dry_run_moncler.md
2. 是否把本草案拆成多份 spec 文件
3. 是否后续进入实际项目目录初始化
4. 是否把 GitHub ppt-master 作为 PPT Bridge Adapter 候选进行本地验证
5. 是否把 image_gen / Image 2 作为视觉草图、分镜、设计参考的核心生成能力，并建立正确使用方法
6. 是否引入 Symphony-style Work Board 作为更直观的编排控制平面
```

## 28. GitHub ppt-master 调研

调研对象：

```text
hugohe3/ppt-master
https://github.com/hugohe3/ppt-master
```

阶段结论：

```text
ppt-master 可以解决我们 PPT 问题的一大半，尤其是：
- 可编辑 PPTX
- 避免整页截图
- 避免 HTML/CSS 直接转 PPT 的结构错配
- 用 spec_lock 防止长 deck 视觉漂移
- 从现有 PPTX 提取/派生模板

但它不能直接替代广告创意编排系统。
它更适合作为 PPT Bridge / PPT Renderer 的候选 adapter。
```

### 28.1 对我们有价值的能力

1. Native editable PPTX

PPT Master 的核心目标是输出真实 PowerPoint 对象：

```text
DrawingML shapes
text boxes
charts
gradients
shadows
```

不是整页图片，也不是浏览器 HTML presentation。

这正好对应我们的硬要求：

```text
PPT 不能用整页截图糊弄
文字、图片、图形、表格等应尽量可编辑
```

2. SVG → DrawingML 路线

ppt-master 明确指出 HTML/CSS 和 PowerPoint 的模型不同：

```text
HTML 是文档流
PowerPoint 是绝对坐标画布
```

因此它选择：

```text
AI 生成 SVG
→ 脚本转换为 DrawingML
→ 输出可编辑 PPTX
```

这个判断强化了我们之前的结论：

```text
不要把 HTML DOM 当作 PPT 的源
```

3. spec_lock 机制

ppt-master 要求每页生成前重新读取 `spec_lock.md`，避免长 deck 中颜色、字体、布局漂移。

这与我们的 Freeze Points 对应：

```text
Asset Lock
Slot Contract
SlideSpec Lock
```

4. 模板派生能力

ppt-master 支持从现有 PPTX 派生模板，提取：

```text
theme colors
fonts
master/layout structure
placeholder metadata
reusable image assets
sprite-sheet crop relationships
```

这对广告提案很有价值：

```text
客户给过往高质量提案 → 可抽成项目级模板
品牌有固定 PPT 风格 → 可抽成 template
设计方向已确认 → 可沉淀为后续项目模板
```

5. 图片获取链路

ppt-master 支持 AI image generation 和 web image search，并推荐高影响封面、产品图、人物图优先使用：

```text
用户提供素材 / AI generation > 高质量 web search > 零配置搜索
```

这与我们的 Visual Asset OS / Reference Pack 方向一致。

### 28.2 不能直接解决的问题

ppt-master 不是完整广告创意系统。

它不能替代：

```text
Intake Gate
需求变化时间线
客户/导演/制片需求拆解
Reference Pack 证据链
Creative Council
Copywriting
Proposal Architecture
Visual Asset OS
客户反馈合并
Skill Mining
```

它解决的是后半段的 PPT 生成/转换问题。

### 28.3 对当前方案的修正建议

原设计：

```text
SlideSpec
├─ HTML Renderer
└─ PPT Renderer
```

调研后建议升级为：

```text
SlideSpec
→ SVG Page Spec / SVG Renderer
├─ HTML Preview：展示 SVG 或同坐标画布
└─ PPT Export：SVG → DrawingML → editable PPTX
```

原因：

```text
SVG 和 PPT 都是绝对坐标 2D 画布，结构更接近
HTML 只作为客户预览层，不作为 PPT 源
PPT export 可以借鉴 ppt-master 的转换路线
```

也就是说：

```text
HTML 不再是 PPT 的源
SlideSpec / SVG 才是源
```

### 28.4 推荐集成方式

V1 不直接把 ppt-master 当总系统。

推荐先作为：

```text
PPT Bridge Adapter Candidate
```

验证路径：

```text
3页 SlideSpec
→ 生成 SVG pages
→ 用 ppt-master 或同类 SVG→PPTX 路线导出
→ 渲染 PPT 预览
→ 检查 HTML/SVG 预览与 PPT 一致性
→ 检查可编辑性
```

通过后再决定是否正式集成。

### 28.5 验收指标

本地验证时必须检查：

```text
1. PPT 是否能打开
2. 文字是否可编辑
3. 基础形状是否可编辑
4. 图片是否保持比例
5. slot 替换是否稳定
6. 中文字体是否可靠
7. HTML/SVG 预览与 PPT 渲染是否一致
8. 是否出现整页截图
9. 是否能保留来源说明/参考说明
10. 是否支持广告提案常见版式
```

失败标准：

```text
整页变成图片
文字不可编辑
中文字体错乱
图片裁切漂移
复杂版式导出严重错位
slot 替换不可控
需要大量人工修 PPT 才能交客户
```

### 28.6 暂定结论

```text
ppt-master 值得验证。
它可能是解决 HTML/PPT 一致性与可编辑性的关键参考。
但我们的系统不应变成 ppt-master wrapper。
应把它放在 PPT Bridge Adapter 层，而不是替代上游创意、参考、方案架构和资产系统。
```

## 29. image_gen / Image 2 视觉生成核心能力与使用方法

调研来源：

```text
OpenAI 官方模型页
OpenAI Image Generation Guide
OpenAI Codex imagegen skill
GitHub: openai/codex imagegen skill
GitHub: ResearAI/AutoFigure-Edit
GitHub: wuyoscar/gpt_image_2_skill
GitHub: JuneYaooo/gpt-image2-ppt-skills
GitHub: rsensui2/tekion-slide-generator
GitHub: ConardLi/garden-skills gpt-image-2
GitHub: openclaw/openclaw OpenAI provider docs
```

### 29.1 定位修正

在当前 Codex 环境里，用户所说的 Image 2 应理解为可通过 `image_gen` 使用的高质量图像生成能力。

定位：

```text
不是默认替代所有图像工具
不是最终可编辑 PPT 的结构生成器
但在视觉生成草图、分镜、设计参考、主视觉探索阶段是核心能力
```

核心使用场景：

```text
视觉草图
分镜画面
storyline board
moodboard 补图
PPT主视觉设计参考
KV探索
mockup探索
场景/人物/产品视觉资产探索
多参考图合成/编辑
```

关键原则：

```text
先定义任务，再生成图
先锁参考角色，再喂参考图
先确认资产设计，再批量分镜
先做设计参考，再做PPT结构
生成结果必须进入 asset_manifest
客户可见前必须过 Image QA
```

### 29.2 官方能力边界

gpt-image-2 是当前 OpenAI GPT Image 系列的高质量生成/编辑模型，输入支持：

```text
text
image
```

输出：

```text
image
```

支持：

```text
text-to-image
image editing
multi-image reference/edit
mask-guided edit
flexible size
quality: low / medium / high / auto
output format: png / jpeg / webp
Responses API multi-turn image iteration
Image API one-shot generate/edit
```

关键能力：

```text
高质量摄影/商业视觉
较强文字渲染
多参考图合成
高保真输入图处理
适合产品图、主视觉、UI mockup、信息图、分镜、广告图
```

关键限制：

```text
不支持 native transparent background
复杂 prompt 可能需要较高延迟
精准文字仍需 QA
连续角色/品牌元素仍可能漂移
结构化版式中的精确摆放仍需验证
mask 是 prompt-guided，不保证像素级精确
```

透明图策略：

```text
默认：gpt-image-2 / built-in image_gen 生成纯色 chroma-key 背景 → 本地去背
复杂透明：用户确认后切 gpt-image-1.5 native transparent
```

### 29.3 尺寸和质量策略

gpt-image-2 支持灵活尺寸，但必须满足：

```text
max edge <= 3840px
两边都是 16px 倍数
长短边比例 <= 3:1
总像素 655,360 到 8,294,400
```

常用尺寸：

```text
1024x1024 快速方图
1536x1024 横图
1024x1536 竖图
2048x1152 2K 横图
2752x1536 2K 16:9 高质量 slide 图
3840x2160 4K 横图
2160x3840 4K 竖图
```

质量策略：

```text
low：快速草图、方向探索、缩略图
medium：常规探索、普通客户预览
high：最终主视觉、文字较多、信息图、PPT设计稿、客户可见资产
auto：不确定时由模型选择
```

### 29.4 对我们工作流的意义

image_gen / Image 2 不应只作为“生图按钮”。在视觉草图、分镜、设计参考阶段，它是 Visual Asset OS 的核心生成能力。

它适合承担：

```text
PPT 主视觉设计方案图
广告 Key Visual
产品 mockup
场景 / 环境资产
人物 / 角色资产探索
storyline board
storyboard frame
moodboard image
reference image reconstruction
social crop / platform visual
客户可见参考视觉
```

不适合单独承担：

```text
客户事实判断
品牌/产品授权判断
参考来源证明
PPT 可编辑对象生成
最终 logo / 包装字确认
长期角色一致性保证
```

因此它必须被放进：

```text
Requirement → Slot → Image Job Spec → Image Output → QA → Asset Manifest
```

而不是直接从一句话生成最终客户稿。

### 29.5 GitHub 可借鉴模式

1. openai/codex imagegen skill

可借鉴：

```text
built-in image_gen 默认优先
CLI fallback 用 gpt-image-2
项目资产必须复制到 workspace
每个输入图必须标角色
透明图先 chroma-key，本地去背
gpt-image-2 不设 input_fidelity，因为自动高保真
```

2. ResearAI/AutoFigure-Edit

可借鉴：

```text
gpt-image-2 作为 stage-1 raster generation
后续用 SVG reconstruction 转成可编辑结构
已有图可跳过生成，直接进入结构化重建
生成后做 4K upscale / normalize
```

对我们启发：

```text
客户/AI 生成的参考图可以先作为 raster stage
再进入 SVG/PageSpec/PPT adapter
```

3. gpt-image2-ppt-skills

可借鉴：

```text
gpt-image-2 直接生成 16:9 高清 slide image
支持 HTML viewer + PPTX 打包
支持模板克隆：PPTX 渲染成图 → vision 抽风格 → JSON Schema 复刻
默认并发生成多页
```

对我们限制：

```text
它偏 image-based PPT
客户稿视觉强，但可编辑性可能不满足我们的最终要求
适合早期 PPT 主视觉方案图 / 风格探索 / 客户预览，不适合作为最终可编辑 PPT 唯一路线
```

4. tekion-slide-generator

可借鉴：

```text
Markdown → JSON → prompt → 并行图像生成 → PPTX/PDF
Provider 抽象：OpenAI / Gemini
Visual vs Balanced 两种 slide 风格
参考图片 map：按 slide 匹配参考图
单页重生成和版本号
Logo 保真规则
```

对我们启发：

```text
Visual Asset OS 应增加 Image Use Router
每个 slot 可以绑定 reference image map
PPT主视觉/HTML预览可用 image-based slide，最终 PPT 再走 editable bridge
```

5. garden-skills gpt-image-2

可借鉴：

```text
三模式运行：
Mode A 本地 API 直出
Mode B 委托宿主图像工具
Mode C 只生成 prompt
```

对我们启发：

```text
Image Agent 也要做运行模式判断：
- Codex built-in image_gen
- CLI/API gpt-image-2
- prompt-only
```

6. openclaw provider docs

可借鉴：

```text
gpt-image-2 作为默认生成/编辑模型
透明背景自动切 gpt-image-1.5
支持 2K/4K size override
支持多参考图编辑
```

### 29.6 建议加入 Image Use Router

新增组件：

```text
Image Use Router
```

职责：

```text
判断本次任务如何使用 image_gen / Image 2，以及使用到什么深度
```

不是每个任务都直接生成高精图，而是按用途路由：

```text
不生图，只做 reference pack
prompt-only，先给用户确认
快速视觉探索
设计参考图
客户可见精修图
编辑/合成/变体
批量分镜图
```

决策字段：

```text
job_type
client_visibility
size_required
quality_required
reference_count
needs_edit
needs_mask
needs_transparency
needs_exact_dimension
needs_batch
cost_sensitivity
```

使用策略：

```text
早期视觉探索：先确认内容，再用 image_gen 出少量方向图
PPT主视觉方案图：用 image_gen 做 2-3 版高质量 16:9 设计参考
客户可见 KV：可用 image_gen 精修，但必须强 QA
分镜批量：资产锁后再用 image_gen 批量生成；关键帧优先
透明 PNG：默认 chroma-key，复杂时确认切 gpt-image-1.5
精确尺寸：需要时走 CLI/API 路线
多参考图编辑：适合结合 Image 2
只需要真实案例证据：不生图，走 Reference Pack
```

### 29.7 Image 2 与 PPT Bridge 的结合

建议新增两条路径：

#### A. Image-based Preview Path

用于：

```text
PPT主视觉设计方案图
风格探索
客户快速预览
情绪板
参考支撑页
```

路径：

```text
SlideSpec / Proposal Structure
→ Image Job Spec
→ gpt-image-2 生成 16:9 slide visual
→ HTML Preview / Client Review
→ 不直接作为最终 editable PPT
```

#### B. Editable Bridge Path

用于：

```text
最终 PPTX
可编辑客户交付
后续客户修改
```

路径：

```text
SlideSpec
→ SVG Page Spec / PPT adapter
→ editable PPTX
→ 用 gpt-image-2 资产填入 image slots
```

规则：

```text
Image 2 可以生成视觉稿和资产
不能替代可编辑 PPT 结构
最终 PPT 仍必须检查文字/slot/形状可编辑性
```

### 29.8 Image QA 升级

Image 2 产物进入客户稿前必须检查：

```text
是否绑定 requirement
是否绑定 slot
是否使用正确 reference role
是否出现假 logo / 假包装字
是否出现不可控文字
人物/场景/产品是否漂移
是否满足尺寸和比例
是否有来源/生成记录
是否可客户可见
是否进入 asset_manifest
```

对于文字型图像额外检查：

```text
文字是否逐字正确
是否有乱码
是否被裁切
是否出现额外文字
中文是否准确
```

### 29.9 暂定结论

```text
image_gen / Image 2 是 Visual Asset OS 在视觉草图、分镜、设计参考阶段的核心生成能力。

但它要被正确使用：
- 不能跳过 brief / reference / asset lock
- 不能用一句模糊话直接生成客户稿
- 不能替代客户事实和来源证据
- 不能替代可编辑 PPT Bridge

尤其适合：
- PPT主视觉设计方案图
- KV / mockup / moodboard
- reference reconstruction
- story / storyboard visual
- slide-style visual preview
- 多参考图编辑与合成

但它不能替代：
- 参考证据链
- 资产锁
- Slot Contract
- 可编辑 PPT Bridge
- 客户稿 QA
```

后续应做“正确使用方法”的最小验证：

```text
同一创意方向
→ 生成 1 张 PPT主视觉方案图
→ 生成 2 张 slot 资产图
→ 生成 1 张 storyline board
→ 检查一致性、文字、客户可见性、manifest
→ 判断每类任务应如何使用 image_gen / Image 2，以及使用到什么深度
```

## 30. Superpowers / Symphony 编排评审与优化

调研来源：

```text
Superpowers workflow
https://github.com/obra/superpowers

OpenAI Symphony article
https://openai.com/zh-Hans-CN/index/open-source-codex-orchestration-symphony/

OpenAI Symphony repo
https://github.com/openai/symphony

Symphony SPEC
https://github.com/openai/symphony/blob/main/SPEC.md
```

### 30.1 当前设计完整度判断

当前草案在以下部分已经比较完整：

```text
广告创意工作流
Intake / Reference / Creative / Copy / Proposal Architecture
Visual Asset OS
image_gen / Image 2 使用方式
HTML / PPT Bridge
Gate / Review Council
Skill Mining
文件系统和状态文件
```

当前不足主要在“智能体编排层”：

```text
还是以阶段流程为主，不够像任务控制平面
缺少 Work Item 抽象
缺少任务依赖 DAG
缺少运行状态 / retry / stalled / canceled
缺少可视化 status surface
缺少 agent run record
缺少并发策略
缺少人工 review packet 的标准形态
缺少 workflow policy 文件
```

结论：

```text
设计方向正确，但编排层还不够完整。
需要从“阶段驱动”升级为“Work Board + Stage Router + Agent Run”的双层结构。
```

### 30.2 Symphony 可借鉴点

Symphony 的核心不是 Linear 本身，而是：

```text
把任务管理工具变成 agent 控制平面
把 agent session 从人工盯梢变成 work item 驱动
每个 work item 有独立 workspace / run / status / retry
人只 review 结果，不持续 micromanage
```

可迁移到本项目的点：

```text
1. Work Board 作为控制平面
2. 每个任务有状态、优先级、blocked_by、owner_agent
3. agent 只处理未阻塞任务
4. 支持并发执行独立任务
5. 支持 stalled / retry / canceled
6. 输出 review packet，而不是只说完成
7. workflow policy 写入项目文件，可版本化
8. 状态面板让用户直观看当前项目推进到哪
```

不能直接照搬的点：

```text
Symphony 面向代码 issue / PR
广告创意任务不是都能自动执行
很多节点需要用户/客户/导演确认
创意判断不能完全 daemon 化
参考搜索、图片生成、客户稿输出涉及版权和可见性风险
```

### 30.3 Superpowers 可借鉴点

Superpowers 的核心流程：

```text
Brainstorming
→ Writing Plans
→ Implementation / TDD
→ Verification
→ Review
```

对应到广告创意：

```text
Brainstorming = 需求/创意/方案架构讨论
Writing Plans = 本轮方案结构和任务包
Implementation = Research / Copy / Visual / HTML / PPT 执行
Verification = Gate / Review Council
Review = 用户/客户审阅
```

Subagent-driven development 可迁移为：

```text
每个独立任务给一个 fresh agent
只给任务所需上下文
不继承完整会话历史
先做产物，再做 spec/review 双重审核
```

对本项目的启发：

```text
Research / Reference / Copy / Visual / QA 可以并行
Creative / Proposal Architecture 需要主控合成，不能完全并行
生产 Agent 和 Review Agent 要分开
每个 Agent 任务必须窄、独立、带输出契约
```

### 30.4 建议新增 Orchestration Control Plane v1

新增一层：

```text
Orchestration Control Plane
```

位置：

```text
Project State Machine
→ Work Board
→ Stage Router
→ Agent Run
→ Gate
→ Review Packet
```

它解决：

```text
当前有哪些任务
哪些任务被阻塞
哪些可并行
哪个 agent 在做什么
产物在哪里
哪些需要用户确认
哪些失败需要重试
哪些能进入客户稿
```

### 30.5 Work Item Schema v1

每个工作单元统一成 Work Item。

字段：

```text
work_id
title
work_type
stage
state
priority
owner_agent
created_from_event
linked_requirements
linked_resolutions
linked_slots
linked_references
blocked_by
depends_on
allowed_inputs
expected_outputs
gate_required
client_visibility_risk
human_review_required
run_mode
due_context
```

work_type：

```text
intake
research
reference_card
creative_direction
copywriting
proposal_architecture
image_job
asset_qa
slide_spec
html_preview
ppt_bridge
qa_review
feedback_merge
skill_mining
```

state：

```text
todo
ready
running
waiting_user
waiting_client
waiting_stakeholder
waiting_search
blocked
review
accepted
rejected
superseded
done
```

run_mode：

```text
interactive
subagent
manual_user
external_search
image_gen
ppt_adapter
prompt_only
```

### 30.6 Agent Run Schema v1

每次 agent 执行都应有 run record。

字段：

```text
run_id
work_id
agent
started_at
ended_at
status
attempt
input_package
output_package
evidence
tokens_or_cost
failure_reason
retry_after
next_action
```

status：

```text
preparing
running
succeeded
failed
stalled
timed_out
canceled_by_state_change
needs_context
needs_human_review
```

规则：

```text
同一个 work item 可以多次 run
run succeeded 不等于客户可见
客户可见必须过 Gate
失败要写 failure_reason
重试必须增加 attempt
```

### 30.7 更直观的 Status Surface

当前设计只有文件，不够直观。

建议增加一个用户可读状态面：

```text
AD-creative/handoff/项目看板.md
```

内容：

```text
当前阶段
本轮目标
正在做
已完成
被阻塞
待你确认
待问客户/导演
下一步
风险
最近产物
```

后续如果做 UI，可以直接映射成：

```text
Timeline
Work Board
Artifact Gallery
Gate Log
Decision Queue
Reference Pack
Asset Board
```

### 30.8 编排策略：分两种模式

#### Interactive Strategy Mode

适用：

```text
Intake
Creative Council
Proposal Architecture
方向选择
客户稿进入前
```

特点：

```text
主控和用户强交互
不追求自动并发
重点是判断、取舍、确认
```

#### Autonomous Production Mode

适用：

```text
Reference Card 整理
素材登记
Image Job 草案
Copy 初稿
HTML 预览生成
PPT Bridge 验证
QA 检查
Skill Mining 草稿
```

特点：

```text
按 Work Board 自动派发
独立任务可并行
失败可 retry
结果进入 Review Packet
```

关键规则：

```text
高判断任务走 Interactive
低风险生产任务走 Autonomous
影响客户稿的任务必须回到 Review
```

### 30.9 并发策略

可并行：

```text
品牌官方资料搜索
同类广告参考搜索
视频参考时间码整理
Reference Cards
Copy 备选标题
Image Job Spec 草案
PPT 主视觉方向探索
HTML overflow QA
PPT editable QA
```

不可并行或需主控合成：

```text
Current Truth 更新
Creative Direction 最终推荐
Proposal Architecture 决策
Asset Lock 最终确认
SlideSpec Lock
客户稿发布
Skill 安装
```

### 30.10 Workflow Policy 文件

借鉴 Symphony 的 `WORKFLOW.md`，本项目应有项目内 policy 文件。

建议：

```text
AD-creative/orchestrator/WORKFLOW.md
```

内容：

```text
项目默认流程
状态定义
哪些任务可自动执行
哪些必须用户确认
Agent 角色和权限
并发上限
Gate 硬性禁区
客户可见规则
失败回退
```

这个文件应是 agent 编排的最高项目规则，高于单个 agent 的临时提示词。

### 30.11 对当前方案的具体修正

当前设计从：

```text
Stage-driven workflow
```

升级为：

```text
Stage-driven judgment
+ Work-item-driven production
```

也就是：

```text
主控判断项目阶段和方向
Work Board 承载具体任务
Agent Run 承载执行
Gate 承载验收
Status Surface 承载用户可视化
```

### 30.12 暂定结论

```text
当前方案内容完整度够，但编排层还可以明显优化。
不建议 V1 直接接 Symphony/Linear。
建议先做 Symphony-style local Work Board。
```

V1 推荐形态：

```text
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/WORKFLOW.md
AD-creative/handoff/项目看板.md
```

后续可选升级：

```text
接 Linear / GitHub Issues
接 Symphony-style daemon
接本地 UI
接 LangGraph / CrewAI / ORCH adapter
```

这能同时满足：

```text
更高效：独立任务并行，不靠人工盯每个 agent
更直观：项目看板显示状态、阻塞、待确认、产物
更安全：客户可见内容仍必须 Gate
更可扩展：未来可接 Symphony / Linear / UI
```

## 31. Revised Orchestration Architecture v1

在引入 Symphony-style Work Board 后，v1 架构应从单纯阶段流程升级为四层：

```text
Layer 1: Project Truth
Layer 2: Stage Router
Layer 3: Work Board
Layer 4: Agent Runs / Gates / Review Packets
```

### 31.1 Layer 1: Project Truth

职责：

```text
维护当前项目事实、需求、时间线、决策和版本。
```

核心文件：

```text
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/timeline.csv
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/resolutions.csv
AD-creative/orchestrator/decisions.csv
AD-creative/orchestrator/artifact_versions.csv
```

规则：

```text
只有 Main Controller 可以更新 current_truth
任何 assumption 不能自动升级为 truth
客户/导演/用户反馈必须先进入 timeline
变更必须产生 decision 或 resolution
```

### 31.2 Layer 2: Stage Router

职责：

```text
判断项目当前处于哪个阶段，下一步应该进入哪个阶段。
```

输入：

```text
current_truth
requirements
gaps
resolutions
gate_log
decision_queue
```

输出：

```text
current_stage
allowed_next_stages
blocked_stages
required_decisions
work_items_to_create
```

阶段判断不再只靠线性流程，而是靠状态条件：

```text
没有 current_truth → Intake
有 search_plan 且用户确认搜索 → Reference Research
有 enough reference + requirements → Creative Council
有 recommended direction → Copywriting
有 copy + client_decision → Proposal Architecture
有 proposal_structure → Visual Asset OS / SlideSpec
有 locked SlideSpec → PPT Bridge
有 client-visible output → Final QA
```

### 31.3 Layer 3: Work Board

职责：

```text
把阶段判断拆成可执行 work items。
```

Work Board 解决：

```text
任务怎么并行
哪些任务被阻塞
哪些任务等用户/客户/导演
哪些任务可交给 subagent
哪些任务只能主控处理
```

核心文件：

```text
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/work_dependencies.csv
AD-creative/orchestrator/agent_routes.csv
```

Work Item 最小字段：

```text
work_id
title
work_type
stage
state
priority
owner_agent
depends_on
blocked_by
linked_requirements
linked_artifacts
expected_outputs
gate_required
human_review_required
run_mode
```

### 31.4 Layer 4: Agent Runs / Gates / Review Packets

职责：

```text
记录每次执行、审核和交付给用户看的结果。
```

核心文件：

```text
AD-creative/orchestrator/agent_runs.csv
AD-creative/gates/gate_log.csv
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/本轮交付说明.md
```

规则：

```text
Agent Run 成功不等于 Gate 通过
Gate 通过不等于客户可见
客户可见必须满足 visibility + qa_status + source_trace
Review Packet 是给用户看的，不是内部日志
```

## 32. Agent Role Redesign v1

原来的 agent 列表偏“部门式”。优化后改成“能力式 + 阶段式”混合。

### 32.1 Main Controller

职责：

```text
维护 current_truth
运行 Stage Router
创建 Work Items
派发 Agent Runs
合成 Review Packets
决定是否进入下一阶段
```

不能做：

```text
直接跳过 Gate
把假设写成事实
把客户不可见资产塞进客户稿
```

### 32.2 Intake Analyst

职责：

```text
抽取需求
识别缺口
拆 timeline event
生成问题包
生成 Search Plan
```

### 32.3 Reference Researcher

职责：

```text
搜索/整理品牌、竞品、平台、视频、视觉参考
生成 Reference Cards
标来源、时间码、用途、客户可见性
```

### 32.4 Creative Strategist

职责：

```text
运行 Creative Council
产出方向池
推荐方向/备选方向/不建议方向
给文案和视觉阶段输入
```

### 32.5 Copywriter

职责：

```text
命名
claim titles
方向阐述
logline
参考说明
客户可读文案
```

### 32.6 Proposal Architect

职责：

```text
判断本轮方案结构
决定 moodboard/storyline/storyboard/mockup/BTS/KV 是否需要
决定模块深度
生成 needed slots / needed references / needed assets
```

### 32.7 Visual Director

职责：

```text
定义视觉方向
组织 asset lock
定义 image_gen 使用策略
控制风格一致性
决定哪些图只是探索，哪些可客户可见
```

### 32.8 Image Producer

职责：

```text
把用户模糊语言转成 Image Job Spec
调用 image_gen / Image 2
生成视觉草图、分镜、设计参考、mockup
记录 prompt / reference / 输出
```

注意：

```text
Image Producer 不决定客户可见性
Image Producer 不绕过 Asset Lock
Image Producer 不直接改 SlideSpec
```

### 32.9 Slide Architect

职责：

```text
维护 SlideSpec
设计 HTML preview / PPT bridge 的同源结构
管理 slot contract
```

### 32.10 PPT Producer

职责：

```text
把 SlideSpec 导出为可编辑 PPT
验证 PPT 可编辑性
验证与 HTML/SVG preview 一致性
```

### 32.11 QA / Review Council

职责：

```text
按 Gate Output Contract 审核
输出 PASS / PARTIAL_PASS / REVISE / BLOCKED
提出可执行 revision items
```

### 32.12 Skill Miner

职责：

```text
识别重复通路
记录 evidence
生成项目内 Skill 草稿
不自动安装
```

## 33. Review Packet v1

Review Packet 是每次交给用户看的决策包，不是内部日志。

触发：

```text
阶段完成
Gate 出现 PARTIAL_PASS / BLOCKED
需要用户确认
客户稿准备前
```

格式：

```text
review_id
stage
status
what_changed
key_decisions
recommended_action
options_if_any
risks
questions_to_user
questions_to_client_or_stakeholder
artifacts_to_review
next_step
```

规则：

```text
如果没有需要用户决策，Review Packet 只汇报进度并继续
如果影响客户稿，必须暂停等待确认
如果只是内部优化，不打断用户
```

## 34. Minimal Work Board Example

以晨光刘宇 TVC 早期方向提案为例：

```text
W-001 Intake: 解析客户资料
state: done
owner: Intake Analyst

W-002 Research: 搜集晨光官方/文具TVC/艺人语境参考
state: ready
owner: Reference Researcher
depends_on: W-001

W-003 Creative: 生成方向池
state: blocked
blocked_by: W-002
owner: Creative Strategist

W-004 Copy: OP命名和方向文案
state: todo
depends_on: W-003
owner: Copywriter

W-005 Proposal Architecture: 判断本轮是否需要 moodboard / storyline board / 分镜
state: todo
depends_on: W-003,W-004
owner: Proposal Architect

W-006 Visual: 生成 PPT 主视觉设计参考
state: todo
depends_on: W-005
owner: Visual Director + Image Producer

W-007 SlideSpec: 生成 3 页预览结构
state: todo
depends_on: W-005,W-006
owner: Slide Architect

W-008 QA: Reference / Copy / Visual / SlideSpec Gate
state: todo
depends_on: W-007
owner: QA Council
```

这个例子说明：

```text
阶段不等于任务
任务可并行
Creative 和 Proposal Architecture 需要等待关键输入
Image 生成不能早于 Proposal Architecture / Asset intent
QA 是独立 work item
```

## 35. 当前方案下一步

当前设计已经形成：

```text
广告创意链路
视觉资产链路
PPT/HTML链路
Gate审核链路
Skill沉淀链路
Symphony-style编排链路
```

下一步不建议继续扩概念。

建议进入：

```text
Minimum Validation Chain 设计细化
```

需要补齐：

```text
1. 选择一个真实案例：Moncler 或 晨光刘宇 TVC
2. 生成该案例的 Work Board 示例
3. 生成 3 页 SlideSpec 示例
4. 设计 Reference Pack 示例
5. 设计 Image Job Spec 示例
6. 设计 Gate Report 示例
```

这一步会检验：

```text
工作流是否真能跑
Work Board 是否直观
image_gen 是否用对
Reference Pack 是否能说服客户
SlideSpec/PPT Bridge 是否能落地
```

## 36. Moncler Minimum Validation Dry Run 结果

验证文档：

```text
docs/design/validation_dry_run_moncler.md
```

验证类型：

```text
纸面演练 / Dry Run / 不执行真实搜索 / 不生图 / 不做PPT
```

本次 dry run 结论：

```text
当前 v1 设计可以指导 Moncler 类高端品牌视觉项目的早期方案搭建。
Work Board、Proposal Architecture、Reference Pack、Image Job Spec、Slot Contract、SlideSpec、Gate 都能形成闭环。
```

验证通过的点：

```text
1. Work Board 比单纯阶段流程更直观
2. Proposal Architecture 能避免过早做 storyboard
3. Reference Pack 字段能防止素材堆
4. Image Job Spec 能把 image_gen 使用限制在正确边界内
5. Slot Contract 能提前承接 PPT/HTML 结构
6. Gate 能提前发现客户稿风险
```

发现的问题：

```text
1. Proposal Architecture 需要项目类型默认模块模板
2. Image Use Router 需要项目类型规则
3. Reference Gate 需要 stop condition，避免搜索无限扩张
4. SlideSpec 需要更清楚区分 internal_preview / client_review / final_delivery
5. Work Board 需要明确 waiting_user 与 waiting_client 的区别
```

### 36.1 项目类型默认模块模板

新增默认模板：

#### Moncler 类高端品牌视觉项目

默认重点：

```text
Brand Visual DNA
Master Visual / Master Scene
KV Direction
Product Detail / Mockup
BTS / Shooting Texture
Reference Image / Video Pack
Asset Plan
```

默认暂不优先：

```text
完整 storyboard
30秒剧情线
重旁白文案
社媒种草脚本
```

判断逻辑：

```text
客户要看品牌感 → Brand Visual DNA + 官方参考
客户要看视觉质感 → Master Visual + KV Direction
客户要看产品呈现 → Product Detail + Mockup
客户要看能不能拍 → BTS / Shooting Texture
客户要看传播延展 → Platform Crop / Campaign Asset
```

#### TVC 类故事/艺人项目

默认重点：

```text
Talent / Brand Insight
Creative Platform
OP1 / OP2
Storyline Board
Moodboard
Photography / Video Reference
后续升级 Shot Table / Storyboard
```

#### 社媒种草/平台内容项目

默认重点：

```text
Platform Context
User Scene
Content Hook
Creator / Talent Format
Product Moment
Reference Video
Social Crop
```

### 36.2 Image Use Router 项目类型规则

Moncler 类项目：

```text
PPT主视觉设计参考优先于 storyboard
KV / mockup / product detail 优先于剧情分镜
真实官方产品参考优先于自由生成
没有产品授权前，生成图默认 internal
BTS 可用 image_gen 做氛围草图，但客户稿优先真实视频参考
```

TVC 类项目：

```text
先 storyline board，再关键帧分镜
人物/场景/产品资产锁后再批量分镜
reference video 时间码优先于大批 moodboard
```

社媒类项目：

```text
优先做平台语境参考、封面/首帧、产品动作图
不优先做高成本 KV，除非客户需要 campaign asset
```

### 36.3 Reference Gate Stop Condition

每次搜索计划必须有 stop condition。

字段：

```text
minimum_reference_count
required_source_types
required_modules_covered
quality_threshold
client_visibility_requirement
time_budget
```

示例：

```text
至少 6 条可信来源参考：
- 2 条官方 campaign / KV
- 2 条产品/材质/细节
- 1 条 BTS / shooting texture
- 1 条平台或传播延展
达到后停止扩搜，进入 Reference Gate
```

### 36.4 SlideSpec 可见性状态

SlideSpec 增加 client_visibility 状态：

```text
internal_preview
client_review_pending_qa
client_review
final_delivery
blocked
```

规则：

```text
internal_preview 可以含占位符和内部判断
client_review_pending_qa 需要等待 QA
client_review 不得出现内部注释、假logo、未授权参考、contact sheet
final_delivery 必须通过 Final Gate
blocked 不得导出给客户
```

### 36.5 Work Board waiting 状态细分

state 增加：

```text
waiting_user
waiting_client
waiting_director
waiting_producer
waiting_brand_legal
waiting_platform
```

规则：

```text
waiting_user：需要用户做方向/搜索/可见性/结构确认
waiting_client：需要客户确认 brief、产品、方向、交付边界
waiting_director：需要导演确认拍法、可执行性、镜头语言
waiting_brand_legal：需要品牌/法务确认 logo、产品、肖像、素材授权
```

## 37. GStack / Orchestration Engineering Review

调研对象：

```text
GStack / Superpowers 工作流
OpenAI Symphony
OpenAI Agents SDK
LangGraph
CrewAI
AutoGen
```

本节回答：

```text
当前设计是否完整
哪些地方还能优化
智能体编排是否应该换成更高效、更直观的方式
```

### 37.1 结论

当前设计在“广告创意工作流”层已经够完整。

不够完整的是“编排控制平面”：

```text
缺少可执行的任务状态契约
缺少 append-only event log
缺少 orchestrator loop
缺少 agent run isolation 规则
缺少 status dashboard 的最小数据模型
缺少失败重试/取消/阻塞处理
缺少每个 agent 的 proof-of-work 标准
```

也就是说：

```text
内容系统已经有了
执行系统还没成型
```

### 37.2 GStack 评审判断

GStack / Superpowers 的有效启发：

```text
Design First：先锁设计，再执行
Spec First：方案必须落盘
Subagent-driven：独立任务用 fresh subagent
Verification before completion：不能只说完成，要证据
Plan-eng-review：先做架构/数据流/测试/失败场景审查
Boil the Lake：AI 边际成本低时，不要做半套验证
```

对本项目的修正：

```text
不要再只做纸面 dry run
下一步应做 Orchestration Prototype v0
用最少文件证明 Work Board / Agent Run / Gate / Status Surface 能工作
```

### 37.3 Symphony 启发

Symphony 的重点不是“用 Linear”，而是：

```text
把任务系统当作 agent 控制平面
每个任务有状态、责任、上下文、结果、review
agent 不靠聊天记忆，而靠 work item 运行
人审结果，不盯过程
```

适合迁移的概念：

```text
Work Item
Agent Run
Status Sync
Review Packet
Retry / stalled / blocked
Policy file
```

不建议 V1 直接照搬：

```text
Symphony 更偏代码 issue / PR
广告创意有客户可见性、参考版权、生图资产、PPT交付等特殊风险
直接接 Linear/Symphony 会让工具驱动业务，而不是业务驱动工具
```

建议：

```text
先做 Symphony-style local control plane
后续再接 Linear / GitHub Issues / Symphony daemon
```

### 37.4 OpenAI Agents SDK 启发

Agents SDK 适合：

```text
manager agent → specialist agents
handoffs
guardrails
structured outputs
tracing
tool calling
```

适合本项目的部分：

```text
Creative Council 内部多角色
Research / Copy / Visual / QA 的结构化交接
Gate guardrails
trace 每次 agent run
```

不足：

```text
它不是项目管理系统
不天然解决长期项目时间线
不天然解决客户资料版本、PPT资产、reference证据链
```

建议：

```text
未来可作为 Agent Runtime Adapter
但 V1 的 source of truth 仍应是 AD-creative 文件状态
```

### 37.5 LangGraph 启发

LangGraph 适合：

```text
durable state
checkpoint
human-in-the-loop
branch / resume
graph-based workflow
```

适合本项目的部分：

```text
Stage Router
Gate 后暂停等待用户
客户反馈后回退到某个节点
长项目恢复
```

不足：

```text
需要工程化 runtime
对当前讨论阶段过重
如果过早引入，会先服务框架而不是服务广告流程
```

建议：

```text
V1 保持 file-driven
V2 如需自动化 runtime，再把 Stage Router 映射到 LangGraph
```

### 37.6 CrewAI / AutoGen 启发

CrewAI 适合：

```text
role-based crews
flow + crew 组合
多 agent 按任务协作
```

可借鉴：

```text
Creative Council / Review Council 可被建模为 crew
Proposal Architecture 可作为 flow 中的决策节点
```

AutoGen 适合：

```text
多 agent 对话实验
原型验证
```

但本项目不应以“agent 互聊”为核心。

建议：

```text
Crew/AutoGen 可做实验适配
主架构仍以 Work Board + file state 为核心
```

### 37.7 当前设计缺口

#### Gap 1: 没有 append-only event log

现在有 timeline，但还不是完整 event log。

建议新增：

```text
AD-creative/orchestrator/events.jsonl
```

记录所有状态变化：

```text
event_id
event_type
timestamp
actor
source
payload
affected_ids
```

event_type：

```text
input_received
requirement_created
requirement_changed
work_created
work_started
work_blocked
agent_run_started
agent_run_finished
gate_passed
gate_blocked
decision_requested
decision_resolved
artifact_created
artifact_superseded
```

理由：

```text
CSV 表适合看当前状态
JSONL event log 适合追溯变化
```

#### Gap 2: 没有 Orchestrator Loop

建议定义最小循环：

```text
1. read current_truth + events + work_items
2. update derived state
3. route stage
4. create missing work items
5. find ready work
6. dispatch allowed work
7. collect handoff
8. run gate
9. update status dashboard
10. stop only on decision_required / blocked / done
```

这比“阶段流程图”更接近真实运行。

#### Gap 3: 没有 Proof-of-Work 标准

每个 agent 不能只输出结论。

建议每个 handoff 必须包含：

```text
outputs
evidence
source_refs
assumptions
rejected_options
qa_self_check
next_recommendation
```

没有 evidence 的输出不能进入客户稿。

#### Gap 4: 状态面仍是文档，不够直观

建议 `项目看板.md` 必须固定格式：

```text
Current Stage
Ready Work
Running Work
Blocked Work
Waiting On User
Waiting On Client
Latest Artifacts
Gate Status
Next 3 Actions
```

后续 UI 原型可以直接读取这些字段。

#### Gap 5: 缺少并发安全规则

建议：

```text
Main Controller 独占 current_truth
每个 specialist agent 只能写自己的 stage output
QA agent 只写 gate/review，不改生产文件
SlideSpec Lock 后，修改必须开新 work item
Asset Lock 后，改视觉必须开新 asset_lock_version
```

### 37.8 推荐最终编排形态

V1 采用：

```text
Local File Control Plane
```

最小文件：

```text
AD-creative/orchestrator/WORKFLOW.md
AD-creative/orchestrator/events.jsonl
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

执行形态：

```text
主控 Agent 读写控制平面
specialist subagents 处理 work item
每个 run 输出 handoff
Gate 统一验收
Status Surface 给用户看
```

未来升级：

```text
V1.5: 本地 CLI aco status / aco gate / aco work
V2: UI 读 Work Board / Event Log / Artifact Gallery
V3: Symphony / Linear / GitHub Issues adapter
V4: LangGraph / Agents SDK runtime adapter
```

### 37.9 三种实现路线对比

#### A. 纯文档模板

优点：

```text
最快
低风险
适合继续讨论
```

缺点：

```text
不能证明编排有效
不能减少手工协调
很快又会变成对话驱动
```

适合：

```text
现在之前的阶段
```

结论：

```text
已经不够了
```

#### B. Local File Control Plane

优点：

```text
最贴合当前项目
不依赖外部服务
可被 Codex/subagents 直接读写
未来可接 CLI/UI/Symphony
能真实验证编排
```

缺点：

```text
需要建立最小 schema 和操作规则
初期仍是文件驱动，不是漂亮 UI
```

适合：

```text
下一步
```

结论：

```text
推荐
```

#### C. 直接接 Symphony / LangGraph / Agents SDK

优点：

```text
自动化强
可观测性更好
长期扩展性强
```

缺点：

```text
过早
会把注意力从广告流程转移到框架集成
创意资产、reference、PPT 这些特殊对象还没验证清楚
```

适合：

```text
Local Control Plane 跑通之后
```

结论：

```text
后置
```

### 37.10 下一步工程动作

下一步不再继续抽象概念。

建议做：

```text
Orchestration Prototype v0
```

目标：

```text
用真实文件证明编排控制平面能工作
```

范围：

```text
不做 UI
不做真实 agent 自动派发
不做真实 PPT
不做真实生图
只做控制平面最小可用样例
```

需要创建：

```text
AD-creative/orchestrator/WORKFLOW.md
AD-creative/orchestrator/events.jsonl
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

用 Moncler 填一组样例：

```text
Intake done
Reference Search waiting_user
Proposal Architecture ready
Image Job blocked_by_reference
SlideSpec ready
QA todo
```

验收：

```text
能一眼看出当前项目状态
能一眼看出什么被阻塞
能一眼看出下一步谁做什么
能一眼看出哪些需要用户/客户确认
能证明 Work Board 比长对话更好用
```

## 39. GitHub Orchestration Landscape Research

本轮继续研究对象：

```text
OpenAI Symphony
ComposioHQ/agent-orchestrator
awslabs/cli-agent-orchestrator
langchain-ai/open-swe
OpenAI Agents SDK
Pullfrog / Optio / Fusion / Weave / HerdOS / Orca 等公开项目形态
```

结论：

```text
没有一个项目可以直接拿来解决广告创意编排。
但它们给出了更成熟的控制面模式。
```

### 39.1 Composio Agent Orchestrator 可借鉴

项目：

```text
https://github.com/ComposioHQ/agent-orchestrator
```

核心模式：

```text
每个 issue 一个 agent
每个 agent 一个 git worktree / branch / PR
dashboard 统一监督
CI失败和review comments 自动回流给 agent
tracker/runtime/agent/terminal/notifier 插件化
```

对我们的启发：

```text
控制面应该有插件槽，而不是写死实现
```

可迁移为：

```text
runtime: codex_subagent / local_cli / future_cao / future_agents_sdk
tracker: local_work_board / linear / github
asset_backend: local_files / future_drive
ppt_adapter: ppt-master / presentations / custom
image_backend: image_gen / prompt_only / future_provider
notifier: handoff_md / desktop / slack
```

不直接采用原因：

```text
它面向代码 PR，不面向广告客户稿
worktree/PR 模型对 reference、image slot、PPT、客户可见性过重
```

### 39.2 AWS CLI Agent Orchestrator 可借鉴

项目：

```text
https://github.com/awslabs/cli-agent-orchestrator
```

核心模式：

```text
Supervisor-worker
每个 agent 一个 tmux session
通过 MCP 暴露 handoff / assign / send_message
支持 Web UI / CLI / MCP control planes
支持跨 provider：Codex、Claude Code、Gemini CLI、OpenCode 等
支持 agent profile 和 allowedTools
```

对我们的启发最大。

可迁移为三种任务调度原语：

```text
handoff：同步交接，等待结果
assign：异步派发，不阻塞主控
send_message：给已有 agent 追加上下文或反馈
```

映射到广告创意：

```text
handoff:
- Intake 分析
- Proposal Architecture
- Gate Review

assign:
- Reference Cards 整理
- 视频时间码整理
- Copy 备选标题
- Image Job Spec 草案

send_message:
- 客户反馈后要求某 agent 修正
- QA 退回某个 work item
- 用户补充资料后更新上下文
```

Agent Profile 启发：

```text
每个广告 agent 应有 profile：
- name
- description
- role
- allowed_files
- allowed_tools
- forbidden_outputs
- output_contract
```

这比现在单纯写 agent 职责更可执行。

### 39.3 Symphony 可借鉴

项目：

```text
https://github.com/openai/symphony
```

核心模式：

```text
WORKFLOW.md 是 repo-owned policy
orchestrator 轮询 tracker
创建 isolated workspace
维护 authoritative runtime state
支持 concurrency / retry / reconciliation / stall timeout
worker 成功不等于任务完成，可停在 human review
```

对我们的直接修正：

```text
AD-creative/orchestrator/WORKFLOW.md 必须成为项目规则入口
需要 events.jsonl + work_items.csv + agent_runs.csv
需要 reconciliation
```

广告创意版 reconciliation：

```text
客户新反馈覆盖旧方向 → 取消/废弃相关 work items
SlideSpec Lock 后客户改结构 → 取消 PPT Bridge，回 Proposal Architecture
Asset Lock 后产品变更 → 取消相关 image jobs，重建 asset lock
Reference 被判 internal_only → 移出客户可见页
Gate BLOCKED → 停止下游客户稿导出
```

### 39.4 OpenSWE / LangGraph 可借鉴

项目：

```text
https://github.com/langchain-ai/open-swe
```

可借鉴：

```text
异步 coding agent
多平台触发
sandbox engine
context engine
orchestrator
validation
real-time status updates
```

对我们的启发：

```text
如果后续做自动化 runtime，应选择“异步长任务 + 验证 + 状态回写”模式
```

不直接采用原因：

```text
当前核心不是写代码 PR
广告项目更需要 human-in-loop 和客户可见性控制
```

### 39.5 OpenAI Agents SDK 可借鉴

官方能力：

```text
agents
tools
handoffs
guardrails
sessions
tracing
run hooks
```

适合本项目的未来 adapter：

```text
Creative Council 多角色 handoff
Review Council guardrails
Agent Run tracing
structured output
tool-level guardrails
```

不作为 v1 核心原因：

```text
SDK 解决 agent runtime
不解决项目控制面、reference evidence、asset manifest、PPT slot
```

### 39.6 Pullfrog / Optio / Fusion / Weave / HerdOS / Orca 观察

共同方向：

```text
coding agents 正在从“单个终端会话”走向“任务队列 + dashboard + isolated run + review gate”
```

可借鉴：

```text
dashboard-first
worktree/session isolation
review gate
auto-retry
agent status
human only pulled in for judgment
```

暂不直接采用原因：

```text
多数偏软件工程任务
广告创意的特殊对象更复杂：reference、video timecode、image slot、client visibility、PPT editability
```

### 39.7 最优路线修正

当前最佳路线不是：

```text
直接用 Symphony / AO / CAO / Agents SDK
```

而是：

```text
先做 ACO Local Control Plane
再预留 adapter
```

ACO = Ad Creative Orchestrator。

### 39.8 ACO Local Control Plane v0

核心对象：

```text
Workflow Policy
Work Item
Agent Profile
Agent Run
Event Log
Gate Report
Review Packet
Status Surface
```

最小文件：

```text
AD-creative/orchestrator/WORKFLOW.md
AD-creative/orchestrator/events.jsonl
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/agent_profiles.md
AD-creative/orchestrator/agent_runs.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

调度原语：

```text
handoff
assign
send_message
cancel
retry
reconcile
```

run_mode：

```text
interactive
subagent_sync
subagent_async
prompt_only
image_gen
external_search
ppt_adapter
manual_user
manual_client
```

### 39.9 为什么这比继续抽象更好

因为它能验证真正的问题：

```text
控制面是否能承载广告项目
agent 是否能靠文件交接
阻塞是否可见
状态是否可恢复
客户稿安全是否能通过 gate 控制
```

这比纸面 dry run 有意义。

### 39.10 当前推荐

下一步做：

```text
Orchestration Prototype v0
```

不是完整系统，只建最小控制面样例。

用 Moncler 填真实样例状态：

```text
W-MON-001 Intake done
W-MON-002 Official Reference Search waiting_user
W-MON-003 Proposal Architecture ready
W-MON-004 Image Job Spec blocked_by_reference
W-MON-005 SlideSpec Draft ready
W-MON-006 QA todo
```

成功标准：

```text
你只看 项目看板.md 就知道项目卡在哪
我只看 work_items.csv 就知道该派哪个 agent
agent 只看 work item + profile 就知道该产出什么
Gate 只看 artifacts + contract 就能判断能否进入下一阶段
```

## 38. Control Surface UI 规划

独立规划文件：

```text
docs/design/control_surface_ui_plan.md
```

研究对象：

```text
Linear
Multica
Paperclip
Symphony
```

结论：

```text
我们的控制面应是广告创意项目的本地 Agent Control Surface。
它借鉴 Linear 的任务状态和筛选，Multica 的人/agent 协作，Paperclip 的 agent control plane，Symphony 的 work item / run / review packet。
但不能照搬任何一个。
```

核心 UI：

```text
左侧导航：Project / Timeline / Work Board / References / Visual Assets / SlideSpec / Gates / Delivery / Skills
顶部状态：项目、阶段、Gate、客户可见性、下一决策
中央看板：Ready / Running / Blocked / Review / Done
右侧检查器：需求、参考、资产、slot、agent run、Gate、下一步
底部决策抽屉：待用户/客户/导演确认
```

广告创意专属字段：

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

这使它不是普通 Linear clone，而是：

```text
Linear-like task board
+ creative timeline
+ reference evidence
+ visual asset board
+ slide/slot control
+ gate QA
+ decision queue
```

当前已准备一版 image_gen UI 预览 prompt，用于生成 16:9 桌面控制面概念图。

## 39. 开源编排方案二次调研

独立调研文件：

```text
docs/design/orchestration_alternatives_research.md
```

研究对象：

```text
OpenAI Symphony
AWS CLI Agent Orchestrator
LangChain OpenSWE
Composio Agent Orchestrator
LangGraph
OpenAI Agents SDK
OpenHands
CrewAI / AutoGen
```

结论：

```text
不要直接选一个框架替代当前设计。
广告创意项目的核心不是 PR，而是 brief、客户反馈、导演反馈、参考证据、视觉资产、SlideSpec、PPT Gate。
更好的路线是 Adapter-ready Local Control Plane。
```

吸收机制：

```text
Symphony：任务状态机、WORKFLOW.md、reconciliation、per-work-item workspace
CAO：handoff / assign / send_message 操作语义
OpenSWE：async run、sandbox、mid-run feedback、middleware
LangGraph：checkpoint、interrupt、resume
OpenAI Agents SDK：handoff、guardrails、tracing adapter
OpenHands：workspace/session UI 体验
```

本项目第一版仍然先用：

```text
events.jsonl
work_items.csv
agent_runs.csv
gate_log.csv
artifact_index.csv
项目看板.md
待你确认.md
```

后续再接：

```text
Linear / Symphony
Codex subagents / Agents SDK / LangGraph / CAO
Paperclip-style control plane
Slack / 飞书 / Linear comment
```

新增稳定操作语义：

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

近期验证建议：

```text
用 Moncler 做 Orchestration Prototype v0。
不验证创意质量，验证控制面是否能承载真实项目变化。
重点测一次客户反馈变更后，需求时间线、work item、artifact、Gate 是否正确更新和 supersede。
```

## 40. Control Surface UI v2 修正

用户反馈：

```text
上一版 UI 太丑。
需要研究 Linear 实际 UI，而不是做普通企业后台。
```

已更新文件：

```text
docs/design/control_surface_ui_plan.md
```

核心修正：

```text
默认第一屏从 Kanban 改为 Grouped Issue List。
看板保留为第二视图。
顶部使用 breadcrumb / tabs / filter / display。
右侧使用 Linear-like inspector drawer。
底部决策区改为 slim decision rail。
状态、Gate、visibility、asset slot 改为小 chip / icon / count。
左侧导航改成 compact workspace sidebar。
```

新方向：

```text
Linear-like density
+ advertising creative artifact binding
+ reference / asset / SlideSpec / Gate evidence chain
```

禁止方向：

```text
大卡片看板
巨型审批横幅
上传表单堆叠
普通 SaaS dashboard
Microsoft Teams 风格
假图表
装饰性渐变
```

## 41. Visual Review Gate 设计

独立设计文件：

```text
docs/design/visual_review_workflow.md
```

核心判断：

```text
控制面只显示视觉审核状态和入口。
真正的视觉审核是独立 Gate。
```

视觉审核不是只看图片好不好看，而是检查：

```text
brief fit
brand visual DNA
creative fit
reference trace
asset slot binding
image generation record
client visibility
PPT / HTML usage
fake logo / fake text / fake packaging risk
composition / crop / resolution
story / copy / deck consistency
```

两层审核：

```text
Hard QA：假 logo、假包装字、内部注释、contact sheet、低质拼贴、无来源、不可客户可见等直接 BLOCKED

Creative Visual Review：品牌感、创意支撑、客户可感知价值、主视觉强度、是否需要补参考或重生图
```

审核角色：

```text
Visual Director
Brand Reviewer
Creative Reviewer
Production Reviewer
Client-Side Risk Reviewer
PPT Design Reviewer
```

产物：

```text
visual_review_report.md
visual_review_matrix.csv
asset_decisions.csv
revision_image_jobs.md
client_visible_flags.csv
```

控制面呈现：

```text
Work row：Visual Gate chip
Right inspector：Assets / Gate / Run
Asset board：图像网格 + 审核状态
Gate view：完整视觉审核报告
Decision rail：只显示需要用户确认的问题
```

必须问用户：

```text
主视觉方向取舍
人物/产品/场景资产锁定
客户可见图是否允许 AI 生成
是否接受某张图作为 PPT 主视觉参考
高风险但可用的图是否保留
```

## 42. Codex-first 架构修正

问题：

```text
原始目标是在 Codex 里做广告创意多智能体编排。
最近讨论偏向控制面 UI，容易把项目误导成一个 dashboard 产品。
```

修正判断：

```text
控制面不是核心产品。
控制面只是 Codex 编排状态的可视化视图。
```

真正核心：

```text
Codex-native Creative Orchestration Skill
+ project file source of truth
+ stage router
+ work item contract
+ agent handoff packet
+ gate report
+ asset / reference / SlideSpec trace
+ skill mining loop
```

第一优先级：

```text
在 Codex 会话内可运行
主控 Agent 能读项目状态
专项 Agent 能按 work item 执行
用户只看项目看板和待确认
每一步有产物和 Gate
```

控制面定位：

```text
v0：Markdown 项目看板
v1：本地 CLI status / gate / propose-skill
v2：可选 UI Control Surface
```

因此当前架构顺序应改为：

```text
1. Codex Skill / Workflow Contract
2. Project Folder Protocol
3. Work Item / Handoff / Gate Schema
4. Moncler dry-run as file protocol validation
5. CLI helper
6. UI control surface
```

不应反过来：

```text
先做 UI
再让 Codex 适配 UI
```

结论：

```text
UI 只保留为 future view。
当前继续设计 Codex 内部怎么跑。
```

## 43. Office-hours 架构判断

独立判断文件：

```text
docs/design/codex_first_architecture_office_hours.md
```

最终建议：

```text
Codex-native Skill
+ Project File Protocol
+ Optional Control Views
```

核心分层：

```text
Layer 1：Codex Skill，负责思考和执行
Layer 2：Project File Protocol，负责记忆和交接
Layer 3：Human-facing Files，负责给用户看
Layer 4：Optional Control Views，负责可视化
```

路线判断：

```text
纯 Codex：最快，但长项目会乱
控制面板优先：直观，但会把项目带偏
LangGraph / Agents SDK first：工程化强，但现在过重
Codex Skill + File Protocol：当前最佳
```

当前主线：

```text
把广告创意方法变成 Codex 能稳定执行、可保存、可复用、可审核、可沉淀 Skill 的工作流。
```

下一步不应继续画 UI，而应锁：

```text
Codex Skill 入口命令
Project File Protocol
Work Item Contract
Agent Handoff Packet
Gate Report Contract
Human-facing folder structure
Moncler 非 UI 验证流程
```

## 44. Project File Protocol + Skill 入口

独立设计文件：

```text
docs/design/project_file_protocol_and_skill_entries.md
```

当前锁定方向：

```text
少数用户入口
+ 项目文件事实源
+ 内部阶段路由
+ 明确 handoff / gate / version
```

用户入口先压到 6 个：

```text
ad-creative:start
ad-creative:add-materials
ad-creative:next
ad-creative:status
ad-creative:gate
ad-creative:mine-skill
```

内部阶段由 `ad-creative:next` 路由：

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

事实源文件：

```text
source_events.csv
current_truth.md
requirements.csv
gaps.csv
decisions.csv
resolutions.csv
work_items.csv
agent_runs.csv
artifact_index.csv
version_map.csv
gate_log.csv
events.jsonl
```

给用户看的入口：

```text
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/本轮交付说明.md
AD-creative/handoff/客户追问话术.md
AD-creative/handoff/下一步建议.md
```

第一轮不做 UI。

先验证：

```text
不复制长 prompt，也能继续下一步
新增客户反馈后，旧版本不会污染新版本
每个视觉资产能追溯到 requirement / reference / slot / Gate
```
