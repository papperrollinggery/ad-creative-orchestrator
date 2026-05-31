# 双泳道 Goal 交付工作流

状态：可执行工作流 / goal 模式专用

依据来源：
- `README.md`
- `docs/operating/operating_manual.md`
- `docs/operating/real_project_acceptance_criteria.md`
- `docs/operating/first_real_project_runbook.md`
- `docs/design/ad_creative_orchestrator_v1_draft.md`
- `docs/design/visual_review_workflow.md`
- `templates/project/AD-creative/image_jobs/image_generation_policy.md`
- `templates/project/AD-creative/gates/gate_report_template.md`

## 1. 归一化定义

品牌深度研究：围绕客户资料、品牌事实、官方/可信参考、竞品与平台语境，形成 `current_truth`、`requirements`、`gaps`、`search_plan`、`reference_cards`、`visual_dna_notes`、`creative_directions`，只使用可追溯证据，不把未经确认的信息写成事实。

图片功能：围绕视觉资产、图片参考、image_gen、资产槽位、导入记录、质量审核、客户可见性，形成 `visual_asset_slots`、`image_job_spec`、`image_prompt_pack`、`asset_manifest`、`visual_review_report`、`client_visible_flags`，所有客户可见图片必须经过 Gate。

统一阶段树：两条泳道共享同一项目状态机、同一 Gate、同一风险复盘；任一泳道可独立运行，但进入客户可见物或下游交付时必须串联。

耐久状态：
- `AD-creative/orchestrator/current_truth.md`
- `AD-creative/orchestrator/requirements.csv`
- `AD-creative/orchestrator/gaps.csv`
- `AD-creative/orchestrator/work_items.csv`
- `AD-creative/orchestrator/work_dependencies.csv`
- `AD-creative/orchestrator/decisions.csv`
- `AD-creative/orchestrator/resolutions.csv`
- `AD-creative/orchestrator/gate_log.csv`
- `AD-creative/orchestrator/artifact_index.csv`
- `AD-creative/handoff/项目看板.md`
- `AD-creative/handoff/待你确认.md`
- `AD-creative/gates/<gate_id>_report.md`

## 2. 全局阶段树

| 阶段 | 品牌深度研究泳道 | 图片功能泳道 | 共享门禁 | 下一阶段映射 |
|---|---|---|---|---|
| P0 Intake 与事实基线 | 解析资料、提取品牌事实、需求、缺口、冲突 | 登记现有图片/素材、识别视觉需求、标记未知授权 | Brief Gate + 反驳性议会 | P1；如 brief 边界不清则停在 `待你确认.md` |
| P1 研究计划与图片策略 | 输出搜索计划、来源范围、stop condition、品牌禁区假设 | 输出图片路线：不生图 / prompt-only / 探索 / 设计参考 / 客户可见候选 | Research Plan Gate + 反驳性议会 | P2；如搜索未获确认则只允许内部准备 |
| P2 证据包与资产槽位 | 建立 reference cards、shortlist、do_not_copy、visual DNA | 建立 asset slots、input image roles、manifest skeleton、visibility 初值 | Reference Pack Gate + Slot Gate + 反驳性议会 | P3；如参考不足则回 P1 扩搜 |
| P3 策略方向与图片任务 PRD | 输出创意方向、信息架构、文案候选、方案结构 | 输出 image job specs、prompt pack、尺寸/质量/visibility contract | Creative Gate + Image Job Gate + 反驳性议会 | P4；如方向未锁则不生客户稿图 |
| P4 内部原型与图片探索 | 形成内部 review narrative、slide module、证据说明 | 生成或导入 internal_only 图片、记录 prompt/import、做预 QA | Internal Prototype Gate + Visual QA 初检 + 反驳性议会 | P5；如图片不合格则重建 job spec |
| P5 视觉审核与客户审阅包 | 形成客户可读 story、claim、reference rationale、SlideSpec | 输出 visual review matrix、client_visible_flags、替换/重生图决议 | Visual Review Gate + Client Pack Gate + 反驳性议会 | P6；如客户可见风险存在则不得导出 |
| P6 PPT/最终交付 Gate | 输出 delivery note、版本说明、最终叙事追溯 | 确认 PPT slots 使用 approved assets，跑可编辑性检查 | PPT Gate + Final Gate + 反驳性议会 | P7；发送客户稿前停人工确认 |
| P7 反馈合并与复用沉淀 | 合并反馈、更新 current truth、supersede 旧版本 | 作废/重建受影响 asset/job，沉淀可复用图片链路 | Feedback Gate + Skill Mining Gate + 反驳性议会 | 下一轮 P0/P1/P3；按变更影响回退 |

