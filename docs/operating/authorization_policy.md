# 授权策略

目标：减少中途询问，让系统自己推进低风险内部工作；高风险动作仍明确卡住。

## 三方议会

每次关键推进前可运行：

```text
python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py council <项目目录> --render-dashboard
```

三方：

```text
Strategy Council：是否对客户目标有帮助
Operations Council：是否可追溯、可验证、无结构错误
Craft Council：是否能让广告创意者看懂，操作台和 handoff 是否清晰
```

## 反驳性议会

关键阶段 Gate 前必须补充反驳性议会记录：

```text
反对意见
反驳路径
修订决议
门禁结论
```

规则：

```text
没有反驳性议会记录：Gate 最高 PARTIAL_PASS
存在 blocking 反对意见：Gate 必须 BLOCKED 或 REVISE
反对意见已修订且证据可追溯：Gate 可 PASS
```

## PASS 后可自动推进

```text
初始化模板
登记资料
内部需求/缺口整理
公开官方来源搜索计划
内部视觉方向草图规划
只读操作台刷新
内部 Gate 初检
项目内 Skill 草稿
```

## 永远需要明确确认

```text
发送客户稿
付费、登录、私密账号、KYC、钱包或凭据
上传客户资料到外部平台
全局安装 Skill
覆盖或删除旧版本
将 AI 图标记为客户可见
```

## 判断规则

```text
COUNCIL=PASS：可自动推进低风险内部动作
COUNCIL=PARTIAL_PASS：只能推进结构修复和内部整理
COUNCIL=BLOCKED：先修 blocker
```

## 交付口径

对非开发者只展示：

```text
操作台.html
项目看板.md
待你确认.md
客户追问话术.md
本轮交付说明.md
```

CSV、events.jsonl、gate_log 只作为事实源和审计证据。
