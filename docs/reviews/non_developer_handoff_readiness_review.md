# Non-Developer Handoff Readiness Review

日期：2026-05-22

## 结论

状态：

```text
READY_FOR_NON_DEVELOPER_INTERNAL_OPERATION
```

含义：

```text
广告创意者可用一个命令初始化项目、登记资料、抽取首批需求/缺口、查看操作台、读取待确认事项、运行三方议会审核。
完全不懂命令行的使用者可双击 启动广告创意项目.command，通过 macOS 选择框完成项目目录、资料位置、本轮目标输入。
本次按目标授权已安装本机 Codex Skill，源码与安装目标 SHA256 一致。
```

不含义：

```text
不是完整交互式 UI 产品。
不是已验证自动搜索结果质量。
不是替代最终人工审美判断。
不是已完成最终客户稿内容审稿。
不是允许自动发送客户稿。
```

## 新入口

```text
python3 tools/ad_creative_operator.py run <项目目录> --material <资料文件或文件夹>
python3 tools/ad_creative_operator.py status <项目目录>
python3 tools/ad_creative_operator.py council <项目目录> --render-dashboard
```

## 非开发者可看产物

```text
AD-creative/handoff/操作台.html
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/handoff/客户追问话术.md
AD-creative/handoff/本轮交付说明.md
AD-creative/gates/THREE-COUNCIL-READINESS_report.md
```

## 已验证命令

```text
python3 -m py_compile tools/init_project.py tools/validate_project.py tools/ad_creative_operator.py
```

```text
python3 tools/ad_creative_operator.py run <tmp_project> --material <tmp_materials>
INTAKE_REQUIREMENTS=6
INTAKE_GAPS=5
COUNCIL=PASS
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py council examples/moncler_protocol_dry_run --render-dashboard
COUNCIL=PASS
```

```text
python3 tools/ad_creative_operator.py council examples/simulated_qingling_outdoor_launch --render-dashboard
COUNCIL=PASS
```

```text
python3 tools/ad_creative_operator.py audit-dashboard examples/simulated_qingling_outdoor_launch --render
DASHBOARD_AUDIT=PASS
```

```text
python3 tools/ad_creative_operator.py add-reference <tmp_project> --url https://example.com/ --title "Example public reference smoke test"
REFERENCE_ACTION=created
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py reference-pack-gate examples/moncler_protocol_dry_run
REFERENCE_PACK_GATE=PARTIAL_PASS
FINDINGS=2
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py reference-pack-gate examples/simulated_qingling_outdoor_launch
REFERENCE_PACK_GATE=PARTIAL_PASS
FINDINGS=5
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py search-quality-gate examples/moncler_protocol_dry_run
SEARCH_QUALITY_GATE=PARTIAL_PASS
FINDINGS=2
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py search-quality-gate examples/simulated_qingling_outdoor_launch
SEARCH_QUALITY_GATE=PARTIAL_PASS
FINDINGS=4
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py search-quality-gate <tmp_project_with_complete_search_plan_and_reference>
SEARCH_QUALITY_GATE=PASS
FINDINGS=0
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py search-quality-gate <tmp_project_with_client_visible_search_target>
SEARCH_QUALITY_GATE=BLOCKED
GATE_ISSUES includes 搜索目标不能标记客户可见
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py add-asset <tmp_project> --file <png> --slot-id KV-001 --requirement-id REQ-001 --reference-id REF-001 --selected
ASSET_ID=IMG-001
VALIDATION=PASS
```

```text
CODEX_HOME=<tmp_codex_home> python3 tools/ad_creative_operator.py import-imagegen <tmp_project> --slot-id KV-SMOKE-001 --selected --qa-status PASS
ASSET_ID=IMG-001
IMAGEGEN_IMPORT_LOG=<tmp_project>/AD-creative/image_jobs/imagegen_import_log.md
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py visual-quality-gate <tmp_project>
VISUAL_QUALITY_GATE=PASS
FINDINGS=0
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py visual-quality-gate <tmp_project_with_320x240_selected_asset>
VISUAL_QUALITY_GATE=BLOCKED
GATE_ISSUES includes 尺寸过低
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py client-pack-gate <tmp_project_with_unapproved_client_visible_generated_image>
CLIENT_PACK_GATE=BLOCKED
GATE_ISSUES includes 客户可见生成图缺少批准记录
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py install-skill
SKILL_INSTALL=PASS
SOURCE_SHA256=e4e24fbeb6d5fbd09abd8a6762ba74d1433e255af717db331d174b78a96fc3e8
TARGET_SHA256=e4e24fbeb6d5fbd09abd8a6762ba74d1433e255af717db331d174b78a96fc3e8
```

