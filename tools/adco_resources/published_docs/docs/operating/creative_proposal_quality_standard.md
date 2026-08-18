# Creative Contract and Candidate Quality Standard

用途：把公开行业框架转成 Ad Creative Orchestrator 的 evidence-bound creative contract、候选导入和人工/独立 Critic 复核项。

## 定位

Ad Creative Orchestrator 不是视频生成器、图片生成器、PPT 模板生成器，也不替代创意总监或客户审批。

它负责：

```text
项目控制
资料和参考追溯
creative brief contract 和候选 provenance
质量 Gate
交接和版本归属
```

`creative-brief` 只把当前 evidence chunks、facts、requirements 和 open gaps 冻结为 brief snapshot、contract、candidate schema 与 generation request；它不生成创意方向。

GPT-5.6 Sol 或明确选择的专业 Specialist 负责创意推理：数量服从用户请求；未指定时只生成最小充分集合（1-6 个）。独立 Critic 只在用户明确要求或高后果决策边界启用，负责 brief adherence、insight、brand ownership、mechanism difference、key visual、shootability、production risk 和 brand replacement test；不为流程完整感制造额外候选。

`creative-import` 验证候选结构、manifest/snapshot/provenance 绑定、机制差异、所有落盘声明字段、local workflow assertion 和待人工复核项；parser 生成的 candidate requirement 不会自动升级为硬事实，直接改 CSV 状态也不算确认。local assertion 明确为 `identity_assurance=NONE`，不代表用户/客户身份、批准或发送授权。receipt 的 `candidate_sha256` 绑定精确落盘字节；完整 immutable generation 验证后只原子切换 `current_generation.json`。`creative-review` 重新核对 pointer/generation/import receipt/brief/派生视图，并执行确定性结构/语义/语言 lint；evidence refs 只报告 `PROVENANCE_ONLY`，不声称语义支持。两者都不等于独立创意判断、客户偏好、商业效果或最终发送审批。`creative-proposal` 只是 `creative-brief` 的弃用兼容 alias。

命令：

```text
adco creative-brief <project> [--work-id <id>] [--json]
adco creative-assertion-record <project> --semantics <creative_requirement_confirmation|creative_constraint_approval|creative_constraint_rejection> --requirement-id <id> [--artifact-binding <binding> ...] --note <reason> [--json]
adco creative-requirement-confirm <project> --requirement-id <id> --confirmation-ref <local_operator_assertion:id> [--evidence-ref <chunk>] [--json]
adco creative-constraint-resolve <project> --file <candidate.json> --direction-id <id> --constraint-id <id> --confirmation-ref <local_operator_assertion:id> --decision <approved|rejected> --note <reason> [--json]
adco creative-import <project> --file <candidate.json> [--json]
adco creative-review <project> [--json]
```

## 与 VALIDATION=PASS 的关系

```text
VALIDATION=PASS = 项目结构和追溯关系通过
creative-import = pre-write candidate contract / hard-constraint / exact-byte binding 通过
creative-review = deterministic structure/semantic/language lint，不是独立 Critic
independent Critic = 创意判断与 brand replacement challenge
human/client approval = 人工或客户最终判断
```

这些状态不能互相替代。结构通过不能升级创意质量，Critic 通过也不能把内容直接标成 client-approved。

## 必需输入

运行 creative brief/import/review 前，至少要有：

```text
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/source_events.csv
AD-creative/orchestrator/evidence_chunks.jsonl
AD-creative/orchestrator/fact_inventory.jsonl
AD-creative/orchestrator/artifact_index.csv
参考来源或 search plan
客户/导演/用户待确认项
```

缺少关键客户目标、受众、品牌禁区、投放场景、参考来源或最终决策人时，open evidence gaps 必须保留，不能写 client-ready。候选不能以 assumption 文本代替现有 evidence chunk id。

## Source Mapping

| 来源框架 | 适用场景 | 本地检查项 | 不能复制或声称 |
| --- | --- | --- | --- |
| Cannes Lions Creative Strategy | 策略型 proposal、创意方向页、case rationale | 是否重新解释 challenge；是否有可追溯 insight；是否从 insight 推出 creative idea；是否写清预期 outcome 或结果假设 | 不复制获奖案例措辞；不声称达到 Cannes 标准；没有数据时不声称结果已发生 |
| Cannes Lions Creative Effectiveness | 需要说明效果逻辑、商业目标、客户价值时 | business objective 是否明确；idea 和 strategy 是否连接；是否区分 customer outcome、business impact、sustainable impact；是否标注待验证指标 | 不把效果奖逻辑当作效果证明；不承诺 ROI、销量、增长或长期影响 |
| System1 / Effie Creative Dividend | 判断创意是否有更高传播潜力和长期品牌资产 | 是否有情绪触发；品牌资产是否 distinctive；是否有 showmanship；调性是否一致；是否说明 media support 对结果的影响 | 不复制案例表达；不声称会获得 System1/Effie 分数；不把创意质量和媒介投放混为一个因果结论 |
| Think with Google / Google Ads ABCDs | 广告片、短视频、数字广告执行检查 | Attention 是否在开头建立；Branding 是否早且清晰；Connection 是否和受众/产品场景相关；Direction 是否给出明确行动或下一步 | 不把 ABCD 当作创意公式；不保证平台表现；不把执行检查替代策略洞察 |
| TikTok Creative Codes / best practices | TikTok、抖音类平台的短视频和社交内容方向 | 是否 platform-native；trend 是否作为叙事模板而非贴标签；生产基础是否清楚；是否有多版本 testing plan | 不照搬创作者或热门梗；不声称会 viral；不把 trend 套用到不相关品牌语境 |
| LinkedIn / WARC / LIONS B2B Effectiveness Code | B2B、企业服务、复杂采购链路 | 是否有 creative commitment；是否平衡 long/short；是否写明 effects ladder；是否按 B2B 决策链和购买周期调整 | 不用消费品逻辑硬套 B2B；不声称已影响 pipeline、revenue 或品牌健康度，除非有证据 |
| Ipsos / Effie trends | 前期策略、消费者研究、winning-work 复盘映射 | objective 是否清楚；消费者/市场/品牌研究是否前置；假设和证据是否分开；缺口是否进入 gaps / questions | 不编造 consumer insight；不把趋势观察写成客户事实；不把未验证研究当作真实调研结论 |

