# 非开发者快速开始

目标：广告创意负责人不用理解代码、CSV、Python 结构，也能启动、查看、推进项目。

## 1. 准备资料

把资料放到真实项目目录：

```text
00_项目资料_ProjectMaterials/
```

可以是客户 brief、会议记录、导演意见、客户反馈、参考链接整理。

## 2. 启动项目

最简单方式：

```text
双击 /Users/jinjungao/work/ad-creative-orchestrator/启动广告创意项目.command
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

产物：

```text
AD-creative/handoff/操作台.html
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/客户追问话术.md
AD-creative/ppt/client_review_draft.pptx
AD-creative/ppt/ppt_editability_check.md
AD-creative/gates/GATE-AUTO-CLIENT-PACK-001_report.md
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/profile_knowledge/profile_current_truth.md
AD-creative/handoff/画像分析简报.md
AD-creative/gates/THREE-COUNCIL-READINESS_report.md
AGENTS.md
```

`AGENTS.md` 在项目根目录。它不是客户稿，而是给 Codex 线程看的项目规则：先读哪些文件、哪些事必须停下来确认、哪些 Gate 必须跑、`VALIDATION=PASS` 不能当作客户创意质量批准。

如果项目里已经有 `AGENTS.md`，初始化不会覆盖。保留原有规则；如果生成 `AD-creative/orchestrator/AGENTS.merge_suggestion.md`，把里面的 Ad Creative Orchestrator 项目规则人工合并进根目录 `AGENTS.md`。
合并建议会写到：

```text
AD-creative/orchestrator/AGENTS.merge_suggestion.md
```

如果根目录 `AGENTS.md` 缺失或没有合入必需规则，`adco validate` 会返回 `CHECK`。

adco 的创意方案定位：

```text
adco creative-proposal <项目目录> [--work-id <id>] [--json]
adco creative-quality-gate <项目目录>

creative-proposal 起草 internal creative proposal：challenge、insight、creative idea、proposal structure、证据映射和客户待确认项。
creative-quality-gate 只检查 proposal 草稿的结构、追溯、证据和专业完整度。
证据稀疏、来源未闭合或关键假设未确认时，可以是 PARTIAL_PASS / BLOCKED。
它不批准审美、不代表客户喜欢、不保证商业效果，也不能替代客户或创意负责人确认。
视频/分镜/video prompt 交给 dircreative。
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
AD-creative/ppt/ppt_editability_check.md
```

生成图入库：

```text
adco import-imagegen <项目目录> --slot-id <槽位> --selected
```

用途：

```text
从 CODEX_HOME/generated_images 取最近一张生成图，复制到 AD-creative/visual_assets/selected/，登记 asset_manifest.csv，写 imagegen_import_log.md，刷新操作台。
默认 internal_only；客户可见前必须另跑 Gate 并人工确认。
```

Goal 模式执行：

```text
adco goal-plan <项目目录> --title <目标标题> --objective <目标内容>
adco thread-plan <项目目录> --title <目标标题> --objective <目标内容> --roles brand_client,copy_creative,qa_review
```

`thread-plan` 只给 Codex 主控生成内部线程分工包，不会自动发送客户稿。后续 Gate 如果没有有效反驳性议会记录，最高只会给 `PARTIAL_PASS`。

Thread 执行规则：

```text
主控线程只负责拆分、分派、集成、验证、清理、汇报。
execution_worker 负责明确范围内的实现、文档修改、素材和产物制作。
read_only 只用于 explorer / reviewer / research / cold-review。
execution_worker 必须先写清 exact write_scope。
每个 execution_worker 返回 files_changed、validation、dirty-state impact、cleanup actions。
主控消费 receipt 并合并后，归档对应 worker thread。
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
继续执行 ad-creative:next
读取 AD-creative/handoff/项目看板.md 和 AD-creative/handoff/待你确认.md
优先完成需求整理、缺口判断、客户追问、下一步建议
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
adco creative-proposal <项目目录>
adco creative-quality-gate <项目目录>
adco search-quality-gate <项目目录>
adco reference-pack-gate <项目目录>
adco import-imagegen <项目目录> --slot-id <槽位> --selected
adco visual-quality-gate <项目目录>
adco export-pptx <项目目录>
adco client-pack-gate <项目目录>
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
PPTX_EDITABLE=PASS
CLIENT_PACK_GATE=PASS
HANDOFF_READINESS_GATE=PASS
DASHBOARD_AUDIT=PASS
DASHBOARD_OPEN=SKIPPED
VALIDATION=PASS
```

`VALIDATION=PASS` 只说明必需文件、CSV/JSON 可解析、产物和 requirement/source/gate 的追溯关系成立；不说明创意方向、审美质量、客户话术或最终客户稿已经被批准。客户可见前还要看 `creative-quality-gate`、`search-quality-gate`、`reference-pack-gate`、`visual-quality-gate`、`client-pack-gate`、`handoff-readiness-gate`，并做人工确认。
