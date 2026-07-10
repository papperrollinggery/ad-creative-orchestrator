# 操作手册

状态：v0 可操作版本

## 使用边界

这是 Codex-first 工作流。

```text
Codex 负责判断和执行
项目文件负责事实源
handoff 文件负责给用户看
本地操作台负责给非开发者看状态和下一步
```

## 用户入口

运行时阶段固定为：`P0 truth/lock → P1 client outline → P2 hash confirmation → P3 creative/reference/neutral specialist → P4 immutable PPT → P5 language/visual/authorization/editability → P6 fresh Client Pack binding → P7 independent review/send readiness（不发送）→ P8 feedback/next version`。P4/P6/P7 不得合并。

### 启动广告创意项目.command

完全不懂命令行时，双击：

```text
/Users/jinjungao/work/ad-creative-orchestrator/启动广告创意项目.command
```

它会弹窗选择项目文件夹、客户资料文件或文件夹、本轮目标，并自动打开：

```text
AD-creative/handoff/操作台.html
```

### adco CLI

非开发者入口。

```text
adco run <项目目录> --material <资料文件或文件夹>
```

自动生成：

```text
AD-creative/handoff/操作台.html
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/客户追问话术.md
AD-creative/client_review/client_review_outline.md
AD-creative/client_review/client_outline.csv
AD-creative/proposal_architecture/proposal_structure.md
AD-creative/gates/THREE-COUNCIL-READINESS_report.md
AGENTS.md
```

检查状态：

```text
adco status <项目目录>
```

创建 goal 执行记录：

```text
adco goal-plan <项目目录> --title <目标标题> --objective <目标内容>
```

`goal-plan` 会写入：

```text
AD-creative/orchestrator/goal_iterations/<goal_id>.md
```

创建 Codex Thread 执行层：

```text
adco thread-plan <项目目录> --title <目标标题> --objective <目标内容> --roles brand_client,copy_creative,qa_review
```

Threads 默认不启用。只有有界隔离、真实并行或独立审阅确有必要时才运行 `thread-plan`。

生成内部创意 proposal 草稿：

```text
adco creative-proposal <项目目录> [--work-id <id>] [--json]
```

运行创意 proposal 质量 Gate：

```text
adco creative-quality-gate <项目目录>
```

双击 launcher 会在 `run` 后生成上述客户可读文本框架，然后停在人工确认前。此时 `client-outline-gate` 会因缺少 hash-bound confirmation 保持 BLOCKED；人工确认并重跑 Gate 前不会自动生成 PPT。

`thread-plan` 会写入：

```text
AD-creative/orchestrator/thread_lane_plan.md
AD-creative/orchestrator/thread_registry.csv
AD-creative/orchestrator/thread_cleanup_<work_id>.md
AD-creative/agents/role_briefs/
AD-creative/agents/thread_prompts/<work_id>/
AD-creative/agents/receipts/<work_id>/
```

执行规则：

```text
主控线程只负责拆分、分派、集成、验证、清理、汇报。
execution_worker 负责明确范围内的实现、文档修改、素材和产物制作。
read_only 只用于 explorer / reviewer / research / cold-review。
execution_worker 必须先写清 exact write_scope。
默认最多 3 个 active worker/reviewer。
每个 execution_worker 返回 files_changed、validation、dirty-state impact、cleanup actions。
主控 dispatch 后保存 host scope baseline；reconcile 时用实际文件 diff 对照 receipt 与 exact write_scope，生成 hash-bound host scope proof。worker 自报不能代替 host proof。
主控读取 receipt 和 host proof 后再决定 adoption/rejection。
合并后归档已消费 worker，并把真实 thread_id / cleanup_action 写回 thread_registry.csv。
固定轮询次数只是检查预算；区分 active_with_progress / silent / finalizing_receipt，最多一次带绝对截止时间的 extension 和一次带独立 dispatch proof/receipt path 的 rescue。
客户可见稿不得出现 prompt、thread、worker、lane plan、执行步骤等内部语言。
```

