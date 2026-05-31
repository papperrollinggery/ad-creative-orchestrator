# Skill 沉淀循环上下文

目标：实现类似 Hermes 的能力：当广告创意流程里发现可重复通路时，生成 Skill 草稿，用户确认后再安装。

## 默认策略

V1 不自动安装 Skill。

流程：

```text
发现重复通路
-> 记录 evidence
-> 评分是否值得沉淀
-> 生成项目内 Skill 草稿
-> 用户确认
-> 才允许提升到 ~/.codex/skills
```

默认草稿目录：

```text
skills_drafts/<skill-slug>/
  SKILL.md
  evidence.md
  install_request.md
```

## 候选条件

满足以下条件才进入候选：

- 同类步骤重复出现 >= 2 次
- 输入 / 输出边界稳定
- 可写成清晰触发条件
- 不包含单一客户机密或一次性文案
- 有可复用 Gate 或 QA 标准
- 能明显减少下一次项目的提示词转移成本

不沉淀：

- 单一客户专属内容
- 临时审美判断
- 一次性项目文案
- 还没跑通过的猜想
- 需要大量人工解释才能复用的流程

## 状态流

```text
observed
-> candidate
-> drafted
-> approved
-> installed

或：

candidate
-> rejected
```

状态记录在：

```text
00_orchestrator/skill_opportunities.csv
```

建议字段：

```csv
id,name,status,evidence_file,created_at,updated_at,reason,next_action
```

## Skill 草稿要求

`SKILL.md` 必须包含：

- `name`
- `description`
- 触发条件
- 输入文件
- 输出文件
- 操作步骤
- QA Gate
- 不适用场景

frontmatter 示例：

```yaml
---
name: ad-creative-brief-gate
description: Use when turning an advertising client brief into a locked current_truth, constraints list, no-go list, and first task board before creative development begins.
---
```

## 推荐第一批可沉淀 Skill

### 1. Brief Gate Skill

用途：

- 从 brief / 客户资料中提取项目边界
- 生成 `current_truth.md`
- 生成 `client_constraints.md`
- 生成 `no_go_list.md`

### 2. Storyline Structure Skill

用途：

- 把 TVC 方向拆成 30 秒内节拍
- 输出三幕结构、shot table、旁白草案
- 保证每个镜头有产品、动作、声音、裁切安全区

### 3. Visual Asset Manifest Skill

用途：

- 把 moodboard / 生图 / 分镜资产登记进 manifest
- 区分 raw / selected / rejected
- 阻止未登记图片进入客户稿

### 4. HTML Review Gate Skill

用途：

- 检查 HTML 客户样稿
- 查缺图、溢出、内部注释、假 logo、contact sheet
- 输出 `html_review.md`

### 5. Client Feedback Merge Skill

用途：

- 把客户反馈拆成 Must / Should / Maybe / Reject
- 更新 `current_truth.md`
- 生成修改对应表

## 安装边界

安装到用户级 Skill 前必须有：

- 项目内草稿
- evidence
- 用户确认
- 明确 Skill 名称
- 无客户机密

安装目标：

```text
~/.codex/skills/<skill-slug>/
```

V1 只生成：

```text
install_request.md
```

不直接写 `~/.codex/skills`。

