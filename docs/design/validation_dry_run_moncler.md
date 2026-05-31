# Moncler 最小闭环纸面演练

状态：设计验证 / Dry Run / 非客户稿 / 未执行真实搜索 / 未生图 / 未做 PPT

目的：用 Moncler 类视觉质感项目验证 `ad_creative_orchestrator_v1_draft.md` 的编排设计是否能指导真实项目。

## 1. 演练边界

本次不做：

```text
真实品牌研究
真实搜索
真实生图
真实 HTML
真实 PPT
客户可见稿
```

本次只验证：

```text
Intake 是否能拆清楚
Work Board 是否直观
Proposal Architecture 是否能动态选择模块
Reference Pack 是否能形成证据链
image_gen / Image 2 应如何被使用
SlideSpec / Slot 是否能承接后续 HTML/PPT
Gate 是否能提前发现问题
```

## 2. 输入假设

基于现有 Moncler 工作流上下文，假设收到一批客户资料：

```text
项目类型：Moncler 类高端品牌视觉提案
目标：做一套可客户审阅的广告创意/视觉方案
核心关注：品牌视觉质感、产品呈现、主视觉、mockup、BTS质感、KV延展
可能交付：HTML预览、可编辑PPT、主视觉参考、素材包、asset_manifest
当前阶段：早期视觉/方案方向搭建
客户决策：判断方向是否高级、是否像品牌、产品呈现是否成立
```

已知 Moncler 逻辑：

```text
需求锁定
品牌 / 产品 / 官方参考研究
创意系统锁定
master scene
prompt pack
生图资产包
raw / selected / rejected
asset_manifest.csv
QA Gate
可编辑 PPT
final handoff
```

## 3. Intake Gate 输出样例

### 3.1 一页行动简报

```text
本轮状态：
已进入早期视觉方案搭建阶段，重点不是完整分镜，而是先锁品牌视觉方向、主视觉系统和产品呈现方法。

关键判断：
Moncler 类项目更适合以 Brand Visual DNA / Master Scene / KV / Mockup / BTS / Product Detail 为主，而不是先做完整 storyboard。

必须你确认：
1. 本轮是先做视觉方向提案，还是直接进入客户可审 PPT？
2. 是否允许先搜索 Moncler 官方资料、官网、官方社媒、官方 campaign？
3. 本轮是否需要真实产品图，还是允许先用参考级产品形态做内部探索？

需要问客户：
1. 本轮客户最想判断：品牌感、产品露出、KV方向，还是成片执行？
2. 是否有指定产品/系列/季节/传播平台？
3. 是否允许使用官网/官方社媒作为参考来源？

建议搜索：
需要。搜索目标不是泛泛研究 Moncler，而是补齐品牌视觉代码、产品材质、官方 campaign、BTS/秀场/户外语境。

当前可推进：
1. 建立 Reference Search Plan
2. 建立 Proposal Architecture
3. 草拟 3 页 SlideSpec
4. 草拟 PPT 主视觉方案图的 Image Job Spec

主要风险：
1. 没有官方参考就容易生成“像奢侈品但不像 Moncler”的泛高级图
2. 没有产品边界就可能出现假包装、假 logo、错误产品形态
3. 过早做 storyboard 会浪费，当前更应先做 master visual / mockup / KV

Gate 状态：
PARTIAL_PASS
```

### 3.2 当前需求节点样例

```text
REQ-MON-001
source: existing context
need: 提案必须体现高端品牌视觉质感
status: inferred
priority: high

REQ-MON-002
source: existing context
need: 先建立 master scene，再派生 mockup / KV / BTS / asset pack
status: inferred
priority: high

REQ-MON-003
source: existing context
need: 客户稿不能出现假 logo、假包装字、低质拼贴、未登记图片
status: confirmed_by_workflow
priority: blocking

REQ-MON-004
source: missing client brief
need: 确认主推产品/系列/季节/平台
status: missing
priority: blocking_for_client_visible
```

### 3.3 缺口样例

