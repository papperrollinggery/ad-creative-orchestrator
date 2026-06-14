# Ad Creative Orchestrator

[![check](https://github.com/papperrollinggery/ad-creative-orchestrator/actions/workflows/check.yml/badge.svg)](https://github.com/papperrollinggery/ad-creative-orchestrator/actions/workflows/check.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Local-first, Codex-first workflow for advertising creative operations.

It turns messy briefs, references, image assets, PPT drafts, review gates, and client-visible risk into a traceable project folder.

## Quickstart

From GitHub to a working demo:

```bash
git clone https://github.com/papperrollinggery/ad-creative-orchestrator.git
cd ad-creative-orchestrator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
adco --version
adco quickstart /tmp/adco-demo --no-open
adco quickstart /tmp/adco-demo-json --no-open --json
adco status /tmp/adco-demo
adco next /tmp/adco-demo
adco open-dashboard /tmp/adco-demo
adco validate /tmp/adco-demo
adco check
adco release-status
```

Expected:

```text
QUICKSTART=PASS
VALIDATION=PASS
RUN_CHECKS=PASS
```

Open:

```text
/tmp/adco-demo/AD-creative/handoff/操作台.html
```

For a real project:

```bash
adco init <project_dir>
adco run <project_dir> --material <material_file_or_folder>
adco open-dashboard <project_dir>
adco next <project_dir>
```

## What You Get

- `AD-creative/orchestrator/`: structured source of truth for requirements, gaps, work, artifacts, Gates, versions.
- `AD-creative/handoff/`: non-developer dashboard, project board, pending decisions, client question script.
- `adco quickstart`: one-command first run that creates a demo, validates it, opens the dashboard, and prints next steps.
- `adco demo`: one-command local demo with no real client material.
- `adco sample`: deterministic sample project generator.
- `adco run`: register real materials and produce first-pass requirements, gaps, dashboard, and council report.
- `adco status`: show validation, blockers, pending confirmations, and the next action.
- `adco next`: print the next safe action and automation-friendly next status.
- `adco release-status`: summarize local release readiness and remote blockers.
- `adco docs`: print local docs, template, skill draft paths, and quickstart commands.
- Gate commands for references, search, visual assets, PPT/client pack, and non-developer handoff.

## Safety Model

- Client-facing files are never sent automatically.
- External uploads, paid/login/private account actions, global skill installs, and destructive overwrites require explicit human confirmation.
- AI/generated images stay `internal_only` until visual QA and approval evidence exist.
- Clean Gates without adversarial council evidence are downgraded to `PARTIAL_PASS`.

当前目标不是做独立 SaaS，也不是直接安装全局 Skill。

## Why This Exists

广告创意项目最容易失控的地方不是“写几页方案”，而是客户资料、补充反馈、参考来源、AI 图、PPT、客户可见风险在多个版本里互相污染。

Ad Creative Orchestrator 把这些变成本地文件协议和 Gate：

```text
资料 → 需求/缺口 → 参考证据 → 创意方向 → 图片资产 → 客户审阅包 → PPT/Final Gate → 反馈合并
```

所有客户可见内容必须能追溯到 requirement / reference / asset / Gate。

## Demo

<img src="docs/assets/dashboard-desktop.png" alt="Ad Creative Orchestrator desktop dashboard" width="760">

<img src="docs/assets/dashboard-mobile.png" alt="Ad Creative Orchestrator mobile dashboard" width="260">

可复现命令见 `docs/operating/demo_script.md`。

首跑输出见 `docs/assets/first-run-transcript.md`。

## Install

源码安装：

```bash
python3 -m pip install .
```

可用命令：

```bash
adco --help
adco --version
adco doctor
adco doctor --json
adco release-status
adco release-status --json
adco docs
adco docs --json
adco init <项目目录>
adco-init <项目目录>
adco quickstart [项目目录]
adco quickstart [项目目录] --json
adco demo [项目目录]
adco sample <项目目录>
adco support-bundle <项目目录>
adco support-bundle <项目目录> --json
adco open-dashboard <项目目录>
adco audit-dashboard <项目目录> --render --json
adco run <项目目录> --material <资料文件或文件夹>
adco goal-plan <项目目录> --title "<目标标题>" --objective "<目标内容>"
adco goal-run <项目目录> --goal-id latest --max-steps 3
adco creative-doctor
adco creative-run <项目目录> --kind ads --work-id <工作ID> --brief-file <brief.md>
adco import-creative-production <项目目录> --run-dir <run目录> --kind ads --slot-prefix CP
adco status <项目目录>
adco status <项目目录> --json
adco next <项目目录>
adco next <项目目录> --json
adco validate <项目目录>
adco validate <项目目录> --json
adco check
```

兼容入口仍保留：`adco-init`、`adco-check`、`adco-validate`。

未安装时先执行：

```bash
python3 -m pip install .
```

当前目标：

```text
拿到客户资料后，Codex 能稳定完成：
Intake → 缺口判断 → 搜索建议 → 任务拆分 → agent handoff → 参考包 → 创意方向 → 视觉/image_gen 规划 → 视觉审核 → 客户审阅包/SlideSpec → PPT Gate → 反馈合并 → Final Gate → Skill 草稿沉淀
```

## 当前可操作入口

非开发者双击入口：

```text
启动广告创意项目.command
```

会弹出选择框：

```text
选择项目文件夹
选择资料文件或资料文件夹
填写本轮目标
自动打开 AD-creative/handoff/操作台.html
```

命令行入口：

```text
adco run <项目目录> --material <资料文件或文件夹>
```

它会自动：

```text
初始化项目结构
登记资料
抽取 requirements / gaps / current_truth
生成项目看板 / 待确认 / 客户追问
生成 AD-creative/handoff/操作台.html
生成可编辑 PPTX 草稿并检查可编辑文本层
运行三方议会 readiness 审核
运行 `adco validate`
```

项目本地 Skill 草稿：

```text
skill_drafts/ad-creative-orchestrator/SKILL.md
```

项目模板：

```text
templates/project/
```

Moncler 文件流样例：

```text
examples/moncler_protocol_dry_run/
```

模拟真实客户项目：

```text
examples/simulated_qingling_outdoor_launch/
```

操作手册：

```text
docs/operating/install.md
docs/operating/demo_script.md
docs/operating/github_release_checklist.md
docs/operating/adoption_patterns.md
docs/operating/operating_manual.md
docs/operating/dual_lane_goal_delivery_workflow.md
docs/operating/dual_lane_goal_optimization_plan.md
docs/operating/open_source_release_plan.md
```

真实项目启动 runbook：

```text
docs/operating/non_developer_quickstart.md
docs/operating/first_real_project_runbook.md
docs/operating/real_project_acceptance_criteria.md
docs/operating/authorization_policy.md
```

可操作性审核：

```text
docs/reviews/non_developer_handoff_readiness_review.md
docs/reviews/operational_readiness_review.md
docs/reviews/simulated_project_trial_review.md
```

GitHub 协作：

```text
.github/workflows/check.yml
.github/ISSUE_TEMPLATE/
.github/pull_request_template.md
```

验证与操作工具：

```text
adco check
adco --version
adco doctor --json
make check
make dist-check
make release-check
make package-smoke
adco doctor
adco support-bundle <项目目录>
adco support-bundle <项目目录> --json
adco open-dashboard <项目目录> --no-open
adco init <项目目录>
adco demo <项目目录> --no-open
adco status <项目目录> --json
adco validate <项目目录>
adco validate <项目目录> --json
adco sample <项目目录>
adco status <项目目录>
adco goal-plan <项目目录> --title <目标标题> --objective <目标内容>
adco intake <项目目录>
adco add-reference <项目目录> --url <https链接> --title <标题>
adco search-quality-gate <项目目录>
adco reference-pack-gate <项目目录>
adco add-asset <项目目录> --file <图片文件> --slot-id <槽位> --requirement-id <需求ID>
adco import-imagegen <项目目录> --slot-id <槽位> --selected
adco creative-doctor
adco creative-run <项目目录> --kind moodboard|ads|shots --work-id <工作ID> --brief-file <brief.md>
adco import-creative-production <项目目录> --run-dir <run目录> --kind moodboard|ads|shots --slot-prefix CP
adco visual-quality-gate <项目目录>
adco film-quality-gate <项目目录>
adco export-pptx <项目目录>
adco check-pptx <项目目录> --file <PPTX文件>
adco client-pack-gate <项目目录>
adco handoff-readiness-gate <项目目录>
adco install-skill
adco audit-dashboard <项目目录> --render
adco audit-dashboard <项目目录> --render --json
adco council <项目目录> --render-dashboard
adco-check
adco-init <项目目录>
adco-validate <项目目录>
```

## 推荐使用方式

最短方式：

```text
ad-creative:run

项目目录：<真实项目路径>
资料位置：<客户资料/会议记录/反馈所在文件夹或文件>
本轮目标：先完成需求整理、缺口判断、客户追问、下一步建议
```

在 Codex 中引用本地 Skill 草稿：

```text
使用 /Users/jinjungao/work/ad-creative-orchestrator/skill_drafts/ad-creative-orchestrator/SKILL.md
按 ad-creative:start 继续
```

Goal 模式推进：

```text
先读 docs/operating/dual_lane_goal_delivery_workflow.md
再复制 templates/project/AD-creative/orchestrator/goal_iteration_plan_template.md
按品牌深度研究 / 图片功能双泳道填写本轮 goal
每个阶段 Gate 前必须跑反驳性议会
没有反对意见、反驳路径、修订决议时，Gate 最高只能 PARTIAL_PASS
```

如果是新广告项目：

```text
1. 双击：启动广告创意项目.command
2. 把客户资料放入 00_项目资料_ProjectMaterials/
3. 打开 AD-creative/handoff/操作台.html
4. 把 AD-creative/handoff/客户追问话术.md 发给客户或内部负责人
5. 让 Codex 继续执行 ad-creative:next
```

## 当前验收标准

```text
不看 UI，也知道项目卡在哪里
不复制长 prompt，也能继续下一步
换一个 Agent，也能读 handoff 接着做
新增客户反馈后，旧版本不会污染新版本
每个视觉资产能追溯到 requirement / reference / slot / Gate
每个客户可见项先经过 visibility / Gate 判断
Skill 草稿只在项目内生成，不自动安装
```

## 当前验证状态

```text
examples/moncler_protocol_dry_run: VALIDATION=PASS
examples/simulated_qingling_outdoor_launch: VALIDATION=PASS
临时真实资料压力测试: INTAKE_REQUIREMENTS>0 / INTAKE_GAPS>0 / VALIDATION=PASS
启动广告创意项目.command: env-mode smoke test PASS
真实参考链接登记: add-reference live https check PASS
搜索质量 Gate: search-quality-gate PASS / PARTIAL_PASS / BLOCKED smoke PASS
参考包质量 Gate: reference-pack-gate PARTIAL_PASS when TBD search targets remain
真实图片文件登记: add-asset copy + manifest + visual gate PASS
image_gen 输出入库链路: import-imagegen + manifest + import log + visual gate PASS
视觉质量 Gate: visual-quality-gate blocks low-res / unapproved client-visible AI assets
Creative Production bridge: creative-doctor / creative-run review-only / import-creative-production fixture PASS
影视商业质量 Gate: film-quality-gate report + Gate log PASS
Goal Runner: goal-run deterministic safe-stop PASS
可编辑 PPTX 草稿: export-pptx / check-pptx PASS
客户稿风险 Gate: client-pack-gate PASS
非开发者交接 Gate: handoff-readiness-gate PASS
全局 Skill 安装: install-skill SHA256 match PASS
操作台 Playwright Chromium desktop/mobile screenshots: PASS
公开 demo 截图: docs/assets/dashboard-desktop.png / docs/assets/dashboard-mobile.png
sample project generator: adco sample / run_checks temp sample PASS
demo command: adco demo PASS
goal-plan 执行记录生成: examples/moncler_protocol_dry_run / examples/simulated_qingling_outdoor_launch PASS
反驳性议会 Gate 策略: 无记录时 PASS→PARTIAL_PASS / 有记录时 PASS 回归测试 PASS
操作台 Goal Tab: audit-dashboard PASS
Goal/Gate 回归测试: adco check PASS
Gate 结构化回归测试: adco check PASS
Gate 正向 fixture: visual PNG PASS / editable PPTX client-pack PASS / no-deps optional skip PASS
editable CLI install: adco / adco-check smoke PASS
package install: pip install . / adco init / adco demo / adco validate / adco check smoke PASS
wheel distribution check: make dist-check PASS
version diagnostics: adco --version PASS
doctor diagnostics: adco doctor PASS with remote configured
release diagnostics: adco release-status reports READY_FOR_REMOTE_CHECKS
docs diagnostics: adco docs reports local docs and quickstart paths
status diagnostics: adco status reports next action, blockers, open gaps, and pending confirmations
next diagnostics: adco next reports NEXT_STATUS and NEXT_ACTION
support bundle: adco support-bundle PASS with sanitized project diagnostics
support bundle JSON: adco support-bundle --json PASS
dashboard open command: adco open-dashboard PASS
dashboard audit JSON: adco audit-dashboard --json PASS
quickstart command: adco quickstart PASS
quickstart JSON: adco quickstart --json PASS
local release check: make release-check PASS
GitHub Actions: make release-check PASS on Python 3.10 / 3.12
public clone trial: git clone + pip install . + adco quickstart/open-dashboard/validate PASS
```

仍需真实项目负责人最终执行：

```text
真实联网搜索结果人工抽样质量
真实 image_gen 审美质量人工验收
最终客户稿人工发送确认
```
