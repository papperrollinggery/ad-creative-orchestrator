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
```

可从这里复制：

```text
/Users/jinjungao/work/ad-creative-orchestrator/templates/project/
```

或运行：

```text
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/init_project.py <真实项目路径>
```

## 1. 放入资料

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
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py run <真实项目路径> --material <资料文件或文件夹>
```

然后打开：

```text
AD-creative/handoff/操作台.html
```

最短方式：

```text
使用 /Users/jinjungao/work/ad-creative-orchestrator/skill_drafts/ad-creative-orchestrator/SKILL.md

ad-creative:run

项目目录：
<填真实项目路径>

资料位置：
<填客户资料/会议记录/反馈所在文件夹或文件>

本轮目标：
先完成需求整理、缺口判断、客户追问、下一步建议。公开官方来源搜索可在三方议会 PASS 后自动推进；AI 图客户可见、客户稿发送、付费/登录/上传资料前必须停。
```

展开方式：

给 Codex：

```text
使用 /Users/jinjungao/work/ad-creative-orchestrator/skill_drafts/ad-creative-orchestrator/SKILL.md

ad-creative:start

项目目录：
<填真实项目路径>

要求：
1. 先读取 AD-creative/orchestrator/ 和 AD-creative/handoff/。
2. 如果是新项目，按模板初始化缺失文件。
3. 不做创意生产。
4. 只输出当前状态、缺失文件、下一步建议。
```

## 3. 添加资料 Prompt

```text
ad-creative:add-materials

新增资料位置：
<填资料路径>

资料语义：
initial / supplement / change / feedback / approval / rejection / unknown

要求：
1. 登记 source event。
2. 抽取 requirements / gaps。
3. 判断是否需要搜索。
4. 如果需要客户/导演/我确认，写入 待你确认.md。
5. 输出客户追问话术。
6. 不直接开始创意生产。
```

## 4. 推进 Prompt

```text
ad-creative:next

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
使用 /Users/jinjungao/work/ad-creative-orchestrator/skill_drafts/ad-creative-orchestrator/SKILL.md

以 goal 模式推进。

要求：
1. 先读取 docs/operating/dual_lane_goal_delivery_workflow.md。
2. 复制 templates/project/AD-creative/orchestrator/goal_iteration_plan_template.md 作为本轮执行记录。
3. 按品牌深度研究 / 图片功能双泳道拆阶段。
4. 每阶段写输入、产出、依赖、退出条件、下一阶段。
5. 每个 Gate 前运行反驳性议会。
6. 没有反对意见、反驳路径、修订决议时，Gate 最高只能 PARTIAL_PASS。
7. 阶段完成后更新 gate_log / decisions / resolutions / 项目看板 / 待你确认。
8. 运行 `adco validate` 或 `ad_creative_operator.py validate` 后再报告结果。
```

## 5. 状态 Prompt

```text
ad-creative:status

只读，不推进。

输出：
项目阶段
卡点
待确认
最近产物
下一步建议
```

## 6. Gate Prompt

```text
ad-creative:gate

Gate 类型：
Brief Gate / Research Gate / Creative Gate / Visual Plan Gate / Visual Review Gate / HTML Gate / PPT Gate / Final Gate / Skill Mining Gate

检查对象：
<填 artifact 或 stage>

要求：
1. 只审核，不直接改稿。
2. 输出 PASS / PARTIAL_PASS / REVISE / BLOCKED。
3. 写 gate report。
4. 更新 gate_log / artifact_index / work_items / 项目看板。
```

## 7. Skill Mining Prompt

```text
ad-creative:mine-skill

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
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py council <真实项目路径> --render-dashboard
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py validate <真实项目路径>
```

通过标准：

```text
COUNCIL=PASS
ERRORS=0
VALIDATION=PASS
```

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
adco validate / ad_creative_operator.py validate 是否 PASS
tools/test_goal_workflow.py 是否 PASS
```