## 3. 阶段核对表

| 阶段/泳道 | 独立输入 | 独立产出 | 依赖 | 退出条件 | 后置关系 |
|---|---|---|---|---|---|
| P0 品牌深度研究 | 客户资料、会议记录、导演意见、历史反馈 | `current_truth.md`、`requirements.csv`、`gaps.csv`、客户追问 | 原始资料已登记到 `source_events.csv` | 无 blocking gap 被伪装成已确认事实；追问清单已写入 handoff | P1 品牌研究计划 |
| P0 图片功能 | 客户素材、现有图片、参考链接、未知来源图片 | 初始 asset list、视觉需求清单、授权未知项 | P0 品牌事实基线 | 所有图片只标 internal/unknown，不升级 client_visible | P1 图片策略 |
| P1 品牌深度研究 | P0 缺口、需求、客户追问 | `search_plan.md`、平台/来源范围、stop condition | Brief Gate 未 BLOCKED | 每条搜索绑定 gap/requirement；搜索目标不直接客户可见 | P2 参考证据包 |
| P1 图片功能 | P0 视觉需求、图片素材状态 | image route decision、asset lock 前置清单 | 图片用途已绑定 requirement | 未锁人物/产品/场景前不得批量生成；客户可见图需后置确认 | P2 资产槽位 |
| P2 品牌深度研究 | 搜索计划、已确认可搜范围 | `reference_cards.csv`、`reference_shortlist.md`、`do_not_copy.md`、`visual_dna_notes.md` | 搜索确认或仅内部资料研究 | 参考具备 source/role/why/borrow/do_not_copy/client_visible | P3 策略方向 |
| P2 图片功能 | 图片路线、参考证据、视觉需求 | `visual_asset_slots.csv`、manifest skeleton、slot contract | 每个 slot 绑定 requirement/reference role | 每个 slot 有用途、可见性、尺寸/比例、风险 | P3 image job PRD |
| P3 品牌深度研究 | reference pack、requirements、visual DNA | `creative_directions.md`、`option_matrix.csv`、`message_line_candidates.md`、`proposal_structure.md` | Reference Gate 非 BLOCKED | 方向数量、证据、客户价值、非范围明确 | P4 内部原型 |
| P3 图片功能 | slot contract、方向、视觉策略 | `image_job_spec`、`image_prompt_pack`、生成/编辑约束 | 方向未锁只能 prompt-only 或少量探索 | 每个 image job 有 use_case、输入角色、avoid、output_contract | P4 图片探索 |
| P4 品牌深度研究 | 策略方向、文案、方案结构 | 内部 review narrative、slide module draft、证据说明 | Creative Gate 非 BLOCKED | 内部稿不含客户可见声明；客户待确认项已列出 | P5 客户审阅包 |
| P4 图片功能 | image job spec、素材、image_gen 输出 | 导入图片、`asset_manifest.csv`、import log、预 QA 结果 | 图片必须进项目资产目录后才能引用 | 低清、假 logo、未记录 prompt、未绑定 slot 全部 BLOCKED | P5 视觉审核 |
| P5 品牌深度研究 | 内部原型、视觉预 QA、参考证据 | `client_review_outline.md`、`slide_spec.md`、客户可读叙事 | Internal Gate 通过 | 客户稿无内部注释、TODO、假案例、无来源参考 | P6 PPT/Final |
| P5 图片功能 | asset manifest、visual review inputs | `visual_review_report.md`、`visual_review_matrix.csv`、`client_visible_flags.csv` | 图片 QA 初检通过 | 客户可见图 QA PASS 且有人工确认路径 | P6 PPT slots |
| P6 品牌深度研究 | SlideSpec、客户审阅包、交付范围 | `delivery_note.md`、final gate report、版本追溯 | Client Pack Gate 非 BLOCKED | 发送前人工确认已登记；最终文本可追溯 | P7 反馈/复盘 |
| P6 图片功能 | approved assets、PPT slot、SlideSpec | `ppt_editability_check.md`、最终 asset 使用记录 | PPT/HTML/SlideSpec 一致 | PPT 可编辑性 PASS；不可编辑页说明用途与原因 | P7 资产复盘 |
| P7 品牌深度研究 | 客户反馈、导演反馈、Gate 结果 | `feedback_map.csv`、`affected_artifacts.md`、`next_version_plan.md` | Final Gate 完成或反馈触发 | 旧需求只 supersede，不覆盖；下轮入口明确 | 回 P0/P1/P3 |
| P7 图片功能 | 反馈影响的 asset/job/slot | 作废/重建 job，更新 manifest，skill opportunity | 反馈影响范围已绑定 artifact | 受影响图片不再流入客户稿；可复用链路有 evidence | 回 P2/P3/P4 |