```text
GAP-MON-001
gap: 缺客户指定产品/系列
impact: blocking
action: 问客户；同时可先做内部视觉探索，但不得进入客户稿

GAP-MON-002
gap: 缺官方参考来源
impact: high_impact
action: 生成搜索计划，待用户确认后搜索

GAP-MON-003
gap: 缺本轮方案深度判断
impact: high_impact
action: Proposal Architecture 先判断是否需要 moodboard / mockup / KV / BTS / storyboard

GAP-MON-004
gap: 缺真实 logo / 产品图片授权边界
impact: blocking_for_delivery
action: 问客户或只用官方来源标注为参考
```

## 4. Stage Router 判断

当前阶段：

```text
S0 Intake → S1 Reference Research → S4 Proposal Architecture
```

暂不进入：

```text
S2 Creative Council 深创意发散：需要官方参考后再做
S5 Visual Asset OS 正式生图：需要先确认参考和资产意图
S7 PPT Bridge：没有 locked SlideSpec
```

允许创建的 work items：

```text
Reference Search Plan
Proposal Architecture Draft
PPT主视觉方案图 Image Job Spec Draft
3页 SlideSpec Draft
Gate Review
```

## 5. Work Board 示例

```text
W-MON-001
title: 解析 Moncler 输入资料并生成 Intake 简报
work_type: intake
stage: S0
state: done
owner_agent: Intake Analyst
expected_outputs: intake_brief, requirements, gaps, questions
gate_required: Brief Gate
human_review_required: yes
run_mode: interactive

W-MON-002
title: 生成 Moncler 官方/视觉/产品 Reference Search Plan
work_type: research
stage: S1
state: waiting_user
owner_agent: Reference Researcher
depends_on: W-MON-001
expected_outputs: search_plan
gate_required: Search Plan Gate
human_review_required: yes
run_mode: external_search

W-MON-003
title: 设计本轮 Moncler 方案结构
work_type: proposal_architecture
stage: S4
state: ready
owner_agent: Proposal Architect
depends_on: W-MON-001
expected_outputs: proposal_structure, module_depth_plan
gate_required: Proposal Architecture Gate
human_review_required: yes
run_mode: interactive

W-MON-004
title: 草拟 PPT 主视觉方案图 Image Job Spec
work_type: image_job
stage: S5
state: blocked
owner_agent: Visual Director + Image Producer
depends_on: W-MON-002,W-MON-003
blocked_by: 缺参考确认 / 缺产品边界
expected_outputs: image_job_specs
gate_required: Image Brief Gate
human_review_required: yes
run_mode: prompt_only

W-MON-005
title: 草拟 3 页 SlideSpec
work_type: slide_spec
stage: S6
state: ready
owner_agent: Slide Architect
depends_on: W-MON-003
expected_outputs: slide_spec_3_pages, slot_contract
gate_required: SlideSpec Gate
human_review_required: yes
run_mode: prompt_only

W-MON-006
title: Reference / Proposal / Slot / SlideSpec Gate
work_type: qa_review
stage: Gate
state: todo
owner_agent: QA Council
depends_on: W-MON-002,W-MON-003,W-MON-004,W-MON-005
expected_outputs: gate_report
gate_required: no
human_review_required: yes
run_mode: interactive
```

## 6. Reference Search Plan 示例

本演练不执行搜索，只定义搜索计划。

```text
search_id: SEARCH-MON-001
trigger_stage: Intake
search_goal: 建立 Moncler 品牌视觉代码和官方 campaign 参考
linked_gap: GAP-MON-002
linked_requirement: REQ-MON-001, REQ-MON-002
linked_decision: 判断本轮方案是否以 KV / mockup / BTS 为主
platforms:
- Moncler official site
- Moncler official Instagram / YouTube
- campaign archive
- Vogue / Hypebeast / fashion media
- Behance / Pinterest only as visual style secondary reference
keywords:
- Moncler campaign
- Moncler Grenoble campaign
- Moncler Genius campaign
- Moncler product detail
- Moncler outdoor luxury visual
expected_outputs:
- Brand Visual DNA cards
- Product Material cards
- KV / Campaign references
- BTS / texture references
- Reference Pack shortlist
client_visibility: pending
stop_condition: 至少有 6 条可用官方/可信来源参考，其中 2 条可支撑 KV，2 条可支撑 product/detail，1 条可支撑 BTS，1 条可支撑 brand world
```

## 7. Reference Card 示例

注意：以下为字段样例，不是真实搜索结果。

