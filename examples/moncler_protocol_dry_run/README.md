# Moncler Protocol Dry Run

状态：历史文件流/Delivery 兼容性验证样例，不是真实客户交付，不代表最终创意方案，也不是当前 Content Surface 的默认操作范本。保留其记录用于 validator 和迁移兼容性，不从中推断真实搜索、生成或客户交付已发生。

目标：

```text
验证 Project File Protocol 能否承载 Moncler 类视觉提案项目：
资料进入 → 需求抽取 → 缺口判断 → 搜索计划 → work item → agent handoff → reference pack → image job → visual gate → 项目看板 / 待确认
```

验证重点：

```text
不看 UI，也能知道项目卡在哪里
不复制长 prompt，也能继续下一步
换一个 Agent，也能读 handoff 接着做
新增客户反馈后，旧版本不会污染新版本
每个视觉资产能追溯到 requirement / reference / slot / Gate
```

入口：

```text
AD-creative/handoff/项目看板.md
AD-creative/handoff/待你确认.md
AD-creative/orchestrator/current_truth.md
```