## 4. 每阶段 PRD

### PRD-P0 Intake 与事实基线

目标：把原始资料转成可执行事实基线，禁止直接进入创意或图片客户稿。

范围：资料登记、需求抽取、缺口判断、冲突标记、图片/素材初始登记、客户追问。

非范围：创意方向定稿、真实联网搜索执行、批量生图、客户稿发送。

关键里程碑：资料进入 `source_events.csv`；`current_truth.md` 更新；`requirements.csv` 与 `gaps.csv` 有记录；图片/素材风险进入 work item；Brief Gate 完成。

风险：客户资料缺失；导演意见覆盖客户需求；未知来源图片被误用；内部假设被写成事实。

验收标准：能区分首次资料/补充/变更/反馈/导演意见；blocking gap 不下游推进；图片默认 internal/unknown；`待你确认.md` 只列真实决策点。

测试清单：读取 handoff 是否能判断项目卡点；检查每条 requirement 有 source；检查 gaps 有影响等级；检查图片项无 client_visible 自动升级；运行 Brief Gate 与反驳性议会。

责任人：Main Controller、Intake Analyst、Operations Council。

预计时长：0.5-1 工作日。

依据来源/验收证据：`README.md` 当前目标；`real_project_acceptance_criteria.md` Intake 成立；`operating_manual.md` ad-creative:run/start/add-materials。

### PRD-P1 研究计划与图片策略

目标：把品牌研究和图片使用先规划成可停、可验、可回退的任务。

范围：搜索计划、平台/来源范围、stop condition、图片路线、asset lock 前置条件、客户可见性边界。

非范围：无计划扩搜；把搜索结果当客户稿；生客户可见 AI 图；未确认人物/产品/场景就批量生成。

关键里程碑：`search_plan.md` 有 linked_gap/linked_requirement；图片路线决议写入 decisions/resolutions；P1 Gate 完成。

风险：搜索无限扩张；UGC 冒充官方证据；图片功能过早进入生成；客户可见边界不清。

验收标准：每条搜索说明 why/scope/platform/expected output/do_not_copy/stop_condition；每条图片路线有 use_case、visibility、lock dependency；未获确认时只允许内部准备。

测试清单：抽查搜索目标无 client_visible；检查 stop condition 不为空；检查 image route 不越过 asset lock；运行 Research Plan Gate 与反驳性议会。

责任人：Reference Researcher、Visual Director、QA / Review Council。

预计时长：0.5 工作日。

依据来源/验收证据：`Search Plan Contract v1`；`Reference Gate Stop Condition`；`image_generation_policy.md` Required Order 与 Client Visibility。

### PRD-P2 证据包与资产槽位

目标：把品牌证据和图片槽位绑定，形成后续策略/生图/PPT 的共同底座。

范围：reference cards、shortlist、do_not_copy、visual DNA、asset slots、reference role、manifest skeleton、slot contract。

非范围：最终创意判断；客户可见图片批准；无来源参考进入客户稿；未绑定 requirement 的图片槽位。

关键里程碑：参考包字段完整；`visual_asset_slots.csv` 覆盖关键页面/画面；Reference Pack Gate 与 Slot Gate 完成。

风险：参考只像收集图集，不能支撑需求；图片槽位和 PPT/HTML 脱节；参考版权和 do_not_copy 缺失。

验收标准：每条参考有 source/role/why relevant/borrow/do_not_copy/client_visible；每个 slot 有 requirement/reference/use case/ratio/visibility；参考不足时回 P1。