项目级 AGENTS.md：

```text
新项目根目录会生成 AGENTS.md。
它是给 Codex 线程看的项目规则，不是客户稿。
所有新线程先读 AGENTS.md，再读 AD-creative/orchestrator/ 和 AD-creative/handoff/。
它固定人工停点、客户可见限制、ThreadOps 分工、Gate 顺序和验证边界。
复制或交接项目时必须一起保留。
```

已有文件处理：

```text
adco init 按文件创建缺失模板。
如果目标目录已有 AGENTS.md，不覆盖、不重写。
写出 AD-creative/orchestrator/AGENTS.merge_suggestion.md。
把本项目规则人工合并到现有 AGENTS.md，并保留客户、仓库或团队已有禁区。
未合并必需规则前，adco validate 返回 CHECK。
```

Gate 规则：

```text
adco validate
search-quality-gate / reference-pack-gate / visual-quality-gate / client-pack-gate / handoff-readiness-gate
需要反驳性证据的内容 Gate，若缺少独立 reviewer 对 exact stage target path/hash 的新鲜记录，PASS 会自动降级为 PARTIAL_PASS。`global`、无关目标、BLOCKED、旧 hash 或主线程/goal plan 自审均无效。handoff-readiness 只检查内部运营连续性，不沿用客户交付 Gate 的阻断语义。
每次 Gate 运行追加新的 `gate_run_id` 并引用被替代记录，不覆盖旧结论。
```

创意 proposal 和质量 Gate：

```text
creative-proposal 是工作流和 CLI 命令，不是客户最终稿。
它用于起草 challenge interpretation、insight、creative idea、option matrix、message line、proposal structure、证据映射和客户待确认项。
creative-quality-gate 是独立 Gate 和 CLI 命令，独立于 adco validate。
adco validate 只看结构和追溯；creative-quality-gate 看 proposal 草稿的策略/创意/专业完整度。
creative-quality-gate 通过也不代表创意品味、客户偏好、商业效果或最终发送已经批准。
证据稀疏、来源未闭合或关键假设未确认时，creative-quality-gate 可以是 PARTIAL_PASS / BLOCKED。
详细标准见 docs/operating/creative_proposal_quality_standard.md。
```

模块路由：

```text
策略方向、创意 proposal、option matrix、message line、proposal structure：留在 adco。
视频脚本、分镜、导演阐述、video prompt：通过 `adco.specialist-exchange` 的 `dircreative.film-preproduction` profile 交接；ADCO 不依赖 DIR 仓库路径、包版本或内部 validator。
image / KV / 背景图 / moodboard / visual asset：交给 imagegen 或 Creative Production，回到 adco 登记和 visual-quality-gate。
固定 PPT / DOCX / XLSX 模板和版式系统：交给 Template Creator 或专门文档模板流程，adco 只维护内容结构、字段、追溯和 Gate。
```

重新抽取 intake：

```text
adco intake <项目目录>
```

会议 / 客户画像分析：

```text
adco profile-analyze <项目目录> --source-id <SRC-ID> --brand <品牌> --company <公司>
```

该命令读取已登记的会议记录或客户资料，生成：

```text
AD-creative/orchestrator/profile_knowledge/profile_subjects.csv
AD-creative/orchestrator/profile_knowledge/meeting_voice_map.csv
AD-creative/orchestrator/profile_knowledge/profile_insights.csv
AD-creative/orchestrator/profile_knowledge/profile_conflicts.csv
AD-creative/orchestrator/profile_knowledge/profile_current_truth.md
AD-creative/handoff/画像分析简报.md
```

使用规则：

```text
人物画像、品牌画像、公司画像都必须带 source_event 证据。
决策权和影响力只是 candidate 判断，必须等用户或客户确认后再当稳定事实。
出现分歧时先写入 profile_conflicts.csv，不要硬合并成单一结论。
研究和创意阶段优先读取 profile_current_truth.md，再读取 requirements.csv。
```

