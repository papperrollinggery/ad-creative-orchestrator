# 视觉审核工作流

状态：方案草案 / 非实现

## 核心判断

控制面只显示视觉审核状态和入口。

真正的视觉审核是独立 Gate：

```text
Visual Review Gate
= Visual QA
+ Creative Fit Review
+ Brand Fit Review
+ Client Visibility Review
+ Asset Trace Review
+ PPT/HTML Usage Review
```

## 视觉审核对象

视觉审核不只看图片好不好看。

它检查这些对象：

```text
reference image / video
moodboard
key visual
mockup
BTS visual
storyboard frame
character design
product / packshot treatment
scene / environment design
PPT main visual design
slide background image
generated image
edited image
client-facing image
```

## 两层审核

### 1. 硬性 QA

结果直接影响能否进入客户稿。

检查项：

```text
是否绑定 requirement
是否绑定 reference / source
是否绑定 asset slot
是否有生成/编辑记录
是否出现假 logo
是否出现假包装字
是否出现不可控文字
是否出现品牌事实错误
是否侵犯客户禁区
是否把内部注释做进画面
是否是 contact sheet / 低质拼贴
是否比例正确
是否分辨率足够
是否构图裁切错误
是否人物/产品/场景漂移
是否可客户可见
是否进入 asset_manifest
```

输出：

```text
PASS
PARTIAL_PASS
REVISE
BLOCKED
```

### 2. 创意视觉评审

结果不只打分，还要给修改建议。

评审维度：

```text
是否符合 brief
是否符合品牌视觉 DNA
是否支撑当前创意方向
是否足够广告化
是否有客户能感知的价值
是否比参考图更有提案意义
是否和文案/故事线/PPT风格一致
是否适合当前阶段
是否需要更强 mood / 更强产品 / 更强人物 / 更强场景
是否需要补参考
是否需要重新生图
```

输出：

```text
主要问题
修改建议
可继续使用的部分
需要替换的部分
需要补充的参考
是否需要用户确认
下一轮 image job spec
```

## 视觉审核角色

不是一个 Agent 说了算。

视觉审核采用小议会：

```text
Visual Director
Brand Reviewer
Creative Reviewer
Production Reviewer
Client-Side Risk Reviewer
PPT Design Reviewer
```

职责：

```text
Visual Director：判断视觉方向和审美质量
Brand Reviewer：判断品牌 DNA、调性、禁区
Creative Reviewer：判断是否服务创意概念和故事
Production Reviewer：判断是否可执行、可生成、可替换
Client-Side Risk Reviewer：判断客户可见风险
PPT Design Reviewer：判断是否适合进入版式系统
```

最终由主控合并成一个 Gate Report。

## 视觉审核产物

每次审核必须生成：

```text
visual_review_report.md
visual_review_matrix.csv
asset_decisions.csv
revision_image_jobs.md
client_visible_flags.csv
```

字段：

```text
asset_id
slot_id
requirement_id
source_reference_id
stage
visibility
qa_status
creative_score
brand_fit_score
execution_score
risk_level
decision
issues
revision_instruction
next_owner
supersedes
```

## 控制面如何呈现

控制面不展示完整审稿长文。

它只展示：

```text
每张图的 Gate 状态
风险数量
是否客户可见
是否绑定 slot
是否缺 reference
是否需要重生图
谁要确认
```

入口位置：

```text
Work item row：显示 Visual Gate chip
Right inspector：显示 Assets / Gate / Run
Asset board：显示图像网格和审核状态
Gate view：显示完整 visual_review_report
Decision rail：只显示需要用户确认的问题
```

## 图像网格视图

视觉审核需要一个 Asset Board。

布局：

```text
左侧：asset filter
中间：image grid
右侧：selected asset inspector
顶部：stage / direction / visibility / gate filter
```

每张图卡只显示：

```text
thumbnail
asset_id
slot
status
risk badge
visibility badge
version
```

选中后 inspector 显示：

```text
用途
绑定需求
绑定参考
生成 prompt / edit instruction
审核问题
修改建议
是否进入 PPT / HTML / client deck
```

## 人工确认点

必须问用户：

```text
主视觉方向取舍
人物/产品/场景资产锁定
客户可见图是否允许使用 AI 生成
是否接受某张图作为 PPT 主视觉参考
是否用某个视觉风格影响整套方案
高风险但可用的图是否保留
```

不必问用户：

```text
低分图淘汰
内部草图标记 rejected
明显假字/假 logo BLOCKED
缺 slot / 缺 reference 的内部退回
生成下一轮 revision image job
```

## 状态回流

视觉审核会改动这些对象：

```text
asset_manifest.csv
work_items.csv
agent_runs.csv
gate_log.csv
artifact_index.csv
项目看板.md
待你确认.md
```

典型回流：

```text
Visual Gate BLOCKED
→ 回到 Image Job Spec / Asset Lock

Visual Gate PARTIAL_PASS
→ 允许进入内部 HTML/PPT 占位
→ 禁止客户可见

Visual Gate PASS
→ 可进入对应 slot
→ 可用于 HTML preview / PPT design reference

Client Visibility PASS
→ 可进入客户稿
```

## 示例

```text
asset_id: IMG-MON-012
slot_id: COVER-KV-01
requirement_id: R-002
source_reference_id: REF-MON-004
stage: PPT main visual
visibility: internal
qa_status: PARTIAL_PASS
creative_score: 8
brand_fit_score: 7
execution_score: 8
risk_level: medium
decision: revise before client
issues:
- zipper detail looks invented
- background feels more tech than alpine luxury
- text area too busy for cover title
revision_instruction:
- simplify background
- remove invented product details
- keep cold alpine lighting
- reserve clean left title zone
next_owner: Image Producer
```

## 结论

视觉审核不是控制面里的一个字段。

它是：

```text
图像资产进入客户稿前的独立 Gate
+ 图像网格审阅
+ 右侧 asset inspector
+ 议会式视觉评审
+ 硬性风险 QA
+ 修改 image job 回流
+ asset_manifest 状态更新
```