测试清单：抽查 reference-to-requirement 链；抽查 slot-to-requirement 链；检查 `do_not_copy.md`；检查未授权参考不出现在 client_visible。

责任人：Reference Researcher、Slide Architect、Visual Director。

预计时长：1 工作日。

依据来源/验收证据：`real_project_acceptance_criteria.md` Search 与 Visual；`visual_review_workflow.md` Asset Trace Review。

### PRD-P3 策略方向与图片任务 PRD

目标：把品牌研究转成可审的策略方向，把图片功能转成可执行 image job PRD。

范围：创意方向、option matrix、文案候选、proposal structure、image job spec、prompt pack、输出规格。

非范围：用一句模糊提示词直接生成客户稿；未过 Creative Gate 就批量生产；不带 evidence 的策略主张。

关键里程碑：`creative_directions.md` 完成；`proposal_structure.md` 完成；image job specs 完成；Creative Gate 与 Image Job Gate 完成。

风险：策略方向和品牌证据断链；图片任务只追求好看不服务方案；方向未锁导致后续大面积返工。

验收标准：每个方向有主张、逻辑、关键画面、产品露出、参考支撑；每个 image job 有 use_case、asset_type、input roles、scene、subject、style、composition、lighting、constraints、avoid、output_contract。

测试清单：检查方向数量符合需求；检查每个 claim 有证据；检查 prompt pack 字段完整；检查客户可见候选仍为 pending；运行 Creative/Image Job Gate 与反驳性议会。

责任人：Creative Strategist、Copywriter、Proposal Architect、Image Producer。

预计时长：1-2 工作日。

依据来源/验收证据：`real_project_acceptance_criteria.md` Creative；`image_generation_policy.md` Prompt Format；`ad_creative_orchestrator_v1_draft.md` Image 2 使用策略。

### PRD-P4 内部原型与图片探索

目标：用最小内部原型验证策略与图片路线，不把探索材料误当客户稿。

范围：内部 review narrative、slide module draft、少量 internal_only 视觉探索、图片导入、asset_manifest、预 QA。

非范围：客户稿发送；客户可见 AI 图确认；大批量分镜生成；跳过 import 直接引用生成图。

关键里程碑：内部原型可读；图片已导入项目资产目录；`asset_manifest.csv` 更新；Visual QA 初检完成。

风险：探索图被客户误读为最终图；生成图缺 prompt trace；低清图进入方案；假 logo/不可控文字漏检。

验收标准：所有图片进入 `AD-creative/visual_assets/` 后再引用；生成/编辑记录可追溯；低清、假 logo、未绑定 slot、缺 prompt trace 均 BLOCKED；内部原型明确非客户稿。

测试清单：检查 manifest path 存在；检查 prompt/import log；检查 image slot 绑定；运行 visual-quality-gate；运行反驳性议会。

责任人：Image Producer、Visual Director、Production Reviewer。

预计时长：0.5-1.5 工作日。

依据来源/验收证据：`operating_manual.md` add-asset/import-imagegen/visual-quality-gate；`visual_review_workflow.md` 硬性 QA。

### PRD-P5 视觉审核与客户审阅包

目标：把内部方案转成客户可审包，所有客户可见图片和文本经过风险门禁。

范围：client review outline、SlideSpec、客户可读叙事、visual review report、matrix、client_visible_flags。

非范围：最终交付发送；未 QA PASS 的图片客户可见；contact sheet/内部注释/假案例进入客户稿。

关键里程碑：`client_review_outline.md` 完成；`slide_spec.md` 完成；Visual Review Gate 完成；Client Pack Gate 完成。

风险：客户稿包含内部注释；参考权利/来源不清；AI 图可见性未批准；PPT/HTML 结构无法承接图片。

验收标准：客户可见图都有 asset_manifest 与 Gate 记录；客户稿不含内部注释、假 logo、假包装字、假案例、低质拼贴；SlideSpec client_visibility 状态正确。

测试清单：检查客户可见文本无 TODO/TBD/internal；检查 client_visible_flags；检查 SlideSpec slot；运行 Visual Review Gate、Client Pack Gate、反驳性议会。

责任人：Slide Architect、QA / Review Council、Client-Side Risk Reviewer、PPT Design Reviewer。

预计时长：1 工作日。

依据来源/验收证据：`real_project_acceptance_criteria.md` Client Review Pack；`visual_review_workflow.md` Client Visibility Review。

