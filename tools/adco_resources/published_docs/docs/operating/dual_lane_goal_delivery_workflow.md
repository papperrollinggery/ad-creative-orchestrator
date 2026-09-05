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

品牌深度研究：围绕客户资料、品牌事实、官方/可信参考、竞品与平台语境，形成 `current_truth`、`requirements`、`gaps`、`search_plan`、`reference_cards`、`visual_dna_notes` 和 evidence-bound creative brief；方向由 Sol/专业 Specialist 生成并经独立 Critic 后导入，只使用可追溯证据，不把未经确认的信息写成事实。

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

反驳性证据必须来自独立 reviewer，并绑定当前阶段的 exact target path/hash，时间不得早于目标文件。`global`、无关目标、BLOCKED 记录、旧 hash 或主线程/goal plan 自审都不能把 Gate 提升到 PASS。Gate 历史只追加新的 `gate_run_id`，不得覆盖旧结论。

## 2. 全局阶段树

| 阶段 | 品牌深度研究泳道 | 图片功能泳道 | 共享门禁 | 下一阶段映射 |
|---|---|---|---|---|
| P0 Truth / Lock | 登记资料，建立 current truth、requirements、gaps、version baseline | 盘点现有素材与授权未知项，锁定 FinalDelivery 保护基线 | Brief/Structure/FinalDelivery Lock | P1；事实、版本或保护边界不清则停在 `待你确认.md` |
| P1 Client Outline | 生成客户可读文本框架、逐页叙事与 client confirmation point | 定义每页 material role、visual slot、asset status；不生成 PPT | Outline content preflight | P2；文本不可确认则在 P1 修订 |
| P2 Hash Confirmation | 人工/客户审阅文本，写入 hash-bound confirmation receipt | 确认视觉槽位/素材角色边界，但不代替 asset authorization | Client Outline Gate | P3；confirmation 缺失或 hash stale 时 BLOCKED |
| P3 Creative / Reference / Neutral Specialist | 按需完成创意深化、参考证据、ADCO adoption | 形成 image job/visual exploration；影视专项走中立 specialist exchange | Creative/Reference/Specialist validation | P4；specialist QA 不能代替 ADCO adoption/Gate |
| P4 Immutable PPT | 从已确认 outline 导出新的 `client_review_vNNN.pptx`，更新 exact current version | 只把已登记的当前素材映射到 PPT slots，不覆盖旧版 | Immutable export/version integrity | P5；导出覆盖、版本断链或确认 stale 时 BLOCKED |
| P5 Language / Visual / Auth / Editability | 检查客户语言、exact-current derivatives、PPT editability | 检查 layout、asset manifest、hash/scope authorization、视觉风险 | Language/Layout/Authorization/Editability Gates | P6；任一客户可见风险未闭合则 BLOCKED |
| P6 Fresh Client Pack Binding | 生成 immutable package input manifest 与 current binding digest | 复核 package 中使用的 asset hash 与授权仍一致 | Client Pack Gate + exact-target adversarial review | P7；任一 exact-current 输入变化即 stale，必须重跑 |
| P7 Independent Review / Send Readiness | 独立人工 review 与 explicit send authorization 绑定同一 fresh digest | 复核实际附件/视觉/recipient scope；不执行发送 | Client Send Readiness Gate | P8；Gate PASS 只代表 ready-to-send，发送仍由人执行 |
| P8 Feedback / Next Version | 合并反馈、更新 current truth、supersede 旧版本、写 next version plan | 作废/重建受影响 asset/job，沉淀可复用图片链路 | Feedback/Skill Mining/Next-version Gate | 下一轮 P0/P1/P3/P4；按影响范围回退 |

## 3. 阶段核对表

