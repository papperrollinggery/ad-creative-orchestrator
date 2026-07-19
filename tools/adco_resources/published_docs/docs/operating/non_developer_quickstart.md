# 非开发者快速开始

目标：广告创意负责人不用理解代码、CSV、Python 结构，也能启动、查看、推进项目。

## 1. 准备资料

把资料放到真实项目目录：

```text
00_项目资料_ProjectMaterials/
```

可以是客户 brief、会议记录、导演意见、客户反馈、参考链接整理。

## 2. 启动项目

项目按 P0-P8 依次推进：事实/保护基线 → 客户可读文本 → hash 确认 → 按需创意/参考/专项 → 不可变 PPT → 语言/视觉/授权/可编辑性 → fresh Client Pack → 独立审阅/发送准备（不发送）→ 反馈/下一版本。

最简单方式：

```text
在仓库根目录双击 `启动广告创意项目.command`
```

弹窗会要求选择：

```text
项目文件夹
客户资料文件或文件夹
本轮目标
```

完成后会自动打开：

```text
AD-creative/handoff/操作台.html
```

命令行方式：

```text
adco quickstart
adco quickstart --json
adco support-bundle <项目目录> --json
adco audit-dashboard <项目目录> --render --json
adco demo
adco run <项目目录> --material <资料文件或文件夹>
adco profile-analyze <项目目录> --source-id <SRC-ID> --brand <品牌> --company <公司>
adco open-dashboard <项目目录>
adco docs
```

默认 `adco run` 产物：

```text
AD-creative/handoff/操作台.html
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/客户追问话术.md
AD-creative/orchestrator/evidence_chunks.jsonl
AD-creative/orchestrator/fact_inventory.jsonl
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
AD-creative/orchestrator/current_truth.md
AGENTS.md
```

默认运行只做资料解析、事实/缺口更新、handoff 刷新、一次操作台渲染和受影响范围验证；Council、画像分析、创意方向、Specialist、客户 outline、PPT、Client Pack 和全量 delivery validation 都不会自动执行。

`AGENTS.md` 在项目根目录。它不是客户稿，而是给 Codex 线程看的项目规则：先读哪些文件、哪些事必须停下来确认、哪些 Gate 必须跑、`VALIDATION=PASS` 不能当作客户创意质量批准。

如果项目里已经有 `AGENTS.md`，初始化不会覆盖。保留原有规则；如果生成 `AD-creative/orchestrator/AGENTS.merge_suggestion.md`，把里面的 Ad Creative Orchestrator 项目规则人工合并进根目录 `AGENTS.md`。
合并建议会写到：

```text
AD-creative/orchestrator/AGENTS.merge_suggestion.md
```

如果根目录 `AGENTS.md` 缺失或没有合入必需规则，`adco validate` 会返回 `CHECK`。

adco 的创意控制定位：

```text
adco creative-brief <项目目录> [--work-id <id>] [--json]
adco creative-import <项目目录> --file <candidate.json> [--json]
adco creative-review <项目目录> [--json]

creative-brief 只冻结 evidence/fact/requirement/gap，并生成 brief contract、candidate schema 和 generation request；它不生成创意方向。
GPT-5.6 Sol 或明确选择的专业 Specialist 基于该 contract 生成 4-6 个候选；独立 Critic 做品牌替换测试和机制去重后保留 2-3 个，再交给 creative-import。
creative-import 拒绝无证据、stale snapshot 和重复机制；品牌专属性弱会被标记。creative-review 只是确定性结构/语言 lint，不能替代独立 Critic、客户或创意负责人判断。
creative-proposal 仅为 creative-brief 的弃用兼容 alias。
视频/分镜/video prompt 通过协商后的 `adco.specialist-exchange` 交给 `dircreative.film-preproduction`；ADCO 保留采用、版本、PPT 和客户准备权。
image / KV / 背景图交给 imagegen 或 Creative Production。
固定 PPT / DOCX / XLSX 模板交给 Template Creator。
```

标准见：

```text
docs/operating/creative_proposal_quality_standard.md
```

## 3. 看哪里

优先看：

```text
AD-creative/handoff/操作台.html
```

再看：

```text
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/客户追问话术.md
AD-creative/client_review/client_outline.csv
```

默认 `run` 只到 Intake/handoff。客户可读 outline 必须在后续明确任务中形成；人工或客户逐页确认 exact outline 后，再运行：

```text
adco confirm-client-outline <项目目录> --confirmed-by "<人工确认者>" --confirmed-at <iso_time> --evidence-ref "<user_confirmation:id|client_confirmation:id>"
adco client-outline-gate <项目目录>
```

确认 receipt 绑定 exact `client_outline.csv` hash；文字一改就失效，必须重新确认。Gate PASS 前不生成 PPT。

生成图入库：

```text
adco import-imagegen <项目目录> --slot-id <槽位> --selected
```

用途：

```text
从 CODEX_HOME/generated_images 取最近一张生成图，复制到 AD-creative/visual_assets/selected/，登记 asset_manifest.csv，写 imagegen_import_log.md，刷新操作台。
默认 internal_only；客户可见前必须另跑 Gate，并取得绑定 exact asset hash/use scope/确认者/时间/evidence 的独立授权 receipt。
```

Goal 模式执行：

```text
adco goal-plan <项目目录> --title <目标标题> --objective <目标内容>
adco thread-plan <项目目录> --title <目标标题> --objective <目标内容> --roles brand_client,copy_creative,qa_review
```