### PRD-P6 PPT/最终交付 Gate

目标：把客户审阅包转成可交付版本，并在发送前留下最终风险结论。

范围：PPTX 导出/检查、delivery note、final gate report、版本追溯、发送前人工确认。

非范围：自动发送客户稿；自动确认 AI 图客户可见；覆盖旧版本；忽略不可编辑页说明。

关键里程碑：`ppt_editability_check.md` PASS；`delivery_note.md` 完成；Final Gate 完成；发送确认写入 `待你确认.md` 或 decisions。

风险：PPT 不可编辑；HTML/SlideSpec/PPT 不一致；客户可见图片未获批准；旧版本被覆盖。

验收标准：PPT 有可编辑文本层；HTML/SlideSpec/PPT 内容一致；最终交付能追溯版本和来源；发送前人工确认存在。

测试清单：运行 export-pptx/check-pptx；检查 final gate；检查 artifact version；检查不可编辑页说明；运行反驳性议会。

责任人：PPT Producer、Main Controller、QA / Review Council。

预计时长：0.5-1 工作日。

依据来源/验收证据：`operating_manual.md` export-pptx/check-pptx/client-pack-gate；`real_project_acceptance_criteria.md` PPT / Delivery。

### PRD-P7 反馈合并与复用沉淀

目标：吸收反馈、保护版本链、沉淀可复用流程，并触发下一轮 goal。

范围：feedback map、affected artifacts、next version plan、asset/job supersede、skill opportunity、阶段复盘。

非范围：覆盖旧版本；把客户机密写入 Skill；自动全局安装 Skill；忽略反馈影响范围。

关键里程碑：`feedback_map.csv` 更新；受影响 artifact 标记 supersede；`next_version_plan.md` 完成；Skill Mining Gate 完成；下一轮入口明确。

风险：新反馈污染旧版本；导演意见误覆盖客户需求；图片 job 未作废继续流入客户稿；Skill 沉淀泄漏客户信息。

验收标准：客户变更能覆盖旧需求但不删除历史；受影响图片/job/slot 有回退路径；可复用通路有 evidence；下一轮从 P0/P1/P3/P4 之一明确重启。

测试清单：检查 supersede 关系；检查 affected artifacts；检查 skill draft 不含客户机密；运行 Feedback Gate、Skill Mining Gate、反驳性议会。

责任人：Main Controller、Skill Miner、Operations Council。

预计时长：0.5-1 工作日。

依据来源/验收证据：`real_project_acceptance_criteria.md` Feedback Merge 与 Skill Mining；`ad_creative_orchestrator_v1_draft.md` reconciliation。

## 5. 反驳性议会门禁

门禁规则：
- 每个阶段 Gate 前必须运行反驳性议会。
- 每次至少记录 1 条有效反对意见。
- 反对意见必须绑定 artifact、requirement、risk 或 gate rule。
- 主控必须写出反驳路径、修订决议、是否通过门禁。
- 没有议会记录时，Gate 状态不得高于 `PARTIAL_PASS`。

议会角色：
- Strategy Council：反驳策略是否和需求/品牌事实断链。
- Operations Council：反驳状态、依赖、版本、文件协议是否不可执行。
- Craft Council：反驳产物是否对广告创意负责人不可读、不可审、不可交接。
- Risk Reviewer：反驳客户可见、版权、AI 图、PPT 可编辑、隐私/上传边界。

每阶段议会最低留痕：

| 阶段 | 反对意见 | 反驳路径 | 修订决议 | 门禁结论 |
|---|---|---|---|---|
| P0 | 资料边界不清，不能开始研究或生图 | 检查 `source_events`、`requirements`、`gaps`、追问清单 | blocking gap 写入 `待你确认.md`，只允许内部整理 | 缺口已显式记录才 PASS/PARTIAL_PASS |
| P1 | 搜索和图片路线仍会无限扩张 | 检查 stop condition 与 image route decision | 每条搜索和图片路线绑定退出条件 | 无 stop condition 则 BLOCKED |
| P2 | 参考和图片槽位断链 | 抽查 reference-to-requirement 与 slot-to-requirement | 补齐 source/role/slot/use case | 断链项不得进 P3 |
| P3 | 策略方向可读但不可执行 | 检查 proposal structure 与 image job contract | 将模糊视觉诉求拆为 job spec | 方向/job 任一缺 contract 则 REVISE |
| P4 | 探索图会被误当客户稿 | 检查 manifest、visibility、import log | 全部探索图标 internal_only，客户稿用 placeholder | 客户可见前必须 P5 |
| P5 | 客户稿有可见风险 | 检查 client pack、visual review、flags | 移除内注/假 logo/未授权图，保留风险说明 | 风险未清零则 BLOCKED |
| P6 | 交付文件不可编辑或不可追溯 | 检查 PPT editability、version、final gate | 不可编辑页说明原因；发送前人工确认 | 无确认不得发送 |
| P7 | 反馈会污染旧版本或泄密到 Skill | 检查 supersede、affected artifacts、skill evidence | 旧版本只 supersede；skill 去客户机密 | 无 version/evidence 则 REVISE |