| 阶段/泳道 | 独立输入 | 独立产出 | 依赖 | 退出条件 | 后置关系 |
|---|---|---|---|---|---|
| P0 品牌深度研究 | 原始资料、现有版本、FinalDelivery | `current_truth.md`、requirements/gaps、version/lock baseline | source events 已登记 | 事实、缺口、版本、保护范围可追溯 | P1 outline |
| P0 图片功能 | 客户素材、参考、未知来源图片 | initial asset inventory、授权未知项 | P0 truth baseline | 全部 internal/unknown，不升级 client_visible | P1 slots |
| P1 品牌深度研究 | P0 truth/requirements | `client_review_outline.md`、`client_outline.csv`、SlideSpec skeleton | blocking facts 已显式标记 | 每页低密度、客户可读、可决策、可确认 | P2 confirmation |
| P1 图片功能 | outline page/material needs | visual slot、material role、asset status | 每页 outline 存在 | 只定义槽位，不把未知素材当 approved | P2 confirmation |
| P2 品牌深度研究 | 可确认 outline、人工/客户反馈 | `client_outline_confirmation.json` | 人工/客户明确确认 | receipt 绑定 exact outline hash；Client Outline Gate PASS | P3 creative/reference |
| P2 图片功能 | 已确认 slots/material roles | confirmed slot boundary | 文本 confirmation fresh | 不把 outline confirmation 当 asset authorization | P3 specialist/image work |
| P3 品牌深度研究 | confirmed outline、requirements/gaps | creative/reference artifacts、specialist handoff/receipt/adoption | P2 PASS | 所有 adopted output hash/scope/identity 有证据 | P4 PPT |
| P3 图片功能 | slot contract、references、specialist recommendation | image jobs、internal visual candidates、manifest updates | 未授权只允许 internal | 每个 output 绑定 slot/source/hash，provider 无 ADCO authority | P4 PPT |
| P4 品牌深度研究 | confirmed outline、adopted internal artifacts | new immutable `client_review_vNNN.pptx`、version pointers | P2 confirmation still fresh | 不覆盖旧版；exact current 指针一致 | P5 quality gates |
| P4 图片功能 | registered current assets、PPT slots | exact PPT asset usage map | asset paths project-contained | 使用项可追溯，不把 authorization 留给 filename/notes | P5 visual/auth |
| P5 品牌深度研究 | exact current PPTX/derivatives | language/editability reports | P4 immutable version exists | client language、derivation、editability 无 blocker | P6 package |
| P5 图片功能 | PPT/preview、asset manifest/auth | visual layout/authorization reports | exact asset hashes 可重算 | 客户可见图 QA + hash/scope auth 均有效 | P6 package |
| P6 品牌深度研究 | P5-clean exact-current package inputs | immutable input manifest、`client_pack_binding.json`、Gate report | exact-target adversarial evidence | binding status PASS 且 digest 对当前输入 fresh | P7 review/send |
| P6 图片功能 | package asset inputs | asset/hash portion of package manifest | P5 auth/layout PASS | manifest 与 current asset hashes 一致 | P7 review/send |
| P7 品牌深度研究 | fresh binding、人工审阅、发送范围 | manual review receipt、send authorization、send-readiness report | 两份 receipt 同 digest | Send Readiness PASS；不执行发送 | P8 feedback |
| P7 图片功能 | 实际附件/视觉与 recipient scope | final visual review evidence | fresh binding 未变化 | review 覆盖实际包，未自签 | P8 feedback |
| P8 品牌深度研究 | 客户/导演/用户反馈 | feedback map、affected artifacts、next version plan | feedback 已登记 | 旧版只 supersede；回退入口明确 | P0/P1/P3/P4 |
| P8 图片功能 | 受影响 asset/job/slot | invalidation/rebuild plan、skill opportunity | 影响范围绑定 artifact | 受影响素材不再流入 current package | P0/P1/P3/P4 |

## 4. 每阶段 PRD

### PRD-P0 Truth / Lock

目标：建立可执行事实、版本与保护基线。范围：source events、current truth、requirements/gaps、现有 artifact/version、FinalDelivery lock、初始 asset inventory。非范围：创意定稿、PPT、客户发送。

关键里程碑：`current_truth.md`、requirements/gaps、version pointers 与 FinalDelivery hash baseline 可追溯。风险：假设写成事实、旧版被当 current、用户文件被覆盖。验收标准：blocking gap 显式；未知素材保持 internal/unknown；保护文件只登记 hash。

测试清单：运行 intake/validate/final-delivery-lock，核对 truth/version/lock 一致与 `待你确认.md`。责任人：Main Controller、Intake Analyst、Operations Council。预计时长：0.5-1 工作日。依据：Intake、Version Safety、FinalDelivery protection rules。

### PRD-P1 Client Outline

目标：把 P0 事实转成可由客户/用户逐页确认的低密度文本框架。范围：`client_review_outline.md`、`client_outline.csv`、SlideSpec skeleton、material role、visual slot/status。非范围：PPT、asset authorization、把 draft 写成已确认。

关键里程碑：每页有 title/body/client confirmation point/material role/visual slot/status。风险：文本过薄、内部语言泄漏、视觉槽位与叙事断链。验收标准：outline 内容可确认，但状态仍 pending。