工作区整洁检查：

```text
adco hygiene <项目目录>
```

该命令只检查不删除。它会报告 git tracked/untracked 改动、Python 缓存污染、未归档 Thread 记录，并输出清理计划。验证和草稿生成优先用 `/tmp` 或 `AD-creative/workspaces/<work_id>/`，不要把临时产物写到仓库根目录。

操作台审核：

```text
adco audit-dashboard <项目目录> --render
```

登记真实参考链接：

```text
adco add-reference <项目目录> --url <https链接> --title <标题>
```

参考包质量 Gate：

```text
adco search-quality-gate <项目目录>
adco reference-pack-gate <项目目录>
```

判定：

```text
search-quality-gate 检查搜索计划、搜索目标、客户可见边界。
PASS：参考均可内部/客户稿使用。
PARTIAL_PASS：仍有 TBD、来源归属或用途信息缺口，只能内部推进。
BLOCKED：客户可见参考缺少 https、do_not_copy 或来源可信度。
```

登记真实/生成图片文件：

```text
adco add-asset <项目目录> --file <图片文件> --slot-id <槽位> --requirement-id <需求ID> --selected
```

导入 Codex 生成图：

```text
adco import-imagegen <项目目录> --slot-id <槽位> --selected
```

约束：

```text
只读取 CODEX_HOME/generated_images。
导入后复制到 AD-creative/visual_assets/。
默认 internal_only。
客户可见前仍需视觉 Gate，以及绑定 exact asset hash/use scope/确认者/时间/evidence 的独立授权 receipt。
```

视觉质量 Gate：

```text
adco visual-quality-gate <项目目录>
```

会拦截：

```text
缺文件
图片尺寸过低
selected/approved/done 但 QA 未 PASS
生成图缺少 prompt_or_edit_ref
客户可见生成图缺少 `asset_authorizations.csv` 的 hash/scope/approver/time/evidence receipt；`approval=PASS` 或 notes token 不算授权
客户可见图仍是 contact sheet / placeholder-only / 假 logo / 低质拼贴
```

人工确认客户可读文本框架：

```text
adco confirm-client-outline <项目目录> --confirmed-by "<人工确认者>" --confirmed-at <iso_time> --evidence-ref "<user_confirmation:id|client_confirmation:id>"
adco client-outline-gate <项目目录>
```

先审阅文本，再记录 hash-bound confirmation。Receipt 同时保存确认前 exact 文件 hash、排除宿主 `visibility/status` 状态字段的 canonical 内容 digest，以及确认后当前文件 hash；这样宿主落章不会冒充人工已见内容，而任何客户文本变化仍会让确认失效。Gate PASS 前不能进入 PPT builder。

生成并检查不可变可编辑 PPTX：

```text
adco export-pptx <项目目录>
adco check-pptx <项目目录> --file <PPTX文件>
```

`export-pptx` 每次生成新的 `AD-creative/ppt/exports/client_review_vNNN.pptx`，同步 exact current version/artifact/editability hash，并拒绝覆盖已有版本。`check-pptx` 只生成 hash 绑定的诊断报告，不会把任意文件改成 current。

客户稿风险 Gate：

```text
adco client-pack-gate <项目目录>
```

通过含义：

```text
PPTX 有可编辑文本层
客户可见产物都过 Gate
客户可见图片都 QA PASS 且有匹配 asset hash/scope 的独立授权 receipt
客户可见参考都是 https 且有 do_not_copy
客户可见文本候选不含内部注释、模拟标记、TODO/TBD、假 logo
```

不代表：

```text
可以自动发送客户稿
已经完成独立人工审稿
已经确认 AI 图客户可见
```

`client-pack-gate` 最多表示 ready for independent human review。它生成 immutable input manifest 与 `client_pack_binding.json`；任一 exact-current 输入变化都会让旧 package digest 过期。发送准备必须另跑：