```text
python3 tools/ad_creative_operator.py handoff-readiness-gate examples/moncler_protocol_dry_run
HANDOFF_READINESS_GATE=PASS
BLOCKERS=0
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py handoff-readiness-gate examples/simulated_qingling_outdoor_launch
HANDOFF_READINESS_GATE=PASS
BLOCKERS=0
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py export-pptx <tmp_project>
PPTX_SLIDES=5
PPTX_EDITABLE_TEXT_RUNS=28
PPTX_EDITABLE=PASS
VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py client-pack-gate <tmp_project>
CLIENT_PACK_GATE=PASS
ISSUES=0
VALIDATION=PASS
```

```text
AD_CREATIVE_PROJECT=<tmp_project>
AD_CREATIVE_MATERIAL=<tmp_material>
AD_CREATIVE_GOAL="整理客户 brief。"
AD_CREATIVE_NO_OPEN=1
AD_CREATIVE_NO_DIALOG=1
./启动广告创意项目.command
DONE
VALIDATION=PASS
```

```text
启动广告创意项目.command: zsh -n PASS, executable bit set
启动广告创意项目.command env-mode smoke test: INTAKE_REQUIREMENTS=4 / INTAKE_GAPS=4 / COUNCIL=PASS / PPTX_EDITABLE=PASS / CLIENT_PACK_GATE=PASS / VALIDATION=PASS
```

```text
python3 tools/ad_creative_operator.py intake <tmp_project>
REQUIREMENTS>0
GAPS>0
VALIDATION=PASS
```

```text
node --check /tmp/moncler_protocol_dry_run-dashboard-script.js
node --check /tmp/simulated_qingling_outdoor_launch-dashboard-script.js
PASS
```

```text
python3 tools/validate_project.py examples/moncler_protocol_dry_run
ERRORS=0
VALIDATION=PASS
```

```text
python3 tools/validate_project.py examples/simulated_qingling_outdoor_launch
ERRORS=0
VALIDATION=PASS
```

```text
python3 /Users/jinjungao/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /Users/jinjungao/work/ad-creative-orchestrator --format markdown
已处理：重复 ID 扫描、PPTX namelist 线性查找、风险词逐项扫描、循环内排序。
保留：材料行遍历、素材文件遍历、JSONL 行解析；这些是线性输入扫描，右侧引用集合已预构建。
```

## 操作台检查

检查方式：

```text
qlmanage -t -s 1440 -o /tmp <project>/AD-creative/handoff/操作台.html
playwright screenshot --browser chromium --viewport-size "1440,1200" <file_url> /tmp/adcreative-final-dashboard-desktop.png
playwright screenshot --browser chromium --viewport-size "390,844" <file_url> /tmp/adcreative-final-dashboard-mobile.png
```

通过项：

```text
左侧导航清晰
主区 Work / Materials / Assets / Gates / Decisions 可切换
主区 工作 / 资料 / 参考 / 图片 / 产物 / 关卡 / 待确认 可切换
无效 Timeline nav 已移除
搜索、状态筛选、风险筛选存在
首屏无 JavaScript 时也能看到 Work 和 Gaps
浏览器中可点击行更新右侧检查器
底部只保留高风险确认边界
桌面视口无重叠
移动宽度有单栏降级
移动端表格横向滚动，不压缩列文字
JS 语法通过 node --check
```

## 授权边界

三方议会 `PASS` 后可自动推进：

```text
初始化模板
登记资料
内部需求/缺口整理
公开官方来源搜索计划
内部视觉方向草图规划
internal_only image_gen 输出入库
只读操作台刷新
内部 Gate 初检
项目内 Skill 草稿
本次已授权的全局 Skill 安装
```

仍需明确确认：

```text
发送客户稿
付费、登录、私密账号、KYC、钱包或凭据
上传客户资料到外部平台
未授权的新全局 Skill 安装
覆盖或删除旧版本
将 AI 图标记为客户可见
```

## 剩余工作

```text
真实客户项目中的搜索抽样、image_gen 审美判断、最终发送确认由 AD-creative/delivery/manual_review_checklist.md 承接。
```