测试清单：对显式创建的 client outline 运行 content preflight，检查所有必填字段与客户语言；`creative-brief` 不负责生成 outline。责任人：Proposal Architect、Copy/Creative、Slide Architect。预计时长：0.5-1 工作日。依据：Client Outline content contract。

### PRD-P2 Hash Confirmation

目标：把明确的人类/客户确认绑定到 exact outline hash。范围：逐页审阅、`confirm-client-outline` receipt、Client Outline Gate。非范围：执行面自签、把 outline confirmation 当 asset authorization。

关键里程碑：`client_outline_confirmation.json` 记录确认者、时间、evidence_ref、outline path/hash；Gate PASS。风险：确认后文本变化、automation/worker 冒充确认者。验收标准：receipt hash 与 current outline 一致；文本变化自动 BLOCKED。

测试清单：运行 confirm-client-outline/client-outline-gate，并做一次 outline mutation stale 检查。责任人：Human/Client Confirmer、Main Controller。预计时长：人工审阅时间。依据：Hash-bound confirmation contract。

### PRD-P3 Creative / Reference / Neutral Specialist

目标：在已确认 outline 上按需补足创意、参考、图片任务与专业领域判断。范围：creative directions、reference pack、image jobs、`adco.specialist-exchange` handoff/receipt/adoption。非范围：让 DIR/specialist 更新 ADCO control plane、PPT、FinalDelivery 或 readiness claims。

关键里程碑：创意候选绑定 exact brief/evidence 并经独立 Critic；reference 有 traceability；Specialist Exchange 选择双方最高共同版本，v1-only provider 可回退，ADCO 独立 adoption。风险：reference 断链、重复机制、品牌可替换、provider authority escalation、output/path/hash 漂移。验收标准：所有 imported/adopted output 绑定 evidence/provider/profile/descriptor/handoff/output scope/hash；domain QA 不越权。

测试清单：运行 creative-import/review、Reference/Specialist validation；v2 检查 inline-only、无 nested dispatch/outer readiness claims，v1 检查六个 reserved claims=false 与 host scope proof。责任人：Creative Strategist、Reference Researcher、Domain Specialist、ADCO Main Controller。预计时长：按 specialist scope。依据：Creative Contract 与 Specialist Exchange v1/v2。

### PRD-P4 Immutable PPT

目标：只在全项目 validation PASS 且 outline confirmation fresh 时创建新的 immutable current PPT version。范围：`export-pptx`、vNNN identity、current truth/version/artifact pointers、exact-current derivatives。非范围：覆盖旧版、任意 `--output` 路径、为导出清理 FinalDelivery、把定向导出当全项目完成。

关键里程碑：新 `client_review_vNNN.pptx` 不覆盖；version/artifact/current truth 一致。风险：legacy alias 被当 truth、project-wide CHECK、confirmation stale。验收标准：CHECK 在写前 `TOOL_BLOCKED`；通过后只落 canonical exports path；旧版本保持原 hash。

测试清单：连续导出 vNNN、拒绝覆盖/任意路径、核对 version chain。责任人：Main Controller、PPT Producer。预计时长：0.5 工作日。依据：Version Safety Rule。

### PRD-P5 Language / Visual / Authorization / Editability

目标：在构建 Client Pack 前对 exact-current PPT/package derivatives 运行独立质量门禁。范围：client language、visual layout、asset manifest/authorization、PPT editability、PDF/preview/text derivation。非范围：Client Pack freshness、人工 send review。

关键里程碑：语言/视觉/editability PASS；每个客户可见 asset 有 exact hash/use scope/approver/time/evidence receipt。风险：notes token 伪授权、symlink/path escape、preview 与 PPT 不一致。验收标准：所有 P5 blocker 清零，且检查对象都是 exact current。

测试清单：运行 language/asset-current-manifest/visual-layout/check-pptx，注入 stale hash/路径逃逸验证 BLOCKED。责任人：QA Reviewer、Visual Reviewer、PPT Reviewer。预计时长：0.5-1 工作日。依据：P5 Gate contracts。

### PRD-P6 Fresh Client Pack Binding

目标：把所有 exact-current package inputs 绑定成可失效的 immutable digest。范围：input manifest、`client_pack_binding.json`、version/digest Gate report、exact-target adversarial review。非范围：manual review、send authorization、实际发送。