## Local Gate Checklist

独立 Critic 加上 `creative-import` / `creative-review` 至少检查：

```text
brief_snapshot_sha256 是否仍是 exact current
每个方向是否绑定现有 evidence chunk
insight 是否能从 brief evidence 推导，而不是复述 brief
请求范围内的保留方向是否具有不同的 creative mechanism
why_brand_can_own_it 是否能通过品牌替换测试
key visual 是否清楚，story/behavior 是否可拍
production risk 是否具体
是否标注 borrowed / do_not_copy / avoid-copy 边界
proposal 是否保留 story、segment summary、brand mapping、timing、key dialogue 或 key phrase
是否列出客户/导演/用户必须确认的问题
是否区分 internal draft、client review draft、client-approved
是否说明哪些任务应路由到其他模块
是否规避 humanizer 写作风险：chatbot 残留、模糊权威、夸大意义、not-only/but 公式、破折号堆叠、泛化 AI 词汇
```

通过不代表：

```text
客户已批准
创意总监已认可品味
视觉资产已可客户可见
视频、分镜或 image prompt 已可生产
PPT/DOCX/XLSX 固定模板已生成
效果结果已经发生
```

## Module Routing

| 需求 | 归属模块 | adco 责任 |
| --- | --- | --- |
| 创意推理与按需候选 | GPT-5.6 Sol 或专业 Specialist | 提供 brief contract、证据边界和动态数量 schema |
| 1-6 个请求内候选、option matrix | ADCO import/control plane | 验证硬约束、证据、机制差异、版本和 provenance |
| 视频脚本、分镜、导演阐述、视频 prompt | `dircreative` 或专门 film workflow | 通过 Specialist Exchange 写清需求、证据和交付边界，再独立采用 |
| image / KV / 背景图 / moodboard / visual asset | `imagegen` 或 Creative Production | 生成 image job spec、导入 asset、跑 visual-quality-gate |
| 固定 PPT / DOCX / XLSX 模板和版式系统 | Template Creator 或专门文档模板流程 | 输出内容结构、字段、追溯关系、审阅 Gate |

ADCO 可以起草 brief contract、检查来源、导入候选、登记结果和维护版本；不要把确定性模板或 lint 描述成完整创意、视频、图片或固定模板生成引擎。

## Film / Director Mode Acceptance

导演阐述必须先成为客户可读 treatment，再展开技术镜头表。最低可接受内容：

```text
一句导演命题
受众前后状态变化
品牌或产品不可替换的因果角色
逐段 cause -> visible action -> effect
空间、时间、材质、身体、物件和 UI 的世界规则
摄影、调度、表演、声音与剪辑为什么服务叙事
每个关键效果的实拍 / 合成 / 模拟边界
关键资产、场地、界面或预算失效时的 Plan B
参考片只借鉴什么、禁止复制什么
```

镜头表的每一行必须包含 `story_function`、`causal_input`、`visible_action`、`causal_output`、`physical_space`、`capture_method`、`brand_or_product_role`、`risk` 和 `fallback`。只有氛围词、漂亮构图、镜头焦段或技术术语，不算完成。

Film Gate 还执行四个反证：去掉品牌后故事是否仍原样成立；相邻镜头是否真的互为因果；人物、物件、界面和材质是否遵守同一物理世界；关键制作条件失败后核心承诺是否仍可拍。任一项无法回答时保持 `BLOCKED`，专业 Specialist 的 `completed` 或 domain QA 不能替代 ADCO 独立采用判断。

## Humanized Writing Rules

Proposal、copy、客户交接和 Gate 输出要具体、短句、可追溯。优先写事实、选择理由、风险和下一步动作。

避免：

```text
当然/希望这有帮助/请告诉我
专家认为/行业报告显示/数据显示但没有 source id
标志着/至关重要/重塑格局/关键转折
not only...but / 不止于...更是
连续使用 em dash / en dash / -- 造节奏
seamless / vibrant / pivotal / underscore / showcase / 格局 / 赋能 / 焕新
```

允许保留专业术语，但每个重要判断要落到客户目标、受众阻力、产品利益、参考来源或待确认问题。

## Approval Wording

允许：

```text
internal proposal draft
client review draft
quality gate passed for structure and traceability
ready for human creative review
ready for specialist handoff
```

禁止：

```text
client-approved
final creative quality approved
guaranteed effective
Cannes/Effie/System1-level
ready to send without human review
visual assets approved for client use
```