```text
adco client-send-readiness-gate <项目目录>
```

它要求 `manual_review_receipt.json` 和 `send_authorization.json` 都绑定 exact current version、PPTX hash 和同一个 fresh package digest，并且只输出 `SEND_EXECUTED=0`，不会发送。

影视专项交接使用中立协议，不直接依赖 DIR 仓库路径：

```text
adco specialist-handoff <项目目录> --work-id <WORK-ID> --profile-id dircreative.film-preproduction --objective "<目标>" --input-artifact <ART-ID> --expected-output film.story_package --descriptor <descriptor.json>
adco specialist-adopt <项目目录> --handoff <handoff.json> --receipt <receipt.json> --decision partial_adopt --reason "<理由>" --map-output <DIR-ID=AD-creative/film/output.md>
```

默认 `inline`，不会自动创建 Thread。兼容 descriptor 可在 `1.x` 独立演进，但必须显式支持 base contract `1.0`；若 profile 声明 required receipt extension，ADCO 会把 exact id/version 写进 handoff acceptance，缺失即拒收。DIRcreative 只给 specialist recommendation/QA；ADCO 独立记录 adoption，且仍独占 current truth、version、PPT、FinalDelivery 和 send readiness。

非开发者交接 Gate：

```text
adco handoff-readiness-gate <项目目录>
```

通过含义：

```text
adco validate 通过
操作台可生成且通过审计
双击启动脚本可执行
全局 Skill 安装状态只作为 warning，不影响项目证据质量
生成 pending 的 manual_review_checklist.md；未勾选清单不得登记 PASS
```

搜索/参考/视觉/客户包 Gate 的缺失或阻塞在这里是内部交接 warning；如果已经声明 exact-current PPTX，则文件必须存在且可编辑。该 Gate 不要求已有 PPT、Client Pack、manual review receipt 或 send authorization，也绝不代表 FinalDelivery/发送就绪。

显式获批后才可安装全局 Skill（这不是 canonical/package parity 的一部分，也不能据此推断当前已同步）：

```text
adco install-skill
```

三方议会审核：

```text
adco council <项目目录> --render-dashboard
```

### ad-creative:run

一条指令跑项目。

输入：

```text
项目目录
资料位置
本轮目标
```

Codex 自动：

```text
初始化缺失模板
登记资料
抽取需求和缺口
更新项目看板和待确认
生成客户追问话术
生成客户可读文本框架并停在 hash-bound 人工确认前；不自动生成 PPT
判断是否需要搜索
推进到安全的下一步
遇到必须人工决策就停
运行 adco validate
```

`adco validate` 只验证结构和追溯关系。`VALIDATION=PASS` 不代表创意质量、审美、客户措辞、AI 图客户可见性或最终发送已经批准；这些必须继续跑对应 Gate 并人工确认。

### ad-creative:start

启动或恢复项目。

Codex 必须读取：

```text
AGENTS.md
AD-creative/orchestrator/project.yml
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/work_items.csv
AD-creative/orchestrator/artifact_index.csv
AD-creative/orchestrator/gate_log.csv
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
```

输出：

```text
项目当前阶段
当前卡点
待确认事项
下一步建议
```

### ad-creative:add-materials

接收客户资料、会议记录、导演组意见、客户反馈。

必须先写：

```text
AD-creative/orchestrator/source_events.csv
AD-creative/orchestrator/events.jsonl
```

再更新：

```text
current_truth.md
requirements.csv
gaps.csv
decisions.csv
resolutions.csv
```

输出给用户：

```text
AD-creative/handoff/客户追问话术.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/项目看板.md
```

### ad-creative:next

默认推进入口。

Codex 必须：

```text
1. 读取 current_truth / work_items / gate_log
2. 判断当前是否有 blocking decision
3. 若无阻塞，创建或推进下一个 work item
4. 若需要专项 agent，生成 handoff packet
5. 若需要人工确认，更新 待你确认.md 并停下
```