关键里程碑：binding status PASS；manifest/report hash 可验证。风险：输入变化后复用旧 Gate、global/self adversarial review、gate history overwrite。验收标准：recompute digest 与 binding 一致；Gate 只表示 ready for independent review。

测试清单：运行 client-pack-gate，修改任一 exact-current input 并确认旧 binding stale；核对 append-only gate_run。责任人：Main Controller、Independent Adversarial Reviewer。预计时长：0.5 工作日。依据：Client Pack Binding 1.0。

### PRD-P7 Independent Review / Send Readiness

目标：由独立人类审阅 exact fresh package，并把明确发送授权与实际发送动作分开。范围：manual review receipt、send authorization、recipient scope、Client Send Readiness Gate。非范围：自动发送、执行面自签、复用 stale digest。

关键里程碑：两份 receipt 绑定同一 current version/PPTX hash/package digest；Gate PASS 且 `SEND_EXECUTED=0`。风险：reviewer/authorizer 非独立、recipient scope 缺失、package 在审阅后改变。验收标准：所有 identity/time/evidence/checks 完整且 binding fresh。

测试清单：运行 send-readiness，验证 stale digest/self-stamp/missing scope 均 BLOCKED。责任人：Independent Human Reviewer、Authorized Sender、Main Controller。预计时长：人工审阅时间。依据：Send Readiness contract。

### PRD-P8 Feedback / Next Version

目标：吸收反馈、保护版本链、沉淀可复用流程，并触发下一轮 goal。范围：feedback map、affected artifacts、next version plan、asset/job supersede、skill opportunity。非范围：覆盖旧版本、把客户机密写入 Skill、自动全局安装。

关键里程碑：反馈与 affected artifacts 登记；旧 current package 失效；下一轮入口明确。风险：反馈污染旧版、受影响 asset 继续流入包、Skill 泄密。验收标准：只 supersede 不覆盖；回到 P0/P1/P3/P4 的原因可追溯。

