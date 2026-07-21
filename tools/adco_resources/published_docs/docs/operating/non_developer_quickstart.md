# 非开发者快速开始

目标：广告创意负责人不用理解代码、CSV、Python 结构，也能启动、查看、推进项目。

## 1. 准备资料

把资料放到真实项目目录：

```text
00_项目资料_ProjectMaterials/
```

可以是客户 brief、会议记录、导演意见、客户反馈、参考链接整理。

## 2. 启动项目

项目默认先进入 Content Surface：读取资料 → 事实/真实缺口 → 内容判断或内部产物。只有进入客户可见版本、PPT、资产授权、FinalDelivery 或发送准备时，才展开 P0-P8 Delivery Surface。

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
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/orchestrator/evidence_chunks.jsonl
AD-creative/orchestrator/fact_inventory.jsonl
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
AD-creative/orchestrator/current_truth.md
AD-creative/AGENTS.md
```

默认运行只做资料解析、事实/真实缺口更新、内容摘要和受影响范围验证；操作台、Council、Thread、Git、画像分析、Specialist、客户 outline、PPT、Client Pack 和全量 delivery validation 都不会自动执行。需要操作台时显式运行 `adco open-dashboard <项目目录>` 或给 `adco run` 加 `--dashboard`。

`AD-creative/AGENTS.md` 只约束这个广告工作区。它要求先完成广告内容判断，再按风险进入治理，并明确 `VALIDATION=PASS` 不能当作客户创意质量批准。

如果项目根目录已有 `AGENTS.md`，初始化不会覆盖，也不要求人工合并；ADCO 的规则保持在 `AD-creative/AGENTS.md`。

adco 的创意控制定位：

```text
adco creative-brief <项目目录> [--work-id <id>] [--json]
adco creative-requirement-confirm <项目目录> --requirement-id <id> --confirmation-ref <user_confirmation:source_event_id|client_confirmation:source_event_id> [--evidence-ref <chunk>] [--json]
adco creative-constraint-resolve <项目目录> --file <candidate.json> --direction-id <id> --constraint-id <id> --confirmation-ref <user_confirmation:source_event_id|client_confirmation:source_event_id> --decision <approved|rejected> --note <依据> [--json]
adco creative-import <项目目录> --file <candidate.json> [--json]
adco creative-review <项目目录> [--json]

creative-brief 只冻结 evidence/fact/requirement/gap，并生成 brief contract、candidate schema 和 generation request；它不生成创意方向。
GPT-5.6 Sol 或明确选择的专业 Specialist 基于该 contract 按用户要求生成候选；未指定数量时只生成最小充分集合（1-6 个）。只有明确要求或进入高后果决策边界时才加入独立 Critic，再交给 creative-import。
需要把 parser 发现的硬要求用于耐久导入时，只确认对应 requirement：`--confirmation-ref` 必须指向已登记的 typed `user_confirmation` / `client_confirmation` source event；事件的 owner、trust、`creative_requirement_confirmation` 语义、单一证据文件和 exact requirement ID 必须一致，名字字符串或直接改 CSV 都不生效。无法安全机器判断的单个约束，用 creative-constraint-resolve 绑定 typed approval/rejection event；该事件还必须精确绑定 candidate payload、brief、direction 和 constraint，不需要 Council、Thread 或完整 Gate。
creative-import 拒绝无证据、stale/corrupt brief、重复机制、未确认/未裁决的硬要求和实际约束违规；brief manifest、snapshot 自哈希、candidate version/current/import receipt、directions 和 matrix 必须逐字节匹配。`candidate_sha256` 绑定落盘文件的精确字节。evidence refs 只证明来源存在，不证明语义支持。品牌专属性弱会被标记。creative-review 只是确定性结构/语义/语言 lint，不能替代独立 Critic、客户或创意负责人判断。
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

优先看 CLI 返回的 `INTAKE_SUMMARY`（只是资料整理，不是创意成品）和：

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
先读取 AD-creative/AGENTS.md 和真实资料。
再读取与本轮目标直接相关的 current_truth、项目看板和待你确认。
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

不要把下面的 Gate 全部跑一遍。先判断当前交接边界，只使用对应检查：

| 当前要交什么 | 最小通过标准 |
|---|---|
| 内部策略、文案、脚本、分镜或判断 | 内容本身可用；事实/推断/未知分开；没有把真实素材误读成事实 |
| 内部运营交接 | 上述标准；需要时再跑 `adco handoff-readiness-gate` |
| 客户可读 outline | exact outline 经人工确认，再跑 `adco client-outline-gate` |
| 客户可见图片或 PPT | 对应资产授权、语言、视觉布局和可编辑性检查 |
| Client Pack | exact-current 输入绑定后跑 `adco client-pack-gate` |
| 准备发送 | 独立 review 与发送授权绑定同一 fresh digest，再跑 `adco client-send-readiness-gate`；命令本身不会发送 |

`VALIDATION=PASS` 只说明结构和追溯成立，不说明创意方向、审美质量、客户话术或最终客户稿已经被批准。没有触发的交付边界，不需要为了“流程完整”补跑 Gate。
