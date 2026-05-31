# Simulated Project Trial Review

日期：2026-05-13

模拟项目：

```text
examples/simulated_qingling_outdoor_launch/
```

## 结论

状态：

```text
VALIDATED_READY_FOR_MANUAL_CODEX_OPERATION
```

含义：

```text
项目协议已经跑通一个模拟广告项目的完整链路：
Intake → Search Plan → Reference Pack → Creative → Visual / image_gen Plan → Visual Review → Client Review / PPT Plan → Feedback Merge → Final Gate → Skill Mining。
```

不含义：

```text
没有执行真实外部搜索。
没有生成真实图片。
没有生成实际 PPTX。
不能把模拟输出当客户稿发送。
```

## 试运行输入

```text
客户 brief
会议记录
导演组意见
客户后续变更
```

## 已验证能力

```text
资料时间轴
需求和缺口
搜索计划和模拟参考包
创意方向和方案结构
视觉资产和 image_gen prompt pack
Visual Review Gate
客户审阅包和 SlideSpec
PPT 可编辑性规划
客户反馈合并
Final Gate
项目内 Skill Mining
```

## 关键规则

```text
先锁人物 / 产品 / 环境 / 风格，再生成关键帧。
产品资产缺失时，产品细节图保持 blocked。
AI 图默认 internal_only。
raw 不进客户稿。
selected 也必须过客户可见性确认。
模拟 reference pack 不能当真实客户引用。
```

## 验证工具结果

命令：

```text
python3 tools/validate_project.py examples/simulated_qingling_outdoor_launch
```

结果：

```text
SOURCE_EVENTS=5
REQUIREMENTS=9
WORK_ITEMS=11
AGENT_RUNS=9
ARTIFACTS=36
GATES=8
VERSIONS=11
ERRORS=0
VALIDATION=PASS
```

## 当前剩余风险

```text
真实搜索质量未验证。
真实 image_gen 视觉质量未验证。
真实客户级 PPTX 内容质量未验证。
真实客户资料可能暴露字段不足或目录密度问题。
```

## 判定

```text
可以用于下一个真实项目的手动 Codex-first 操作。
真实项目里，公开官方来源搜索可在三方议会 PASS 后自动推进；AI 图客户可见、客户稿发送、付费/登录/上传资料、全局 Skill 安装前仍必须人工确认。
```