测试清单：检查 feedback/version/package invalidation 与 skill privacy；运行 Feedback/Skill Mining Gate。责任人：Main Controller、Skill Miner、Operations Council。预计时长：0.5-1 工作日。依据：Feedback Merge 与 Skill Mining rules。

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
| P0 | 事实/版本/FinalDelivery 边界不清 | 检查 source/truth/version/lock | blocking gap 与保护范围显式登记 | 基线不完整则 BLOCKED |
| P1 | outline 不可由客户逐页判断 | 检查 title/body/confirmation point/material role/slot | 补齐客户可读文本与槽位 | 不可确认则留在 P1 |
| P2 | confirmation 由执行面自签或 hash stale | 核对 confirmer/time/evidence/current hash | 重新取得真实人工/客户确认 | Client Outline Gate 必须 PASS |
| P3 | reference/specialist output 越权或断链 | 核对 source、descriptor、handoff、scope/hash/claims | ADCO 只采用边界内 recommendation | 无独立 adoption 不得进 P4 |
| P4 | 导出覆盖旧版或 version pointers 断裂 | 核对 vNNN/current truth/version/artifact | 回滚半更新并创建新版本 | immutable/version integrity 必须成立 |
| P5 | 客户语言、视觉、授权或 editability 有风险 | 检查 exact-current language/layout/auth/editability | 移除内注/假 logo/未授权图并重跑 | 任一 blocker 未清零则 BLOCKED |
| P6 | Client Pack binding stale 或 reviewer target 不精确 | 重算 digest，核对 exact target/hash/adversarial evidence | 生成新 immutable manifest/binding/gate run | 只到 independent-review-ready |
| P7 | review/send authorization 非独立或不绑定同一 digest | 核对 reviewer/authorizer/recipient/evidence/digest | 重新审阅/授权，保持 `SEND_EXECUTED=0` | Send Readiness 未 PASS 不得发送 |
| P8 | 反馈污染旧版本或泄密到 Skill | 检查 supersede、affected artifacts、package invalidation | 旧版只 supersede；skill 去客户机密 | 无 next-version/evidence 则 REVISE |

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
→ P0 Truth/Lock
→ P1 Client Outline
→ P2 Hash Confirmation
→ P3 Creative/Reference/Neutral Specialist
→ P4 Immutable PPT
→ P5 Language/Visual/Auth/Editability
→ P6 Fresh Client Pack Binding
→ P7 Independent Review/Send Readiness (never sends)
→ P8 Feedback/Next Version
→ 下一轮 goal
```

模块化路线：

```text
品牌/参考研究单跑：P0 → P3 research/creative outputs → 内部研究包（不宣称 client/PPT/send readiness）
图片功能单跑：P0 asset inventory → P3 image job/internal outputs → P5 visual/auth QA → 内部图片包
文本到审阅包：P0 → P1 → P2 → P3 → P4 → P5 → P6
发送准备：仅从 fresh P6 → P7；命令不发送
反馈修复：P8 → 受影响阶段 → 对应 Gate → next_version_plan
```

切换规则：

| 条件 | 触发 | 暂停 | 恢复 | 失败回退 |
|---|---|---|---|---|
| 一刀流继续 | 当前阶段 Gate PASS，议会无 blocking，依赖产物存在 | Gate BLOCKED、客户/导演冲突、AI 图客户可见、发送客户稿 | blocking issue 关闭且 gate report 更新 | 回到最近一个产物锁定前阶段 |
| 一刀流降级模块化 | 某泳道完成但另一泳道缺输入；只需内部研究/图片包 | 下游阶段依赖另一泳道产物 | 补齐依赖后按真实 phase 合流 | outline 回 P1/P2；专业产物回 P3；PPT 回 P4 |
| 品牌泳道独立运行 | 目标是品牌研究、参考包、策略方向 | 需要客户可见 PPT/发送 | 必须补齐 P1/P2 以及图片 P5 证据 | 回 P0/P3 补事实或来源 |
| 图片泳道独立运行 | 目标是图片整理、视觉 QA、image job、资产导入 | requirement/source/slot 或授权 receipt 缺失 | P0/P1/P3 补齐绑定关系 | 回 P3 重写 job，P5 重跑 auth/layout |
| 模块化合流一刀流 | requirement/artifact/version/gate 可追溯 | outline confirmation 或 asset authorization stale | 重跑相应 P2/P5 后合流 | 回到最早失效阶段 |
| feedback 回退 | P8 发现客户/产品/结构/资产变更 | 旧 binding/version 仍可能被引用 | supersede、affected artifacts 与 package invalidation 完成 | 事实回 P0；文本回 P1/P2；创意回 P3；版式回 P4；素材 QA 回 P5 |

手工演练验证：

| 场景 | 判断 | 结论 |
|---|---|---|
| 只有客户 brief，暂无产品图 | P0/P1/P2 文本可推进；视觉 slot 保持 unknown | P3 只做 internal specialist/image work，P5 授权前不进 P6 |
| 已有方向，缺 AI 图授权 receipt | P3 可内部探索；P4 可使用明确 placeholder | P5 BLOCKED，不能生成 fresh P6 binding |
| 客户反馈改已确认文本/PPT 结构 | P2 confirmation 与 P6 binding 都 stale | 回 P1/P2，再创建新的 P4 版本 |
| 产品图被替换 | asset hash/auth/package digest 全部受影响 | 回 P3/P5，作废旧 P6/P7 证据 |
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
- P8 检查 `skill_opportunities.csv`，只生成项目内 Skill 草稿。
- 下一轮 goal 从 `next_version_plan.md` 读取入口阶段和回退理由。

## 8. 阶段级验证方案

| 验收对象 | 验收人 | 验收方式 | 通过阈值 | 证据 |
|---|---|---|---|---|
| 阶段树 | Main Controller | 手工核对 P0-P8 两泳道字段 | 每阶段有输入/产出/依赖/退出/后置 | 本文第 2/3 节 |
| PRD 完整性 | Operations Council | 检查每个 PRD 统一字段 | 9 个 PRD 块无空字段 | 本文第 4 节 |
| 反驳性议会 | QA / Review Council | 检查每阶段至少一条反对意见链路 | 有反对意见/反驳路径/修订决议/门禁结论 | 本文第 5 节 |
| 切换规则 | Main Controller | 用 5 个场景手工演练 | 每个场景有暂停/继续/回退判断 | 本文第 6 节 |
| goal 闭环 | Main Controller | 检查输入到下一阶段链路 | 有推进/暂停/复用触发条件 | 本文第 7 节 |
| 项目一致性 | Operations Council | 对照 README/操作手册/验收标准 | 不引入外部不可验证信息 | 本文依据来源 |

验收演练结论：

| 检查项 | 结果 | 证据 |
|---|---|---|
| 品牌深度研究与图片功能能归一到同一阶段树 | PASS | P0-P8 均有双泳道映射 |
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
