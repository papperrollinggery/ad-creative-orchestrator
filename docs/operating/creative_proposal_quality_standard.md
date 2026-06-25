# Creative Proposal Quality Standard

用途：把公开行业框架转成 Ad Creative Orchestrator 的本地检查项，用于策略方向、创意方案草稿、客户审阅包前的内部质量控制。

## 定位

Ad Creative Orchestrator 不是视频生成器、图片生成器、PPT 模板生成器，也不替代创意总监或客户审批。

它负责：

```text
项目控制
资料和参考追溯
策略/创意 proposal 内部草稿
质量 Gate
交接和版本归属
```

`creative-proposal` 是工作流和 CLI 命令：指内部策略和创意 proposal 草稿，包括 challenge interpretation、insight、creative idea、option matrix、message line、proposal structure、证据映射和客户待确认项。命令输出默认仍是 internal draft。

`creative-quality-gate` 是独立 Gate 和 CLI 命令：检查 proposal 的结构、证据、专业完整度、可追溯性和风险边界。它不同于 `adco validate`；也不等于创意品味、客户偏好、商业效果或最终发送审批。

命令：

```text
adco creative-proposal <project> [--work-id <id>] [--json]
adco creative-quality-gate <project>
```

## 与 VALIDATION=PASS 的关系

```text
VALIDATION=PASS = 结构和追溯关系通过
creative-quality-gate = proposal 草稿的策略/创意/专业完整度检查
human/client approval = 人工或客户最终判断
```

三者不能互相替代。`VALIDATION=PASS` 不升级 proposal 的创意质量；`creative-quality-gate=PASS` 也不能把内容直接标成 client-approved。

## 必需输入

运行 proposal 草稿或质量 Gate 前，至少要有：

```text
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/source_events.csv
AD-creative/orchestrator/artifact_index.csv
参考来源或 search plan
客户/导演/用户待确认项
```

缺少关键客户目标、受众、品牌禁区、投放场景、参考来源或最终决策人时，只能输出 draft / PARTIAL_PASS / BLOCKED，不能写 client-ready。
证据稀疏、来源未闭合或关键假设未确认时，`creative-quality-gate` 应返回 PARTIAL_PASS 或 BLOCKED。

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

`creative-quality-gate` 至少检查：

```text
challenge 是否被准确解释，而不是复述 brief
insight 是否绑定 source_event / reference / research note
creative idea 是否能从 insight 推导出来
每个 claim 是否能追溯到 requirement 或 reference
是否标注 borrowed / do_not_copy / avoid-copy 边界
proposal 是否保留 story、segment summary、brand mapping、timing、key dialogue 或 key phrase
是否列出客户/导演/用户必须确认的问题
是否区分 internal draft、client review draft、client-approved
是否说明哪些任务应路由到其他模块
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
| 策略方向、创意 proposal、option matrix、message line、proposal structure | adco | 组织草稿、证据映射、Gate、版本和 handoff |
| 视频脚本、分镜、导演阐述、视频 prompt | `dircreative` 或专门 film workflow | 写清需求、证据、交付边界，再移交 |
| image / KV / 背景图 / moodboard / visual asset | `imagegen` 或 Creative Production | 生成 image job spec、导入 asset、跑 visual-quality-gate |
| 固定 PPT / DOCX / XLSX 模板和版式系统 | Template Creator 或专门文档模板流程 | 输出内容结构、字段、追溯关系、审阅 Gate |

adco 可以起草 brief、检查来源、登记结果和维护版本；不要把它描述成实际视频、图片或固定模板的生成引擎。

## Wording Rules

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