`thread-plan` 只给 Codex 主控生成内部线程分工包，不会自动发送客户稿。Threads 默认关闭，只在有界隔离、真实并行或独立审阅确有必要时启用。需要独立反驳性证据的内容 Gate，如果没有绑定 exact stage target/hash 的新鲜 reviewer 记录，最高只会给 `PARTIAL_PASS`；`global` 或主线程自审不算。

Thread 执行规则：

```text
主控线程只负责拆分、分派、集成、验证、清理、汇报。
execution_worker 负责明确范围内的实现、文档修改、素材和产物制作。
read_only 只用于 explorer / reviewer / research / cold-review。
execution_worker 必须先写清 exact write_scope。
每个 execution_worker 返回 files_changed、validation、dirty-state impact、cleanup actions。
主控 dispatch 后保存 host scope baseline；reconcile 时用实际文件 diff 对照 receipt 与 exact write_scope，写出 hash-bound host scope proof。worker 自报不算 host proof。
主控消费 receipt 并合并后，归档对应 worker thread。固定轮询次数只是检查预算；区分 active_with_progress / silent / finalizing_receipt，最多一次 bounded extension 和一次带独立 dispatch proof/receipt path 的 rescue。
```

会议画像分析：

```text
adco profile-analyze <项目目录> --source-id <SRC-ID> --brand <品牌> --company <公司>
```

它会回答：谁说了什么、谁更可能拍板、谁影响大、他们想要什么、担心什么、品牌/公司有什么特点、分歧该怎么合。结论默认只是候选判断，需要你确认后才当最终事实。

工作区整洁检查：

```text
adco hygiene <项目目录>
```

它只检查不删除，主要看有没有临时缓存、未跟踪文件、没收尾的 Thread 记录。

不要手动改：

```text
AD-creative/orchestrator/*.csv
AD-creative/orchestrator/events.jsonl
```

## 4. 怎么继续

对 Codex 说：

```text
先读取项目根目录 AGENTS.md。
读取 AD-creative/handoff/项目看板.md 和 AD-creative/handoff/待你确认.md
运行 adco status <项目目录> 获取只读状态；没有人工阻塞时再运行 adco next <项目目录>
优先完成需求整理、缺口判断、客户追问、下一步建议。
```

命令行状态检查：

```text
adco status <项目目录>
adco next <项目目录>
```

## 5. 什么时候停

内部整理不用停。

必须人工确认：

```text
发送客户稿
付费、登录、私密账号、KYC、钱包或凭据
上传客户资料到外部平台
全局安装 Skill
覆盖或删除旧版本
将 AI 图标记为客户可见
```

## 6. 判断能不能交给别人

执行：

```text
adco council <项目目录> --render-dashboard
adco intake <项目目录>
adco profile-analyze <项目目录> --source-id <SRC-ID> --brand <品牌> --company <公司>
adco creative-brief <项目目录>
adco creative-import <项目目录> --file <candidate.json>
adco creative-review <项目目录>
adco creative-quality-gate <项目目录>
adco search-quality-gate <项目目录>
adco reference-pack-gate <项目目录>
adco import-imagegen <项目目录> --slot-id <槽位> --selected
adco visual-quality-gate <项目目录>
adco confirm-client-outline <项目目录> --confirmed-by "<人工确认者>" --confirmed-at <iso_time> --evidence-ref "<user_confirmation:id|client_confirmation:id>"
adco client-outline-gate <项目目录>
adco export-pptx <项目目录>
adco client-language-gate <项目目录>
adco asset-current-manifest <项目目录>
adco visual-layout-gate <项目目录>
adco client-pack-gate <项目目录>
adco client-send-readiness-gate <项目目录>
adco handoff-readiness-gate <项目目录>
adco audit-dashboard <项目目录> --render
adco audit-dashboard <项目目录> --render --json
adco open-dashboard <项目目录> --no-open
adco validate <项目目录>
adco hygiene <项目目录>
```

通过标准：

```text
COUNCIL=PASS
REQUIREMENTS>0
GAPS>0
SEARCH_QUALITY_GATE=PASS 或 PARTIAL_PASS
REFERENCE_PACK_GATE=PASS 或 PARTIAL_PASS
IMAGEGEN_IMPORT_LOG exists
VISUAL_QUALITY_GATE=PASS
CLIENT_OUTLINE_CONFIRMATION=hash-bound 且 CLIENT_OUTLINE_GATE=PASS
PPTX_EDITABLE=PASS
CLIENT_PACK_GATE=PASS
CLIENT_SEND_READINESS_GATE=PASS（仅在本轮确实准备发送，且独立 review/发送授权绑定同一 fresh digest 时要求）
HANDOFF_READINESS_GATE=PASS
DASHBOARD_AUDIT=PASS
DASHBOARD_OPEN=SKIPPED
VALIDATION=PASS
```

`VALIDATION=PASS` 只说明必需文件、CSV/JSON 可解析、产物和 requirement/source/gate 的追溯关系成立；不说明创意方向、审美质量、客户话术或最终客户稿已经被批准。`client-pack-gate` 只到独立人工审阅入口；任何 exact-current 输入变化都会使旧 package digest 过期。只有绑定同一 fresh digest 的人工 review、发送授权和 `client-send-readiness-gate` 全部成立时，才可称为可发送，而且命令本身不会发送。`handoff-readiness-gate` 只代表可内部交接，不能替代这些 Gate。
