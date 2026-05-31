# Real Project Acceptance Criteria

状态：真实项目能力验收标准

## 目标

下次收到真实客户需求时，本项目必须能支撑：

```text
客户资料进入
→ Intake / 缺口判断
→ 搜索计划
→ Reference Pack
→ 创意方向
→ 方案结构
→ 视觉资产规划
→ image_gen / 图片参考使用
→ 视觉审核
→ 客户可审包
→ PPT / 交付 Gate
→ 客户反馈合并
→ Skill 沉淀
```

## 真实项目完成标准

### 1. Intake 成立

必须产出：

```text
source_events.csv
current_truth.md
requirements.csv
gaps.csv
客户追问话术.md
项目看板.md
待你确认.md
```

通过标准：

```text
能区分首次资料、补充、变更、反馈、导演组意见。
能识别缺口影响等级。
能告诉用户先问客户什么。
不直接开始创意生产。
```

### 2. Search 成立

必须产出：

```text
search_plan.md
reference_cards.csv
reference_shortlist.md
do_not_copy.md
research_gate_report.md
```

通过标准：

```text
每条搜索都绑定 gap / requirement。
每条参考都标 source、role、why relevant、borrow、do_not_copy、client_visible。
搜索目标不能标记客户可见。
搜索计划必须说明 why / scope / platform / expected output / do_not_copy。
不能把 UGC 或非官方内容冒充官方证据。
```

### 3. Creative 成立

必须产出：

```text
creative_directions.md
option_matrix.csv
message_line_candidates.md
proposal_structure.md
creative_gate_report.md
```

通过标准：

```text
方向数量符合客户或用户要求。
每个方向有主张、逻辑、关键画面、产品露出方法、参考支撑。
废弃文案不会回流到客户稿。
```

### 4. Visual 成立

必须产出：

```text
visual_asset_slots.csv
image_job_specs/
asset_manifest.csv
imagegen_import_log.md
visual_review_report.md
visual_review_matrix.csv
```

通过标准：

```text
每个视觉资产绑定 requirement / reference / slot / use case。
image_gen 不能用一句模糊话直接生成客户稿。
生成图必须从 generated_images 复制进 AD-creative/visual_assets 后才能被项目引用。
视觉质量 Gate 必须拦截缺文件、低分辨率、缺 prompt trace、未批准客户可见 AI 图。
人物、产品、场景、主视觉方向未锁前不能批量生成。
AI 图客户可见性必须明确。
```

### 5. Client Review Pack 成立

必须产出：

```text
client_review_outline.md
slide_spec.md 或 slide_spec.json
client_visibility_gate_report.md
```

通过标准：

```text
客户稿不含内部注释。
不含假 logo、假包装字、假案例。
不含 contact sheet。
低质拼贴图不能进入客户稿。
所有客户可见图有 asset_manifest 和 Gate 记录。
```

### 6. PPT / Delivery 成立

必须产出：

```text
ppt_plan.md
ppt_editability_check.md
delivery_note.md
final_gate_report.md
```

通过标准：

```text
PPT 可编辑性有检查。
HTML / SlideSpec / PPT 的内容一致。
如果有不可编辑图片页，必须明确说明用途和原因。
最终交付能追溯版本和来源。
```

### 7. Feedback Merge 成立

必须产出：

```text
feedback_map.csv
revised_current_truth.md
affected_artifacts.md
next_version_plan.md
```

通过标准：

```text
客户变更能覆盖旧需求。
补充需求不会误删旧需求。
导演组意见不会自动覆盖客户需求。
旧版本不被覆盖，只被 supersede。
```

### 8. Skill Mining 成立

必须产出：

```text
skill_opportunities.csv
AD-creative/skill_drafts/<skill-slug>/SKILL.md
AD-creative/skill_drafts/<skill-slug>/evidence.md
AD-creative/skill_drafts/<skill-slug>/install_request.md
```

通过标准：

```text
只沉淀可重复通路。
不包含客户机密。
不包含一次性文案。
不自动安装到 ~/.codex/skills。
```

## 端到端验收

真实项目 Ready 的定义：

```text
用户给一批真实资料
非开发者能用 adco run 启动
能从本地资料抽取首批 requirements / gaps / current_truth
产出项目看板和待确认
产出只读操作台.html
操作台可搜索、可筛选、可切换 Work / Materials / Assets / Gates / Decisions
三方议会审核能给出 PASS / PARTIAL_PASS / BLOCKED
用户确认搜索后能产出 reference pack
能生成两到三个创意方向
能规划视觉资产和 image job
能跑视觉审核
能形成客户可审方案包
能合并一轮客户反馈
能指出可沉淀 Skill
能通过 handoff-readiness-gate 交给非开发广告创意者内部操作
```

## 当前阶段判定

当前已经具备：

```text
Intake
Deterministic Intake Extraction
Project File Protocol
Work Item / Handoff
Gate 基础
非开发者操作台
三方议会 readiness 审核
Reference Pack 结构
Search Quality Gate
Reference Pack Gate
Creative Package 结构
Visual Asset / image_gen 规格
ImageGen 输出入库命令
Visual Quality Gate
Visual Review Gate
Client Review / SlideSpec
PPT Gate 规划
Feedback Merge
Skill Mining
验证工具
全局 Skill 安装
非开发者交接 Gate
```

真实客户发送前仍需负责人执行：

```text
真实联网搜索结果人工抽样
真实 image_gen 审美判断
最终客户稿发送确认
```
