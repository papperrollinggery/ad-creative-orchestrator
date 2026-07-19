# First Real Project Runbook

用途：把一个真实广告项目接入 Ad Creative Orchestrator。

## 0. 前置

在真实项目目录中准备原始资料即可。`adco init` 默认只创建小型 Content Surface：

```text
AD-creative/AGENTS.md
AD-creative/orchestrator/
AD-creative/handoff/
```

进入客户可见版本、PPT、FinalDelivery 或显式运行 `adco init --full` 时，ADCO 才展开 `00` 到 `05` 的人类工作区和完整交付账本。

可从这里复制：

```text
<仓库根目录>/templates/project/
```

或运行：

```text
adco init <真实项目路径>
```

`AD-creative/AGENTS.md` 是局部执行规则：先读资料、完成内容判断，只在真实风险边界使用 Gate/版本/PPT/Thread，并明确 `VALIDATION=PASS` 只是结构和追溯通过。

真实项目目录已有根级 `AGENTS.md` 时不会被覆盖；不再生成或要求合并建议。

## 1. 放入资料

Content Surface 不按 P0-P8 表演流程；先完成本轮广告内容工作。P0-P8 只用于已经触发的 Delivery Surface。

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

需要本地状态视图时再打开：

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

其中 `run` 把资料解析成 evidence chunks，更新 fact inventory、requirements、真实 gaps/conflicts，并先输出内容答案；默认 Dashboard、Council、Thread、Specialist、客户 outline、PPT、Client Pack 和全量 validation 都是 0。`status` 只读；`next` 只推进到下一个安全内容动作。AI 图客户可见、客户稿发送、付费/登录/上传资料前必须停。

Codex 展开方式：

给 Codex：

```text
先运行 `adco docs`，读取输出中的 `SKILL_DRAFT`。
执行 Agent 的 start/status 语义路线；这不是额外 CLI 子命令。

项目目录：
<填真实项目路径>

要求：
1. 先读取 AD-creative/AGENTS.md、真实资料和与本轮目标直接相关的状态文件。
2. 如果是新项目，按模板初始化缺失文件。
3. 先输出可用的内容判断，不把路径、Gate 或记录当答案。
4. 只询问真正阻塞本轮产出的缺口。
```

## 3. 添加资料 Prompt

```bash
adco run <真实项目路径> --material <新增资料路径>
```

Codex 应把新增资料分类为 `initial / supplement / change / feedback / approval / rejection / unknown`，并执行：

```text
要求：
1. 登记 source event。
2. 抽取 requirements / 真实 gaps，并区分确认事实、推断和未知。
3. 继续所有不被缺口阻塞的内容工作。
4. 如果确实需要客户/导演/我确认，写入 待你确认.md。
5. 返回内容结论和下一内容动作。
```

## 4. 推进 Prompt

```bash
adco next <真实项目路径>
```

对应的 Agent 语义要求：

```text
要求：
1. 读取真实资料、当前 truth 和本轮内容目标。
2. 只为真正阻塞本轮产出的未知停下；其余工作继续。
3. 直接完成下一个内容动作，不默认创建 work item、Gate 或 handoff packet。
4. 只有触发客户可见/版本/资产/PPT/FinalDelivery/发送边界时才升级治理。
5. 更新内容摘要和真实待确认项。
```

## 4.1 Goal 模式 Prompt

```text
先运行 `adco docs`，使用输出中的 `SKILL_DRAFT`。

只有用户明确要求建立长期目标/交付计划时才进入 goal 模式；普通内容任务不需要。

要求：
1. 先读取 docs/operating/dual_lane_goal_delivery_workflow.md。
2. 复制 templates/project/AD-creative/orchestrator/goal_iteration_plan_template.md 作为本轮执行记录。
3. 只拆当前目标真正需要的任务线，不固定双泳道或角色数量。
4. 每阶段写内容输入、产出、依赖和退出条件；记录规模与风险成比例。
5. 议会、独立 reviewer、Gate 只在对应判断风险确有价值时使用。
6. 阶段先交付内容结果，再附必要的治理证据。
7. 进入 Delivery Surface 后，才按相关边界运行 `adco validate` 和对应 Gate。
```

## 4.2 Creative Contract Prompt

Goal 模式默认仍由单一主控 inline 推进，不因“复杂”自动开 Threads。只有有界隔离、真实并行或独立 cold review 有明确收益时才生成 Thread lane。真实 worker 必须绑定真实 thread id；主控保存 host scope baseline，并在 reconcile 时用实际 diff 生成 host scope proof。轮询次数只是检查预算，最多一次有绝对截止时间的 extension 和一次独立证明的 rescue。

命令：

```text
adco creative-brief <真实项目路径> [--work-id <id>] [--json]
adco creative-import <真实项目路径> --file <candidate.json> [--json]
adco creative-review <真实项目路径> [--json]
```

```text
creative-brief -> Sol/专业 Specialist -> independent Critic -> creative-import

要求：
1. creative-brief 只冻结 evidence/fact/requirement/gap，生成 contract/schema/request，不生成方向或客户稿。
2. GPT-5.6 Sol 或明确选择的专业 Specialist 基于 exact brief snapshot 生成 4-6 个机制不同的候选。
3. 独立 Critic 检查 brief adherence、insight、brand ownership、机制差异、key visual、shootability、production risk 和 brand replacement，保留 2-3 个。
4. creative-import 要求每个候选绑定现有 evidence chunk；无证据、stale snapshot 或重复机制直接拒绝，品牌专属性弱会被标记。
5. creative-review 是确定性结构/语言 lint，不能替代独立 Critic；creative-proposal 仅是 creative-brief 的弃用 alias。
6. 不复制 Cannes / Effie / System1 / Google / TikTok / WARC / Ipsos 案例措辞。
7. 视频脚本、分镜、video prompt 使用 `adco specialist-handoff` 的 `dircreative.film-preproduction` profile；Controller 选择双方最高共同版本，provider 仅支持 v1 时回退 v1，v2 只允许 inline 且拒绝 nested dispatch 和外层 readiness claims。
8. image / KV / 背景图交给 imagegen 或 Creative Production；固定 PPT / DOCX / XLSX 模板交给对应文档流程。
```

如果要运行确定性候选 lint：

```text
adco creative-review <真实项目路径>

要求：
1. 检查结构、证据绑定、机制差异、品牌专属性、视觉清晰度、可拍性和生产风险。
2. receipt 明确标注 deterministic lint；独立 Critic 证据仍需另行完成。
3. 结构 PASS 只表示可以继续人工创意复核或专项交接。
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

只运行当前边界对应的命令。内部内容答案不要求 Council 或完整 Gate 链；进入 Delivery Surface 后，才从下面选择相关检查：

```text
adco validate <真实项目路径>
adco creative-brief <真实项目路径>
adco creative-import <真实项目路径> --file <candidate.json>
adco creative-review <真实项目路径>
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

通过标准不是“所有状态都 PASS”，而是当前交付边界所需证据齐全：

```text
ERRORS=0
VALIDATION=PASS
当前边界对应的 Gate=PASS/PARTIAL_PASS（按该 Gate 语义）
CLIENT_SEND_READINESS_GATE 仅在本轮确实准备发送时要求
HANDOFF_READINESS_GATE 仅在需要内部运营交接时要求
```

`VALIDATION=PASS` 只证明结构、CSV/JSON、引用链和 traceability 成立。它不批准创意质量、审美、客户话术、客户可见 AI 图或最终发送。`creative-import`/`creative-review` 通过也只证明候选契约和确定性 lint 成立，不能替代独立 Critic 或客户批准。

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
