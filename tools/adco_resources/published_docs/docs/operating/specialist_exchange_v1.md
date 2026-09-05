# ADCO Specialist Exchange v1/v2

## 目的与权责

`adco.specialist-exchange` 是 ADCO 与专业 Skill/Provider 之间的中立版本化协议。ADCO 是 control plane；当前主模型或用户明确选择的专业 Specialist 提供 creative reasoning；DIRcreative 是 film craft provider。ADCO runtime 不依赖 DIR 仓库、安装路径、版本、内部脚本或 run 目录。

ADCO 独占客户/业务事实、客户问题、exchange index、artifact adoption、`current_truth.md`、`version_map.csv`、`artifact_index.csv`、Gate、PPT、FinalDelivery、Client Pack 和 send readiness。Provider 只返回有界 domain output/recommendation/QA，不能更新外层控制状态。

## 版本协商

```text
protocol_id: adco.specialist-exchange
ADCO supported_contract_versions: 2.0, 1.0
selection: 双方支持版本中的最高数值版本
```

Provider descriptor 同时声明 `2.0`/`1.0` 时选择 v2；只声明 `1.0` 时自动回退兼容 v1；没有共同版本时拒绝 handoff。Provider 不能用 `compatible: true` 自证兼容。

Canonical schemas：

```text
tools/adco_resources/contracts/specialist_exchange/v1/
tools/adco_resources/contracts/specialist_exchange/v2/
```

V1 历史 handoff/receipt/adoption 保持原样可读可验；v2 只用于新协商写入。

## 创建 handoff

```text
adco specialist-handoff <project> \
  --work-id <WORK-ID> \
  --profile-id dircreative.film-preproduction \
  --objective "<bounded objective>" \
  --input-artifact <ART-ID> \
  --expected-output film.story_package \
  --require-capability film.story_package \
  --descriptor <descriptor.json>
```

输入必须已登记且位于项目内，ADCO 重新计算 SHA-256。输出只能落在 handoff 指定的项目内 scope，不能写控制面、PPT exports 或 FinalDelivery。

## V2 最小协议

V2 固定 `execution_mode=inline`，禁止 nested dispatch、lane/thread/worker 派发字段。Handoff 只给 Provider 必需信息：

```text
protocol_id
contract_version
task
brief_snapshot
locked_decisions
requested_outputs
quality_targets
execution_mode
```

Receipt 只返回：

```text
protocol_id
contract_version
status: completed | needs_user | blocked | failed
outputs: output_id, type, path, sha256
domain_qa
summary
```

V2 receipt 禁止任何外层 readiness claim，包括 `client_ready`、`ppt_ready`、`final_delivery_ready`、`send_ready`、`project_complete`、`control_plane_updated`。输出必须匹配 requested id/type/path root/hash，是非空且不经 symlink/hardlink 复用的独立普通文件；`completed` 必须返回全部 requested outputs。

ADCO 在本地 exchange index 另存 provider/profile identity、descriptor hash、handoff path/hash、host scope baseline、receipt path/hash 与 adoption decision；这些控制字段不重复塞给 Provider。

## V1 兼容边界

V1 保留原有 descriptor `1.x` 兼容与 profile receipt extension、`read_only` receipt-only 返回、`prompt_only`/`real_media` 授权、结构化 questions、六个 false reserved claims、host baseline/proof 和可选的 verified ThreadOps execution。

`read_only` 只允许 exact receipt path，只能以 needs_user/blocked/failed 加 defer/reject 结束；不得产生 adopted output 或推进 Gate。`real_media` 必须引用项目内、结构化、hash-bound 的真实用户/客户授权。V1 Thread mode 只有在显式选择且已有真实 ThreadOps lane、isolated workspace/worktree、exact scope、dispatch proof、baseline 与 host reconciliation 时成立；v2 不继承这条能力。

## Receipt 与独立采用

```text
adco specialist-adopt <project> \
  --handoff <handoff.json> \
  --receipt <receipt.json> \
  --decision <adopt|partial_adopt|reject|defer> \
  --reason "<ADCO decision reason>" \
  [--map-output <PROVIDER-ID=AD-creative/film/target.md>]
```

ADCO 在采用前验证协商版本、canonical schemas、identity、scope、path/hash、inode 唯一性、status/QA、host baseline 与 receipt 绑定，再写独立 adoption record。Provider receipt 即使 `completed + qa pass` 也不会自动成为 ADCO adoption；reject/defer 不得携带 output mapping，目标已存在时拒绝覆盖。

Domain QA PASS 只证明 specialist output 的领域检查。后续仍需 ADCO creative/client-language/visual/authorization/PPT/package/manual-review/send-readiness Gate；任何版本都不能绕过这些 Gate。