演练样例：

| 项目 | 内容 |
|---|---|
| 场景 | P3 准备进入 P4，已有方向和 image job spec |
| 反对意见 | Image job 中产品包装仍使用 placeholder，批量生成会产生假包装字 |
| 反驳路径 | 检查 `image_generation_policy.md` Brand Safety 与 P3 image job output_contract |
| 修订决议 | P4 只允许生成 internal_only 构图/光影探索；产品包装区域用空白占位；客户可见候选必须等官方产品资产锁定 |
| 门禁结论 | P3→P4 `PARTIAL_PASS`，允许内部探索，禁止客户可见与批量分镜 |
| 验收证据 | image job visibility=`internal_only`；decision 写入 `decisions.csv`；Gate report 写明禁止项 |

## 6. 一刀流与模块化切换

一刀流路线：

```text
输入资料
→ P0 Intake
→ P1 Research/Image Strategy
→ P2 Reference/Slot
→ P3 Direction/Image Job
→ P4 Internal Prototype/Image Exploration
→ P5 Visual Review/Client Pack
→ P6 PPT/Final Gate
→ P7 Feedback/Skill Mining
→ 下一轮 goal
```

模块化路线：

```text
品牌深度研究单跑：P0 → P1 → P2 → P3 → Research/Creative Gate → 交付研究包
图片功能单跑：P0 最小事实基线 → P1 图片策略 → P2 slot → P3 image job → P4/P5 QA → 交付图片包
反馈修复单跑：P7 → 受影响阶段 → 对应 Gate → 更新 next_version_plan
```

切换规则：

| 条件 | 触发 | 暂停 | 恢复 | 失败回退 |
|---|---|---|---|---|
| 一刀流继续 | 当前阶段 Gate PASS，议会无 blocking，依赖产物存在 | Gate BLOCKED、客户/导演冲突、AI 图客户可见、发送客户稿 | blocking issue 关闭且 gate report 更新 | 回到最近一个产物锁定前阶段 |
| 一刀流降级模块化 | 某泳道完成但另一泳道缺输入；时间预算不足；只需研究包或图片包 | 下游阶段依赖另一泳道产物 | 补齐依赖后从当前阶段重新合流 | 回到 P1/P2 重建 plan/slot |
| 品牌泳道独立运行 | 目标是品牌研究、参考包、策略方向 | 需要客户可见图片或 PPT 交付 | 图片泳道完成 P2/P3 后合流 | 回 P1 补来源或 stop condition |
| 图片泳道独立运行 | 目标是图片整理、视觉 QA、image job、资产导入 | requirement/source/slot 任一缺失；客户可见确认缺失 | P0/P2 补齐绑定关系 | 回 P2 重建 slot，或 P3 重写 job |
| 模块化合流一刀流 | 两泳道共享 requirement/artifact/gate 均可追溯 | 任一产物 client_visibility 未确认 | 相关 Gate PASS 后合流 | 回到产生断链的最早阶段 |
| feedback 回退 | 客户反馈覆盖旧需求、产品/结构/资产变更 | 旧版本仍可能被下游引用 | supersede 完成，affected artifacts 更新 | 客户变更回 P0/P3；结构变更回 P3/P5；产品变更回 P2/P4 |

手工演练验证：