```text
reference_id: REF-MON-001
type: campaign
source_platform: Moncler official site
source_url: 待真实搜索确认
source_owner: Moncler
linked_requirement: REQ-MON-001
linked_module: Brand Visual DNA
client_decision_supported: 判断方案是否符合品牌视觉语境
why_it_matters: 用于确认 Moncler 官方视觉中的光线、空间、人物姿态和产品气质
what_to_borrow: 克制构图、材质质感、空间冷感、产品中心性
what_not_to_copy: 不复制具体模特、场景、品牌构图、logo使用
client_visibility: pending
rights_note: 仅作参考；客户稿需标来源或改为内部参考
quality_score: pending
status: candidate
```

```text
reference_id: REF-MON-002
type: product_page
source_platform: Moncler official e-commerce / official product page
source_url: 待真实搜索确认
source_owner: Moncler
linked_requirement: REQ-MON-004
linked_module: Product Moment / Mockup
client_decision_supported: 判断产品外观、材质、细节露出是否准确
why_it_matters: 避免 image_gen 生成错误产品结构或假包装字
what_to_borrow: 材质、廓形、细节、产品比例
what_not_to_copy: 不复制页面 UI，不生成假价格/假文案
client_visibility: pending
rights_note: 真实客户稿需确认授权或标参考
quality_score: pending
status: candidate
```

```text
reference_id: REF-MON-003
type: video
source_platform: YouTube / official video / Vimeo
source_url: 待真实搜索确认
timecode_start: 待真实搜索确认
timecode_end: 待真实搜索确认
linked_module: BTS / Shooting Approach
client_decision_supported: 判断拍摄质感和镜头运动是否适合本轮方案
why_it_matters: 客户看 Moncler 类项目时通常需要相信“能拍出这个质感”
what_to_borrow: 镜头节奏、材质近景、环境氛围、人物状态
what_not_to_copy: 不复制具体片段、人物、文案、音乐
client_visibility: pending
status: candidate
```

## 8. Proposal Architecture 示例

### 8.1 本轮方案目标

```text
让用户/客户判断 Moncler 视觉方向是否成立，重点看品牌感、主视觉、产品呈现和可执行质感。
```

### 8.2 推荐方案结构

```text
P1 Cover / Master Visual Direction
P2 Brand Visual DNA + Product Role
P3 Reference Pack / KV + Mockup + BTS 支撑
```

如果扩展成完整方案，后续模块：

```text
P4 Master Scene Matrix
P5 KV Direction
P6 Product Detail / Mockup
P7 BTS / Shooting Texture
P8 Asset Plan
P9 Platform Crops
P10 QA / Delivery Notes
```

### 8.3 暂时不做

```text
完整 storyboard：当前客户未必需要，且缺产品/场景锁定
30秒故事线：Moncler 类项目当前更偏视觉系统而非剧情
客户可见精修图：缺真实产品/授权边界
最终 PPTX：没有 locked SlideSpec 和 selected assets
```

### 8.4 模块深度

```text
Brand Visual DNA: L2 文字 + 官方参考
Master Visual Direction: L3 文字 + 参考 + image_gen 设计参考草图
KV Direction: L3
Mockup: L3/L4，取决于是否有真实产品图
BTS / Shooting Texture: L2 参考视频 + 时间码
Storyboard: 暂不做
```

## 9. Image Use Router 示例

### 9.1 使用判断

```text
PPT主视觉方案图：使用 image_gen / Image 2
Mockup探索：使用 image_gen / Image 2，但需要官方产品参考
Product close-up：没有真实产品图前只做 internal exploration
BTS质感图：可用 image_gen 做氛围草图，但客户稿优先真实视频参考
完整分镜：暂不生成
```

### 9.2 Image Job Spec 草案

