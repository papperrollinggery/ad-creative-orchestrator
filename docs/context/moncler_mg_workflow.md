# 广告创意工作流：Moncler × 晨光融合版

目标：把广告创意从需求输入推进到客户可审方案，并保留可继续生产的资产、分镜、PPT 和审核记录。

## 1. 需求锁定

输入文件：

- `brief.md`
- `source_assets/`
- `client_feedback.md`
- `reference_links.md`

必须先锁：

- 项目类型：TVC / KV / Campaign / 官宣片 / 平台物料
- 交付物：HTML 样稿、PPTX、PDF、分镜、脚本、素材包
- 时长 / 画幅 / 平台：16:9、9:16、4:5、横竖版
- 产品范围：主推产品、辅助产品、禁用产品
- 人物限制：单人 / 多人 / 艺人形象 / 服装
- 客户硬性要求：主题、文案、禁区、截止时间
- 当前版本状态：草案 / 可审 / 待返工 / 最终版

输出：

- `00_README/current_truth.md`
- `00_README/client_constraints.md`
- `00_README/no_go_list.md`

## 2. 品牌、产品、人物研究

Moncler 逻辑：先拆品牌 DNA、视觉代码、产品质感、官方参考。

晨光逻辑：把艺人特质、粉丝共情、产品日常角色翻译成画面方法。

输出：

- `01_research/brand_dna.md`
- `01_research/product_role.md`
- `01_research/talent_insight.md`
- `01_research/platform_context.md`
- `01_research/reference_shortlist.md`

判断标准：

- 不写百科
- 不写空泛人群画像
- 每条洞察必须能落到画面、动作、声音或产品露出

## 3. 创意系统锁定

结构：

```text
一个总命题
两个方向
每个方向两个场景世界
每个方向一条记忆句
每个方向一套产品露出逻辑
```

示例结构：

```text
总命题：美好，是把每天认真过完

OP1：日复一日的沉淀
场景：教室 + 练功房
产品：笔写下计划，本子承载复盘

OP2：始终如初的热爱
场景：卧室/书房 + 小舞台
产品：笔写下约定，本子保存初心
```

输出：

- `02_strategy/creative_platform.md`
- `02_strategy/options_matrix.md`
- `02_strategy/message_lines.md`

## 4. 故事线与分镜骨架

每条方向按时间拆，不先写大段文案。

标准结构：

```text
0-3s：产品/空间钩子
3-8s：人物状态建立
8-20s：动作推进 / 双场景交叉
20-28s：情绪完成
28-30s：品牌收束
```

每个镜头必须写：

- 时间
- 场景
- 景别
- 人物动作
- 产品位置
- 旁白 / 字幕
- 声音锚点
- 裁切安全区

输出：

- `03_story/storyline.md`
- `03_story/shot_table.csv`
- `03_story/voiceover.md`

## 5. 视觉系统与资产规划

Moncler 逻辑：不做随机图片，先定 master scene，再派生 storyboard / mockup / platform crop。

晨光逻辑：每张图必须服务分镜思考，覆盖空间、光线、景别、机位、产品、动作。

输出：

- `04_visual/master_scene_matrix.md`
- `04_visual/moodboard_plan.md`
- `04_visual/prompt_pack.md`
- `04_visual/ratio_spec.md`

资产分类：

- Hero / KV
- Scene moodboard
- Storyboard frame
- Product close-up
- BTS / detail
- Platform crop
- PPT background

## 6. 生图与素材包

目录结构：

```text
05_assets/
  raw/
  selected/
  rejected/
  notes/
  prompts/
  reference/
```

每张图必须登记：

- `asset_id`
- `direction`
- `scene`
- `shot_id`
- `ratio`
- `source_path`
- `status`
- `review_status`
- `use_case`
- `notes`

输出：

- `05_assets/asset_manifest.csv`
- `05_assets/rejection_log.csv`
- `05_assets/prompt_manifest.csv`

禁区：

- 假 logo
- 假包装字
- AI 水印
- 变形人脸 / 手指
- 拉伸图片
- contact sheet 直接进客户稿
- 未登记图片直接进 PPT

## 7. 客户可审样稿

晨光逻辑优先：先做 HTML 样稿，客户确认结构、文案、图片、节奏后，再转可编辑 PPTX。

HTML 样稿页序：

1. 封面
2. 目录
3. Brief 边界
4. 品牌 × 人物洞察
5. 双方向总览
6. 场景对比
7. OP1 概念
8. OP1 故事结构
9. OP1 Moodboard
10. OP1 摄影参考
11. OP2 概念
12. OP2 故事结构
13. OP2 Moodboard
14. OP2 摄影参考
15. 平台传播语境
16. 产品角色
17. 视频参考 / 命名参考
18. 推荐执行

输出：

- `06_sample/index.html`
- `06_sample/screenshots/`
- `06_sample/html_review.md`

## 8. QA 门禁

Moncler 逻辑：每一步有 Gate，不靠聊天记忆。

Gate：

- Brief Gate：需求、产品、人物、平台、禁区明确
- Strategy Gate：总命题、双方向、画面方法成立
- Story Gate：每条片 30 秒内，节拍清楚
- Visual Gate：图片服务分镜，不是装饰
- Asset Gate：selected 全部登记
- HTML Gate：无缺图、无溢出、无内部注释
- PPT Gate：文字、logo、表格、平台 UI 可编辑
- Final Gate：PPT、素材包、manifest、QC、handoff 完整

输出：

- `07_qc/review.md`
- `07_qc/html_render_check.md`
- `07_qc/ppt_layer_checklist.csv`

## 9. PPT 生产

只在 HTML 确认后开始。

规则：

- 不把 HTML 整页截图塞进 PPT
- 图片保持比例
- 文字、logo、表格、平台 UI 保持可编辑
- 只使用 `asset_manifest.csv` 中 selected / pass 的资产
- 保留 PPT 源素材目录

输出：

- `08_ppt/editable_pptx/`
- `08_ppt/pdf_preview/`
- `08_ppt/page_exports/`
- `08_ppt/source_assets/`

## 10. 客户反馈合并

晨光 V8/V9 逻辑：客户反馈不是简单改字，而是合并优势方向。

处理方式：

```text
客户反馈
-> 拆成内容 / 视觉 / 文案 / 产品 / 交付格式
-> 标记 Must / Should / Maybe / Reject
-> 更新 current_truth
-> 只改受影响文件
-> 出修改对应表
```

输出：

- `09_feedback/client_feedback_table.md`
- `09_feedback/revision_plan.md`
- `09_feedback/change_log.md`

## 11. 最终交付包

目录：

```text
10_delivery/
  final_pptx/
  final_pdf/
  client_report/
  speaker_notes/
  asset_manifest.csv
  source_assets/
  qc/
  handoff.md
```

最终必须回答：

- 方案是否可审
- PPT 是否可编辑
- 素材是否独立归档
- 哪些图可正式使用
- 哪些资产只是参考
- 下一步缺什么真实素材

## 12. Codex 执行模式

推荐分工：

- 主控：维护 `current_truth`、合并产物、最终 QA
- Research：品牌 / 产品 / 参考视频
- Copy：故事线 / 旁白 / 页面文案
- Visual：prompt / 生图 / moodboard
- Asset：manifest / 资产登记
- PPT：可编辑 PPTX
- QA：只审核，不覆盖主文件

硬规则：

- 主控文件永远优先于聊天记忆
- 旧版本不覆盖，进入 archive
- 未过审资产不得进入客户稿
- 客户可见稿不出现内部说明
- 每轮输出必须能继续被下一个 agent 接手

