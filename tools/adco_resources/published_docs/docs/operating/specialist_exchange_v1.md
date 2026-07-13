# ADCO Specialist Exchange v1

## 目的

`adco.specialist-exchange` 是 ADCO 与专业 Skill 之间的中立版本化协议。`dircreative.film-preproduction` 是首个 profile，但 ADCO runtime 不依赖 DIR 仓库路径、安装路径、版本号、内部脚本或 `.dircreative/runs`。

```text
protocol_id: adco.specialist-exchange
contract_version: 1.0
default execution_mode: inline
nested_dispatch_allowed: false
```

## 权责

ADCO 独占：客户/业务事实、客户问题、artifact adoption、`current_truth.md`、`version_map.csv`、`artifact_index.csv`、Gate、PPT、FinalDelivery、client-send readiness。

DIRcreative profile 负责：story package、script、shot plan、visual bible、film reference/prompt plan 和 domain QA。它只能返回 recommendation；保留 claims `client_ready`、`ppt_ready`、`final_delivery_ready`、`send_ready`、`project_complete`、`control_plane_updated` 必须全部为 `false`。

## Descriptor

Provider descriptor 必须声明 profile、capabilities、execution/workspace modes 和零升级 authority。ADCO 接受兼容 descriptor `1.x`，前提是 `supported_contract_versions` 显式包含 base contract `1.0`。兼容性由 ADCO 计算；provider 不能自报 `compatible: true`。没有 descriptor 时仍可生成 `unverified` 人工 handoff，但不能 adopt。

Profile 可声明一个 `receipt_extension`（`id`、`version`、`required`）。required extension 会被复制到 handoff 的 `acceptance.required_receipt_extensions`；receipt 必须返回 exact id/version，否则拒收。Profile 还可显式声明 `generation_modes`；缺省值是 `prompt_only`，只有显式包含 `real_media` 的 neutral profile 才能接收真实媒体授权。当前 DIRcreative v1 descriptor 未声明该字段，因此仍严格为 `prompt_only`，无需 DIR 侧同步。ADCO 只验证协商后的中立边界，不读取 DIR 仓库、安装位置、包版本或内部 validator，因此 DIR 可独立演进其领域 receipt。

Canonical schemas 位于：

```text
tools/adco_resources/contracts/specialist_exchange/v1/
```

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

输入必须已登记在 `artifact_index.csv`，文件必须位于项目内，handoff 会重新计算 SHA-256。Handoff 同时绑定 provider/profile/descriptor/handoff identity、expected output kinds 和 host-computed scope baseline。输出只能写入 handoff 指定的 workspace；specialist 不能写 ADCO 控制文件、PPT exports 或 FinalDelivery。`read_only` 的 `scope.write` 只能包含 exact `receipt_path`，不授予 output root；它只能 receipt-only 返回 `needs_user` / `blocked` / `failed`，再由 ADCO `defer` / `reject`，不得产生 adopted output 或推进 Gate。

`prompt_only` 必须保持 `authorized=false` 且 `authorization_ref=null`。`real_media` 必须引用项目内真实存在、非 symlink、非 hardlink 的结构化授权 JSON；证据必须绑定 exact work/profile/mode/input artifact IDs/expected output kinds、用户或客户确认、授权人和时间，并由 host baseline 锁定内容。DIRcreative v1 profile 仍只接受 `prompt_only`。

默认 `inline`。只有显式选择 `--execution-mode codex_thread --lane-id <LANE>` 时才使用 Thread，而且 lane 必须已有 ThreadOps 验证的真实 thread id、未 reconcile 的 active execution lane 和 host scope baseline。不能用 main/planned/source id，也不能嵌套派发。采用前还必须有主控 reconciliation 生成的 hash-bound host scope proof。

## Receipt 与采用

Receipt 必须从 handoff 指定的 exact receipt path 返回，并绑定 exchange/handoff/work/provider/profile、descriptor SHA、handoff SHA、输入 hash、requested output kind、输出 path/hash、QA、outcome、执行证据、六个 false claims 和协商后的 extensions。Receipt 文件本身必须是 exact lexical path 下非空、单链接、非 symlink/hardlink 的普通文件，不能借 inode 复用写入控制面。每个输出也必须位于项目内和 exact write scope 内，是非空、单链接的普通文件；拒绝 symlink、hardlink，并分别要求 `provider_artifact_id`、`kind`、规范化 path 和物理 inode 唯一。ADCO 在 adoption 前执行 packaged canonical handoff/receipt JSON Schema，写 adoption 前再执行 adoption Schema；项目 validator 会重新读取并复核三者，缺字段、空版本或空 recommendation 不能靠更新 index/hash 绕过。由于 DIR v1 要求 baseline 保留 specialist 控制目录 exclusion，ADCO 另用 exact allowlist 复核 index/lock、已登记 handoff/baseline/adoption 与 hash-bound descriptor snapshot；任何额外控制面文件都会阻断 runtime adoption 和持久化 validation。ADCO 用 host baseline 检查实际项目 diff；worker/provider 自报 `out_of_scope_writes=false` 不是充分证据。`needs_user` 必须返回结构化问题，且每个 question id 非空并在 receipt 内唯一；问题由 ADCO 展示给用户/客户，specialist 不直接联系客户。

```text
adco specialist-adopt <project> \
  --handoff <handoff.json> \
  --receipt <receipt.json> \
  --decision partial_adopt \
  --reason "<ADCO decision reason>" \
  --map-output <PROVIDER-ART-ID=AD-creative/film/target.md>
```

ADCO adoption record 与 provider receipt 分离，并以 `adoption_sha256` 绑定 exchange index；项目 validator 还会复核 adoption 的 handoff/receipt/decision/outcome/Gate 语义，不能只刷新单个 hash 改写结论。`completed + qa pass` 才可 full adopt；`needs_user` 最多 internal partial adoption 且不得推进 Gate；`blocked` / `failed` 只能 reject/defer；simulated output 不得 adopt。`reject` / `defer` 不得携带 output mapping；read-only receipt 不产生采用产物。目标路径必须是项目内规范路径，不能穿越、落入控制面/PPT/FinalDelivery 或经 symlink 逃逸；目标文件已存在时拒绝覆盖。

## 验证边界

Domain QA PASS 只证明 specialist output 通过该领域检查。后续仍要经过 ADCO creative/client-language/visual/authorization/PPT/package/manual-review/send-readiness Gate。任何 specialist claim 都不能绕过这些 Gate。