| 场景 | 判断 | 结论 |
|---|---|---|
| 只有客户 brief，暂无产品图 | P0/P1 品牌可跑；图片泳道只能建 unknown slot | 切模块化品牌研究，图片停在 P2 |
| 已有品牌证据和方向，缺 AI 图客户确认 | P3/P4 可内部探索；P5/P6 不可客户可见 | 一刀流暂停在 P5 前 |
| 客户反馈改 PPT 结构 | SlideSpec Lock 后结构变更 | 回 P3 Proposal Architecture，取消 P6 PPT Bridge |
| 产品图被替换 | Asset Lock 后产品变更 | 回 P2/P4，取消相关 image jobs |
| Gate BLOCKED | 客户稿含内部注释或未授权参考 | 停止下游导出，回问题来源阶段修订 |

## 7. Goal 持续推进闭环

标准循环：

```text
输入
→ 阶段执行
→ 阶段产物写入 project files
→ 阶段 Gate
→ 反驳性议会
→ 风险复盘
→ 决策更新
→ handoff 更新
→ 下一阶段或回退
```

推进触发条件：
- 阶段产物齐全。
- Gate 非 BLOCKED。
- 反驳性议会已有反对意见、反驳路径、修订决议。
- `work_items.csv` 下一项依赖已满足。
- `待你确认.md` 无阻塞级人工决策。

暂停条件：
- 客户/导演/用户需求冲突。
- 搜索范围、图片客户可见性、主视觉方向、人物/产品/场景锁定未确认。
- Gate BLOCKED。
- 需要付费、登录、私密账号、上传客户资料、发送客户稿、覆盖/删除旧版本、全局安装 Skill。

复用机制：
- 每阶段结束复制 `phase_prd_template.md` 填写下一阶段。
- 每个 Gate 使用 `adversarial_council_gate_template.md` 留痕。
- P7 检查 `skill_opportunities.csv`，只生成项目内 Skill 草稿。
- 下一轮 goal 从 `next_version_plan.md` 读取入口阶段和回退理由。

## 8. 阶段级验证方案

| 验收对象 | 验收人 | 验收方式 | 通过阈值 | 证据 |
|---|---|---|---|---|
| 阶段树 | Main Controller | 手工核对 P0-P7 两泳道字段 | 每阶段有输入/产出/依赖/退出/后置 | 本文第 2/3 节 |
| PRD 完整性 | Operations Council | 检查每个 PRD 统一字段 | 8 个 PRD 块无空字段 | 本文第 4 节 |
| 反驳性议会 | QA / Review Council | 检查每阶段至少一条反对意见链路 | 有反对意见/反驳路径/修订决议/门禁结论 | 本文第 5 节 |
| 切换规则 | Main Controller | 用 5 个场景手工演练 | 每个场景有暂停/继续/回退判断 | 本文第 6 节 |
| goal 闭环 | Main Controller | 检查输入到下一阶段链路 | 有推进/暂停/复用触发条件 | 本文第 7 节 |
| 项目一致性 | Operations Council | 对照 README/操作手册/验收标准 | 不引入外部不可验证信息 | 本文依据来源 |

验收演练结论：

| 检查项 | 结果 | 证据 |
|---|---|---|
| 品牌深度研究与图片功能能归一到同一阶段树 | PASS | P0-P7 均有双泳道映射 |
| 每阶段可独立运行 | PASS | 第 3 节每个泳道有独立输入/产出/退出条件 |
| 每阶段可串联一刀流 | PASS | 第 2/6 节给出下一阶段映射与一刀流路线 |
| 每阶段 PRD 字段完整 | PASS | 第 4 节每个 PRD 含目标、范围、非范围、里程碑、风险、验收、测试、责任人、时长、依据 |
| 反驳性议会可执行 | PASS | 第 5 节有阶段表与 P3 演练 |
| 切换规则可暂停/恢复/回退 | PASS | 第 6 节每类路线有触发、暂停、恢复、失败回退 |
| goal 模式可持续推进 | PASS | 第 7 节形成输入→执行→验收→复盘→决策→下一阶段 |

## 9. 下一轮队列

下一轮最小任务：
- 用 `templates/project/AD-creative/orchestrator/phase_prd_template.md` 为真实项目实例生成 P0/P1 阶段 PRD。
- 用 `templates/project/AD-creative/gates/adversarial_council_gate_template.md` 跑一次真实阶段 Gate。
- 将 Gate 结论写回 `gate_log.csv`、`decisions.csv`、`resolutions.csv`、`项目看板.md`、`待你确认.md`。
