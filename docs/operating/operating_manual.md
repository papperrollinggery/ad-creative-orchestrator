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
AD-creative/ppt/client_review_draft.pptx
AD-creative/ppt/ppt_editability_check.md
AD-creative/gates/THREE-COUNCIL-READINESS_report.md
```

检查状态：

```text
adco status <项目目录>
```

创建 goal 执行记录：

```text
adco goal-plan <项目目录> --title <目标标题> --objective <目标内容>
```

该命令会写入：

```text
AD-creative/orchestrator/goal_iterations/<goal_id>.md
```

Gate 规则：

```text
reference-pack-gate / search-quality-gate / visual-quality-gate / client-pack-gate / handoff-readiness-gate
若缺少有效反驳性议会记录，PASS 会自动降级为 PARTIAL_PASS。
```

重新抽取 intake：

```text
adco intake <项目目录>
```

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
客户可见前仍需视觉 Gate 和明确确认。
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
客户可见生成图缺少 client_visibility_approved 记录
客户可见图仍是 contact sheet / placeholder-only / 假 logo / 低质拼贴
```

生成并检查可编辑 PPTX：

```text
adco export-pptx <项目目录>
adco check-pptx <项目目录> --file <PPTX文件>
```

客户稿风险 Gate：

```text
adco client-pack-gate <项目目录>
```

通过含义：

```text
PPTX 有可编辑文本层
客户可见产物都过 Gate
客户可见图片都 QA PASS
客户可见参考都是 https 且有 do_not_copy
客户可见文本候选不含内部注释、模拟标记、TODO/TBD、假 logo
```

不代表：

```text
可以自动发送客户稿
已经完成最终人工审稿
已经确认 AI 图客户可见
```

非开发者交接 Gate：

```text
adco handoff-readiness-gate <项目目录>
```

通过含义：

```text
adco validate 通过
操作台可生成且通过审计
三方议会 PASS
搜索/参考/视觉/客户包 Gate 不阻塞内部交接
PPTX 可编辑
双击启动脚本可执行
全局 Skill 已安装且和项目草稿哈希一致
生成 manual_review_checklist.md 供真实客户稿发送前人工复核
```

安装全局 Skill：

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
判断是否需要搜索
推进到安全的下一步
遇到必须人工决策就停
运行 adco validate
```

### ad-creative:start

启动或恢复项目。

Codex 必须读取：

```text
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
