# First Real Project Runbook

用途：把一个真实广告项目接入 Ad Creative Orchestrator。

## 0. 前置

在真实项目目录中准备：

```text
00_项目资料_ProjectMaterials/
01_参考资料_References/
02_重要素材_KeyAssets/
03_阶段成果_WorkInProgress/
04_客户审阅_ClientReview/
05_最终交付_FinalDelivery/
AD-creative/
AGENTS.md
```

`00` 到 `05` 是给人看的项目目录。adco 会更新每个目录下的 `目录索引.md`，把 `AD-creative/` 深层控制面里的真实产物映射出来；不要让这些目录长期只剩 README。

可从这里复制：

```text
<仓库根目录>/templates/project/
```

或运行：

```text
adco init <真实项目路径>
```

新项目根目录的 `AGENTS.md` 是项目级执行规则。它要求所有 Codex 线程先读取项目事实源、handoff 文件和安全边界，再开始执行；也会明确 `VALIDATION=PASS` 只是结构和追溯通过，不代表客户创意质量批准。

如果真实项目目录已有 `AGENTS.md`，初始化会跳过已有文件，不会覆盖，并写出 `AD-creative/orchestrator/AGENTS.merge_suggestion.md`。把 Ad Creative Orchestrator 的规则人工合并到现有文件，保留客户、仓库或团队已有禁区；未合并前 `adco validate` 会返回 `CHECK`。

## 1. 放入资料

运行时按 P0-P8 推进：P0 truth/lock，P1 client outline，P2 hash confirmation，P3 creative/reference/neutral specialist，P4 immutable PPT，P5 language/visual/authorization/editability，P6 fresh Client Pack binding，P7 independent review/send readiness（不发送），P8 feedback/next version。

把资料放入：

```text
00_项目资料_ProjectMaterials/01_客户资料_ClientMaterials/
00_项目资料_ProjectMaterials/02_会议记录_MeetingNotes/
00_项目资料_ProjectMaterials/03_导演组资料_DirectorNotes/
00_项目资料_ProjectMaterials/04_客户反馈_ClientFeedback/
```

不要把资料放进 `AD-creative/`。

## 2. 启动 Prompt

非开发者最短方式：

```text
adco run <真实项目路径> --material <资料文件或文件夹>
```

然后打开：

```text
AD-creative/handoff/操作台.html
```

最短方式使用真实 CLI：

```bash
adco docs
adco run <真实项目路径> --material <客户资料/会议记录/反馈所在文件夹或文件>
adco status <真实项目路径>
adco next <真实项目路径>
```

其中 `run` 登记资料并停在客户可读文本框架；`status` 只读；`next` 只推进到下一个安全决策点。公开官方来源搜索可在前置 Gate 满足后推进；AI 图客户可见、客户稿发送、付费/登录/上传资料前必须停。

Codex 展开方式：

给 Codex：

```text
先运行 `adco docs`，读取输出中的 `SKILL_DRAFT`。
执行 Agent 的 start/status 语义路线；这不是额外 CLI 子命令。

项目目录：
<填真实项目路径>

要求：
1. 先读取项目根目录 AGENTS.md、AD-creative/orchestrator/ 和 AD-creative/handoff/。
2. 如果是新项目，按模板初始化缺失文件。
3. 不做创意生产。
4. 只输出当前状态、缺失文件、下一步建议。
```

## 3. 添加资料 Prompt

```bash
adco run <真实项目路径> --material <新增资料路径>
```

Codex 应把新增资料分类为 `initial / supplement / change / feedback / approval / rejection / unknown`，并执行：

```text
要求：
1. 登记 source event。
2. 抽取 requirements / gaps。
3. 判断是否需要搜索。
4. 如果需要客户/导演/我确认，写入 待你确认.md。
5. 输出客户追问话术。
6. 不直接开始创意生产。
```

## 4. 推进 Prompt

```bash
adco next <真实项目路径>
```

对应的 Agent 语义要求：

```text
要求：
1. 读取当前 truth / work items / gate log。
2. 如果有待确认，停下。
3. 如果可推进，创建下一个 work item。
4. 如果需要专项 agent，生成 handoff packet。
5. 如果需要 Gate，先跑 Gate。
6. 更新 项目看板.md 和 待你确认.md。
```

## 4.1 Goal 模式 Prompt

```text
先运行 `adco docs`，使用输出中的 `SKILL_DRAFT`。

以 goal 模式推进。

要求：
1. 先读取 docs/operating/dual_lane_goal_delivery_workflow.md。
2. 复制 templates/project/AD-creative/orchestrator/goal_iteration_plan_template.md 作为本轮执行记录。
3. 按品牌深度研究 / 图片功能双泳道拆阶段。
4. 每阶段写输入、产出、依赖、退出条件、下一阶段。
5. 每个 Gate 前运行反驳性议会。
6. 没有反对意见、反驳路径、修订决议时，Gate 最高只能 PARTIAL_PASS。
7. 阶段完成后更新 gate_log / decisions / resolutions / 项目看板 / 待你确认。
8. 运行 `adco validate` 后再报告结果。
```