```text
job_id: IMGJOB-MON-001
job_type: ppt_design_reference
linked_slot_id: SLOT-MON-001
linked_requirement: REQ-MON-001
linked_direction: Master Visual Direction
asset_type: ppt_design_reference
asset_role: hero
primary_request: 为 Moncler 类高端户外奢侈品牌提案生成一张16:9主视觉设计参考图，强调克制、高级、冷感空间、产品中心性和可用于PPT封面的视觉结构。
input_references:
- reference_id: REF-MON-001
  role: brand_reference
  use: 参考品牌视觉气质、构图、材质，不复制具体画面
  do_not_copy: true
visual_locks:
  character: 暂不锁定具体人物
  product: 使用无具体logo的羽绒服/外套产品形态作为内部探索，不生成假logo
  environment: 冷感山地/雪境/现代户外空间，待官方参考确认
  style: 高端品牌大片、克制留白、材质清晰
composition: 16:9，中心主视觉，左侧或上方预留PPT标题区域
lighting_mood: 冷白自然光，低饱和，高质感，不廉价电商感
color_palette: 冷白、深黑、岩灰、少量高光
materials_textures: 防水面料、羽绒体积、雪、岩石、金属细节
text_verbatim: none
constraints:
- 不出现真实或假 Moncler logo
- 不生成假包装字
- 不出现水印
- 不出现内部注释
- 仅供内部设计参考，客户可见前需QA
client_visibility: internal
qa_checklist:
- 是否像高端品牌大片
- 是否适合PPT封面结构
- 是否没有假logo/假字
- 是否可派生成KV/Mockup/BTS方向
```

```text
job_id: IMGJOB-MON-002
job_type: mockup
linked_slot_id: SLOT-MON-003
linked_requirement: REQ-MON-004
asset_type: mockup
asset_role: product_reference
primary_request: 生成一张产品穿着/展示 mockup 草图，用于探索高端外套在雪境或冷感建筑空间中的产品呈现方式。
input_references:
- reference_id: REF-MON-002
  role: product_reference
  use: 参考真实产品轮廓和材质
  do_not_copy: false
visual_locks:
  product: 待真实产品图确认前，只能做内部草图
constraints:
- 无logo
- 无假标签文字
- 不进入客户稿
client_visibility: internal
```

## 10. Slot Contract 示例

```text
slot_id: SLOT-MON-001
slide_id: SLIDE-MON-001
module_type: cover
purpose: 封面主视觉 / PPT主视觉方向
linked_requirement: REQ-MON-001
linked_direction: Master Visual Direction
needed_asset_type: ppt_design_reference
visual_role: hero
ratio: 16:9
size_hint: full bleed background with safe title area
reference_ids: REF-MON-001
asset_lock_id: pending
prompt_job_id: IMGJOB-MON-001
selected_asset_id: pending
client_visibility: internal_until_qa
qa_status: pending
status: waiting_generation
```

```text
slot_id: SLOT-MON-002
slide_id: SLIDE-MON-002
module_type: brand_visual_dna
purpose: 展示官方参考缩略图和视觉代码
linked_requirement: REQ-MON-001
needed_asset_type: reference_thumbnail
visual_role: evidence
reference_ids: REF-MON-001
client_visibility: pending
qa_status: pending
status: waiting_reference
```

```text
slot_id: SLOT-MON-003
slide_id: SLIDE-MON-003
module_type: mockup_bts_reference
purpose: 展示 mockup / BTS / product detail 的参考支撑
linked_requirement: REQ-MON-002, REQ-MON-004
needed_asset_type: mockup / video_frame / product_closeup
visual_role: evidence
reference_ids: REF-MON-002, REF-MON-003
client_visibility: pending
qa_status: pending
status: waiting_reference
```

## 11. 3页 SlideSpec 示例

### 11.1 Slide 1

```text
slide_id: SLIDE-MON-001
page_no: 1
module_type: cover
claim: Moncler 的提案应先建立可延展的高端户外主视觉系统
purpose: 让客户快速感知整体审美方向
linked_requirements: REQ-MON-001, REQ-MON-002
layout_type: full_bleed_hero_with_title
content_blocks:
- title: Moncler Visual Direction
- subtitle: Master scene / KV / product texture exploration
image_slots:
- SLOT-MON-001
reference_blocks: none
client_visibility: internal_preview
status: draft
```

### 11.2 Slide 2

```text
slide_id: SLIDE-MON-002
page_no: 2
module_type: brand_visual_dna
claim: 本轮视觉判断应绑定官方视觉代码，而不是泛化“高级感”
purpose: 说明为什么需要官方参考和品牌视觉拆解
linked_requirements: REQ-MON-001
layout_type: split_reference_and_insight
content_blocks:
- title: Brand Visual DNA
- body: 从官方 campaign、产品图和视频参考中拆解空间、光线、材质和产品呈现方法。
- label: Borrow / Do Not Copy
image_slots:
- SLOT-MON-002
reference_blocks:
- REF-MON-001
client_visibility: pending_reference_qa
status: draft
```

