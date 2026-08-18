# Specialist Exchange Reference

Read this file only for a neutral Specialist Exchange handoff, provider receipt,
or ADCO adoption. Creative briefing belongs in `creative_contract.md`; PPT and
client delivery belong in `ppt_and_client_pack.md`.

## Ownership

ADCO owns client/business truth, questions, exchange index, adoption, artifact
registration, versions, gates, PPT, FinalDelivery, Client Pack, and send
readiness. A professional Specialist owns only the bounded domain output requested
by the handoff. DIRcreative is one film-craft provider; ADCO does not depend on
its repository path, installation path, package version, run directory, or
internal validator.

Provider recommendations never become ADCO adoption automatically. Domain QA
never proves client-ready, PPT-ready, FinalDelivery-ready, send-ready, project
complete, or control-plane updated.

## Film handoff quality

Do not delegate an unresolved narrative and expect DIRcreative or another
provider to discover the advertising proposition. Before film handoff, ADCO
prepares a compact, evidence-bound packet containing:

- director thesis and audience state change;
- the brand/product's causal role and the result of a brand-replacement test;
- a beat-to-beat cause/effect chain and declared world/physical rules;
- latest user overrides, prohibited inventions, and exact asset truth;
- practical/VFX boundary, critical dependencies, stop conditions, and Plan B;
- reference principles plus what must not be copied.

The provider may improve film craft, but it must not silently change the
proposition, world rules, latest override, asset authority, or seller/consumer
point of view. Require a client-readable treatment before accepting a technical
shot list. For every adopted shot, recheck causal continuity, physical
feasibility, brand necessity, capture method, asset binding, and fallback. A
provider's `completed` or domain QA remains a candidate receipt until ADCO
performs this independent review.

## Negotiation and compatibility

```text
protocol_id: adco.specialist-exchange
controller versions: 2.0, 1.0
selection: numerically highest version supported by both controller and provider
v2 default/only execution_mode: inline
v2 nested dispatch: forbidden
```

`specialist-handoff` reads `supported_contract_versions` from the provider
descriptor. A provider advertising `2.0` and `1.0` receives v2. A provider that
supports only `1.0` falls back to the unchanged v1 contract. No common version is
an error; the provider cannot self-declare compatibility.

Canonical schemas:

```text
tools/adco_resources/contracts/specialist_exchange/v1/
tools/adco_resources/contracts/specialist_exchange/v2/
```

Both schema families are packaged and validated. Existing v1 rows/receipts stay
valid; v2 is used only for newly negotiated exchanges.

## Commands

```text
adco specialist-handoff <project> \
  --work-id <WORK-ID> \
  --profile-id <PROFILE-ID> \
  --objective "<bounded objective>" \
  --input-artifact <ART-ID> \
  --expected-output <OUTPUT-KIND> \
  --require-capability <CAPABILITY> \
  --descriptor <descriptor.json>

adco specialist-adopt <project> \
  --handoff <handoff.json> \
  --receipt <receipt.json> \
  --decision <adopt|partial_adopt|reject|defer> \
  --reason "<ADCO decision reason>" \
  [--map-output <PROVIDER-ID=PROJECT-PATH>]
```

## v2 minimal provider contract

The v2 handoff contains only provider-needed data:

```text
protocol_id
contract_version
task
brief_snapshot
locked_decisions
requested_outputs
quality_targets
execution_mode=inline
```

Requested outputs bind output id, type, and project-contained path root. Input
artifacts are already represented in the exact brief snapshot; ADCO separately
persists provider/profile identity, descriptor hash, handoff path/hash, host scope
baseline, receipt path/hash, and adoption decision in its local exchange index.

The v2 receipt contains only:

```text
protocol_id
contract_version
status: completed | needs_user | blocked | failed
outputs: output_id, type, path, sha256
domain_qa
summary
```

V2 rejects any nested-dispatch field and any outer readiness claim, including
`client_ready`, `ppt_ready`, `final_delivery_ready`, `send_ready`,
`project_complete`, or `control_plane_updated`. Output paths must remain within
requested roots and point to non-empty, unique, non-symlink/non-hardlinked files
whose hashes match. `completed` must return every requested output.

## v1 compatibility boundary

V1 retains its existing descriptor/profile extension, read-only receipt,
prompt-only/real-media authorization, optional verified ThreadOps execution,
host-scope proof, structured questions, six false reserved claims, and detailed
receipt/adoption schemas. Do not remove or rewrite those fields in old data.

V1 Thread mode is allowed only when explicitly selected and backed by a verified
real ThreadOps lane, isolated workspace/worktree, exact scope, dispatch proof,
host baseline, and host reconciliation. This does not make v2 dispatchable: v2 is
always inline and rejects lane/thread/nested dispatch state.

## Independent adoption

For either version, ADCO validates descriptor/handoff/receipt schemas, identity,
scope, file type, path, hash, inode uniqueness, status/QA semantics, and host
integrity before recording a separate adopt/partial-adopt/reject/defer decision.
Accepted artifacts are copied into new project-controlled paths without overwrite
and registered with exact provenance. Rejected/deferred work carries no adopted
output mapping.

For film adoption, the Film Gate scans exact active physical artifact rows for
`film.story_package`, `film.treatment`, `film.script`, `film.shot_plan`,
`film.visual_bible`, and `film.reference_prompt_plan`. `domain.film_qa` remains QA
evidence, not a physical film output.