## 4.2 Creative Proposal Prompt

Goal 模式默认仍由单一主控 inline 推进，不因“复杂”自动开 Threads。只有有界隔离、真实并行或独立 cold review 有明确收益时才生成 Thread lane。真实 worker 必须绑定真实 thread id；主控保存 host scope baseline，并在 reconcile 时用实际 diff 生成 host scope proof。轮询次数只是检查预算，最多一次有绝对截止时间的 extension 和一次独立证明的 rescue。

命令：

```text
adco creative-proposal <真实项目路径> [--work-id <id>] [--json]
adco creative-quality-gate <真实项目路径>
```

```text
creative-proposal

要求：
1. 只起草 internal proposal，不写 client-approved / final。
2. 产出 challenge interpretation、insight、creative idea、option matrix、message line、proposal structure。
3. 每个 claim 必须绑定 requirement、source_event、reference 或明确标成 assumption / gap。
4. 使用 docs/operating/creative_proposal_quality_standard.md 的 source mapping 做本地检查。
5. 不复制 Cannes / Effie / System1 / Google / TikTok / WARC / Ipsos 案例措辞。
6. 视频脚本、分镜、video prompt 使用 `adco specialist-handoff` 的 `dircreative.film-preproduction` profile；不读取或写死 DIR 仓库内部路径。接受兼容 descriptor `1.x` 时仍要求它显式支持 base contract `1.0`，并按 exact id/version 协商 profile receipt extension。
7. image / KV / 背景图只写 image job spec，交给 imagegen 或 Creative Production。
8. 固定 PPT / DOCX / XLSX 模板只写结构和字段，交给 Template Creator。
```

如果要审核 proposal：

```text
creative-quality-gate

要求：
1. 审核结构、追溯、证据、专业完整度和客户可见风险。
2. 明确输出 PASS / PARTIAL_PASS / REVISE / BLOCKED。
3. PASS 只表示 ready for human creative review 或 specialist handoff。
4. 不把 PASS 写成客户批准、审美批准、商业效果证明或最终发送许可。
```

如果要进入 PPT builder 或客户版导出：

```text
adco confirm-client-outline <项目目录> --confirmed-by "<人工确认者>" --confirmed-at <iso_time> --evidence-ref "<user_confirmation:id|client_confirmation:id>"
adco client-outline-gate <项目目录>
adco export-pptx <项目目录>
adco check-pptx <项目目录> --file <项目目录>/AD-creative/ppt/exports/client_review_vNNN.pptx
adco client-language-gate <项目目录>
adco asset-current-manifest <项目目录>
adco visual-layout-gate <项目目录>
adco client-pack-gate <项目目录>
adco client-send-readiness-gate <项目目录>
```

要求：
1. 先由人工/客户审阅文本，再用 `confirm-client-outline` 把确认绑定到 exact outline hash；`client-outline-gate` BLOCKED 时不允许进入 PPT builder。文本变更会让确认失效。客户详细方案可以是 22-45+ 页，但每页必须低密度、客户可读、能决策，并填写 visual_slot / visual_asset_status。
2. `client-language-gate` 命中 prompt/thread/worker/AI/gate/内部/执行过程/需确认等词时，不允许导出客户版。
3. 用户说 Grok/ChatGPT/ImageGen/browser 已有图时，先执行 `adco browser-asset-intake ...` 或 `adco preflight-asset ...`，不能直接判定缺图或重复生成。
4. `visual-layout-gate` 没有 exact current PPTX 和真实 preview 时必须 BLOCKED；有真实页面后再检查拉伸、裁切、图片尺寸、卡片套卡片、报告感、文字过短、图文不匹配、同图重复误用、竖屏/横屏比例和客户阅读顺序。
5. `approval=PASS` 不算授权；客户可见素材必须有匹配 asset hash/scope 的独立 `asset_authorizations.csv` receipt。
6. `client-pack-gate` 只代表 ready for independent human review，并把所有 exact-current 输入绑定为 package digest。任何输入变化后必须重跑。`client-send-readiness-gate` 还要求独立人工 review receipt 和发送授权都绑定同一个 fresh digest，并且不会发送。
7. `VALIDATION=PASS` 只代表结构和追溯关系，不代表创意质量、客户语言、视觉审美、素材授权或可发送。

如果要清理文件或确认最终交付：

```text
adco final-delivery-lock <项目目录>
adco dedupe-audit <项目目录>
adco cleanup-plan <项目目录>
```