### ad-creative:status

只读状态。

不推进项目。

输出：

```text
项目阶段
最近事件
当前 work items
阻塞项
待用户/客户/导演确认
最近产物
下一步
```

### ad-creative:gate

运行阶段审核。

适用：

```text
Brief Gate
Research Gate
Creative Gate
Creative Quality Gate
Visual Gate
HTML Gate
Visual Plan Gate
Visual Review Gate
PPT Gate
Final Gate
Skill Gate
```

必须生成：

```text
AD-creative/gates/<gate_id>_report.md
```

Creative Quality Gate 必须同时读取：

```text
docs/operating/creative_proposal_quality_standard.md
proposal_structure.md / creative_directions.md / option_matrix.csv / message_line_candidates.md 中存在的对应草稿
requirements / source_events / references / gaps
```

审核只把公开行业框架映射成本地检查项；不能复制案例文案，不能声称达到 Cannes / Effie / System1 / Google / TikTok / WARC / Ipsos 的认证或效果水平。

并更新：

```text
gate_log.csv
artifact_index.csv
work_items.csv
项目看板.md
待你确认.md
```

### ad-creative:mine-skill

识别可复用通路。

只生成项目内草稿，不安装。

输出：

```text
AD-creative/skill_drafts/<skill-slug>/SKILL.md
AD-creative/skill_drafts/<skill-slug>/evidence.md
AD-creative/skill_drafts/<skill-slug>/install_request.md
```

## 人工确认规则

三方议会 `PASS` 后可以自动推进：

```text
模板初始化
资料登记
需求提取
缺口初判
内部 work item 拆分
内部 handoff packet 生成
公开官方来源搜索计划
内部 Gate 初检
只读操作台刷新
项目内 Skill 草稿生成
```

必须停下：

```text
客户/导演/用户需求冲突
客户稿发送前
付费、登录、私密账号、KYC、钱包或凭据
上传客户资料到外部平台
覆盖或删除旧版本
将 AI 图标记为客户可见
全局 Skill 安装前
```

## 搜索策略

搜索前必须记录：

```text
为什么需要搜索
搜索解决哪个缺口
建议搜哪些平台
不搜会影响什么
搜索结果进入哪个产物
```

平台路由：

```text
国内品牌：新片场、B站、小红书、抖音、微博、品牌官网、公众号
国外品牌：YouTube、Vimeo、Instagram、TikTok、品牌官网、campaign archive、Behance、Pinterest
导演/制作：新片场、Vimeo、YouTube、导演官网、制作公司官网
PPT/视觉：品牌官网、campaign archive、Behance、设计案例库
```

## 不允许

```text
不把内部注释写进客户稿
不伪造 logo / 包装 / 案例
不把无来源参考冒充真实案例
不覆盖旧版本
不私自升级 client_visible
不自动安装到 ~/.codex/skills
不把客户机密沉淀进 Skill
```

## 验证命令

初始化新项目：

```text
adco init <项目目录>
```

每个关键阶段后运行：

```text
adco validate <项目目录>
```

Goal / Gate 回归测试：

```text
adco check
```

必须通过：

```text
TEST_GOAL_WORKFLOW=PASS
ERRORS=0
VALIDATION=PASS
```

`VALIDATION=PASS` 的含义：

```text
结构完整
CSV 列数正确
JSON / JSONL 可解析
追溯链可连接
必需产物路径存在
```

不代表：

```text
客户创意质量已批准
客户稿可以自动发送
生成图可以客户可见
搜索参考已经足够用于客户稿
最终审美和商业判断已经通过
```

该命令检查：

```text
必需文件
CSV 列数
JSON / JSONL 可解析
work item → requirement / artifact
artifact → work item / requirement / source event / path
agent run → work item / gate
gate → checked artifacts
version → artifact
```