### 11.3 Slide 3

```text
slide_id: SLIDE-MON-003
page_no: 3
module_type: reference_pack
claim: Moncler 类项目当前应优先验证 KV、Mockup 与 BTS 质感，而不是完整分镜
purpose: 帮客户判断本轮方案模块和制作深度
linked_requirements: REQ-MON-002, REQ-MON-004
layout_type: three_column_evidence
content_blocks:
- title: What We Need To Prove First
- column_1: KV / Master Scene
- column_2: Product / Mockup
- column_3: BTS / Shooting Texture
image_slots:
- SLOT-MON-003
reference_blocks:
- REF-MON-001
- REF-MON-002
- REF-MON-003
client_visibility: internal_preview
status: draft
```

## 12. Gate Report 示例

```text
gate_id: GATE-MON-DRYRUN-001
stage: Minimum Validation Chain
status: PARTIAL_PASS
score: 3.7
decision: 带修改进入下一轮设计验证

blocking_issues:
- 缺客户指定产品/系列，不能生成客户可见 mockup 或 product detail
- 缺真实官方参考，Reference Pack 目前只能是搜索计划和字段样例

revision_items:
- 增加 Official Reference Search Plan 的 stop condition
- 在 Proposal Architecture 中明确暂不做完整 storyboard 的理由
- 在 Image Job Spec 中明确 internal / client_visible 分界
- 在 SlideSpec 中保留 notes_internal，但禁止进入客户可见层

questions_for_user:
- 是否允许下一步对 Moncler 做真实官方/公开视频/视觉参考搜索？
- 本次 Moncler 验证更像品牌视觉提案，还是产品 campaign 方向提案？

questions_for_client:
- 本轮客户最想判断品牌感、产品露出、KV方向，还是执行拍法？
- 是否有指定产品/系列/季节？
- 是否允许官方公开素材进入参考页？

search_needed:
- search_goal: 补齐官方视觉代码、产品形态、KV/BTS参考
  platforms: Moncler official site, official social/video, campaign archive, fashion media
  linked_gap: GAP-MON-002
  expected_decision: 判断 Reference Pack 是否足够支撑 Proposal Architecture

affected_artifacts:
- reference_pack
- proposal_structure
- image_job_specs
- slot_manifest
- slide_spec

next_state: Reference Research, pending user search confirmation
owner: Main Controller
```

## 13. 演练发现的问题

### 13.1 当前设计有效点

```text
1. Work Board 比单纯阶段流程更直观
2. Proposal Architecture 能避免过早做 storyboard
3. Reference Pack 字段能防止素材堆
4. Image Job Spec 能把 image_gen 使用限制在正确边界内
5. Slot Contract 能提前承接 PPT/HTML 结构
6. Gate 能提前发现客户稿风险
```

### 13.2 需要回改主草案的问题

```text
1. Proposal Architecture 应增加“项目类型默认模块模板”，如 Moncler 类 / TVC 类 / 社媒种草类
2. Image Use Router 应明确：Moncler 类项目中，PPT主视觉设计参考优先于 storyboard
3. Reference Gate 应增加 stop condition，避免搜索无限扩张
4. SlideSpec 示例应区分 internal_preview / client_review / final_delivery
5. Work Board 应明确 waiting_user 与 waiting_client 的区别
```

### 13.3 设计风险

```text
1. 如果没有真实搜索，Moncler 方向容易泛化为“高端雪景大片”
2. 如果没有产品素材，mockup 容易生成错误产品
3. 如果 PPT 主视觉图太强，客户可能误以为是最终 KV
4. 如果 reference 不标“借鉴/不复制”，会有误导风险
```

## 14. 结论

Moncler dry run 说明当前 v1 设计可以指导真实项目的早期方案搭建。

但下一步必须补强：

```text
项目类型默认模块模板
Reference Search stop condition
Image Use Router 的项目类型规则
Work Board 状态细化
SlideSpec 可见性状态
```

建议下一步：

```text
把本次 dry run 的发现回写到主草案
```