要求：
1. `05_最终交付_FinalDelivery` 里用户手动放入的 PPT/PDF 默认 protected，只登记 hash。
2. `dedupe-audit` 和 `cleanup-plan` 只分类原图、重要裁切、派生图、旧导出、缓存、预览、contact sheet，不直接删除。

## 5. 状态 Prompt

```bash
adco status <真实项目路径>
```

状态路线只读，不推进：

```text
只读，不推进。

输出：
项目阶段
卡点
待确认
最近产物
下一步建议
```

## 6. Gate Prompt

使用对应阶段的真实 Gate 命令，例如：

```bash
adco creative-quality-gate <真实项目路径>
adco client-outline-gate <真实项目路径>
adco film-quality-gate <真实项目路径>
adco visual-layout-gate <真实项目路径>
adco client-pack-gate <真实项目路径>
```

`gate/review` 是 Agent 级语义路线；命令行不存在名为 `gate` 的通用 adco 子命令。审核时遵守：

```text

Gate 类型：
Brief Gate / Research Gate / Creative Gate / Client Outline Gate / Visual Review Gate / PPT/Layout Gate / Client Pack Gate / Client Send Readiness Gate / Internal Handoff Gate / Skill Mining Gate

检查对象：
<填 artifact 或 stage>

要求：
1. 只审核，不直接改稿。
2. 输出 PASS / PARTIAL_PASS / REVISE / BLOCKED。
3. 写 gate report。
4. 更新 gate_log / artifact_index / work_items / 项目看板。
```

## 7. Skill Mining Prompt

`mine skill` 是 Agent 级语义路线，不是 CLI 子命令。只有识别出有证据的复用通路时才使用：

```text
要求：
1. 检查当前项目是否有可复用通路。
2. 需要 evidence。
3. 只生成项目内 Skill 草稿。
4. 不安装到 ~/.codex/skills。
5. 不包含客户机密或一次性文案。
```

## 8. 验证命令

每个关键阶段后运行：

```text
adco council <真实项目路径> --render-dashboard
adco validate <真实项目路径>
adco creative-proposal <真实项目路径>
adco creative-quality-gate <真实项目路径>
adco confirm-client-outline <真实项目路径> --confirmed-by "<人工确认者>" --confirmed-at <iso_time> --evidence-ref "<user_confirmation:id|client_confirmation:id>"
adco client-outline-gate <真实项目路径>
adco search-quality-gate <真实项目路径>
adco reference-pack-gate <真实项目路径>
adco visual-quality-gate <真实项目路径>
adco client-pack-gate <真实项目路径>
adco client-send-readiness-gate <真实项目路径>
adco handoff-readiness-gate <真实项目路径>
```

`creative-quality-gate` 会把审核结果写入 Gate report / gate_log。证据稀疏、来源未闭合或关键假设未确认时，应接受 PARTIAL_PASS / BLOCKED，不要强行写 PASS。

通过标准：

```text
COUNCIL=PASS
ERRORS=0
VALIDATION=PASS
CREATIVE_QUALITY_GATE=PASS 或 PARTIAL_PASS
SEARCH_QUALITY_GATE=PASS 或 PARTIAL_PASS
REFERENCE_PACK_GATE=PASS 或 PARTIAL_PASS
VISUAL_QUALITY_GATE=PASS
CLIENT_PACK_GATE=PASS
CLIENT_SEND_READINESS_GATE=PASS（仅在本轮确实准备发送，且独立人工审阅和发送授权绑定同一 fresh package digest 时要求）
HANDOFF_READINESS_GATE=PASS（仅表示内部运营可交接）
```

`VALIDATION=PASS` 只证明结构、CSV/JSON、引用链和 traceability 成立。它不批准创意质量、审美、客户话术、客户可见 AI 图或最终发送。`CREATIVE_QUALITY_GATE=PASS` 也只是 proposal 草稿可进入人工创意复核或专项模块交接，不是客户批准。

## 9. 人工停点

看到这些必须停：

```text
brief 边界不清
客户/导演需求冲突
创意方向数量
主视觉方向
人物/产品/场景资产锁定
AI 图是否客户可见
客户稿发送前
全局 Skill 安装前
```

## 10. 验收

真实项目第一轮完成后，检查：

```text
AD-creative/handoff/项目看板.md 是否能让用户知道项目卡在哪里
AD-creative/handoff/待你确认.md 是否只列真正需要用户决策的问题
AD-creative/orchestrator/work_items.csv 是否能派发下一个 agent
AD-creative/agents/runs/<run_id>/handoff.md 是否能让另一个 agent 接手
AD-creative/orchestrator/artifact_index.csv 是否能追踪产物状态
AD-creative/orchestrator/gate_log.csv 是否挡住客户稿风险
AD-creative/orchestrator/goal_iterations/ 是否有本轮 goal 执行记录
AD-creative/handoff/操作台.html 是否显示 Goal Tab
adco validate 是否 PASS
adco check 是否 PASS
```
