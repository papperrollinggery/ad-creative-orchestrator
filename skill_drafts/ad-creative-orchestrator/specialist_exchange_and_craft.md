# Specialist Exchange and Creative Craft Reference

Read this file before neutral specialist exchange, profile analysis, public research, visual/image work, PPT export/review, Client Pack review, or feedback-driven revision.

## Neutral specialist exchange

ADCO owns client/business truth, adoption, versions, PPT, FinalDelivery, and send readiness. A specialist provider owns only its bounded domain output. Provider recommendations never become ADCO adoption automatically.

Protocol baseline:

```text
protocol_id: adco.specialist-exchange
contract_version: 1.0
default execution_mode: inline
nested_dispatch_allowed: false
```

Commands:

```text
adco specialist-handoff <project> --work-id <id> --profile-id <profile> --objective <objective> --input-artifact <artifact_id> --expected-output <kind> --descriptor <json>
adco specialist-adopt <project> --handoff <handoff.json> --receipt <receipt.json> --decision <adopt|partial_adopt|reject|defer> --reason <reason> [--map-output <provider_id=project_path>]
```

## Handoff rules

Every handoff binds:

```text
work/handoff/provider/profile ids
compatible contract and descriptor versions
input artifact id/path/hash
objective and expected output kind
execution/workspace mode
read/write/output/receipt scopes
generation authorization mode
questions contract
required receipt extension when advertised
```

Inputs/outputs are project-relative, indexed, hash-bound, and inside exact scopes. Provider outputs are non-empty regular files with unique provider id, kind, canonical path, and physical inode. No symlinks or hardlinks.

`needs_user` question ids are non-empty and unique. The specialist returns questions to ADCO; it never contacts the client.

## Execution boundaries

`read_only` grants only the exact receipt path. It may close only as receipt-only needs-user/blocked/failed plus ADCO defer/reject. It cannot adopt output or advance a Gate.

`prompt_only` keeps media generation unauthorized and carries no real-media reference.

`real_media` requires project-contained structured user/client authorization bound to the host baseline. Omission defaults to prompt-only.

`codex_thread` is allowed only when explicitly selected and backed by a verified ThreadOps lane, real Thread id, isolated workspace, exact scope, dispatch proof, and host reconciliation. Never hardcode a provider repository path, package version, run directory, or validator path.

Packaged canonical schemas run before adoption and again during project validation. An index/hash update cannot legalize a schema-invalid receipt or adoption. Compatible provider descriptor versions may evolve within declared base-contract compatibility. Required receipt extensions must be negotiated in the handoff and present in the receipt.

Domain QA PASS never means client-ready, PPT-ready, FinalDelivery-ready, send-ready, project-complete, or control-plane-updated.

## Adoption

ADCO separately records adopt/partial-adopt/reject/defer with reason and explicit output mapping. Before adoption:

1. Validate handoff, receipt, provider extension, and generation authorization.
2. Verify exact input/output scopes, file type, hash, inode uniqueness, and baseline binding.
3. For Thread mode, verify host scope proof and reconciliation reference.
4. Register accepted artifacts without overwriting existing versions.
5. Record rejected/deferred reasoning.
6. Advance only the ADCO-owned stage supported by evidence.

## Profile analysis

Use `adco profile-analyze` for meeting notes, transcripts, client discussion, brand, or company context. It maintains:

```text
profile_subjects.csv
meeting_voice_map.csv
profile_insights.csv
profile_conflicts.csv
profile_current_truth.md
AD-creative/handoff/画像分析简报.md
```

Tie claims to source-event evidence where possible. Decision power, influence, personality, preference, and concern labels remain candidates until confirmed. Record disagreement and reconciliation path. Do not turn internal profiling into client-visible claims without separate approval.

## Creative proposal quality

`creative-proposal` produces internal, traceable strategy artifacts:

```text
AD-creative/creative/creative_directions.md
AD-creative/creative/option_matrix.csv
AD-creative/proposal_architecture/proposal_structure.md
AD-creative/client_review/slide_spec.md
```

The quality Gate checks:

```text
brief and evidence coverage
material gaps and questions
product feature -> customer benefit translation
differentiated directions and choice rationale
key visual/action and story logic
unsupported cases/references
generic slogans or claims
internal execution language
```

Customer-facing pages may be long-form and numerous when the story requires it, but each page stays low-density and decision-readable. Do not collapse narrative, timing, dialogue, or brand mapping into short pitch cards or production tables.

## Writing quality

Prefer concrete customer moment, product benefit, evidence, risk, and next action. Remove chatbot residue, vague authority, exaggerated significance, repetitive framing, repeated dash rhythm, and generic AI vocabulary. Any factual authority claim needs a source id or an explicit question.

## Search and reference work

Before search, state:

```text
gap to solve
platforms/sources
why those sources
fallback if not searched
expected output
```

Prefer public official sources. Ask before private account, paid/login, client-material upload, or confidential disclosure. Register every used source with role, provenance, relevance, borrow boundary, and do-not-copy boundary. Run search/reference Gates afterward.

## Visual asset intake

Before generation or acceptance:

```text
bind requirement
bind reference role
bind asset slot and use case
declare client visibility
record source/platform/conversation/local file
hash the file
record original/processed status
record prompt/edit instruction when relevant
run visual QA
obtain independent hash-bound authorization for direct client use
```

`approval=PASS` or a notes token is never sufficient authorization. Direct client use needs an authorization receipt bound to asset id/hash, scope, approver, time, and evidence.

Inspect local manifests and browser-held assets before declaring images missing or generating replacements. Import generated outputs into project-controlled storage before referencing them.

## PPT export and review

Before PPT builder:

```text
client-readable framework complete
client_review_outline and slide_spec complete
explicit human/client confirmation bound to exact outline hash
client-outline-gate PASS
visual system defined
unapproved images remain placeholders
```

`export-pptx` writes a new immutable version and refuses overwrite. Register exact PPTX hash/size/version. Derive PDF, preview, text extract, and editability check from the same exact PPTX and bind derivation id/hash.

PPT review checks:

```text
text overflow/crop
busy-image contrast
font legibility/count
image distortion/crop/scale/orientation
repeated still/background misuse
story-beat differentiation
timing labels
key dialogue/phrase labels
editable text on exact current PPTX
```

No exact PPTX plus real preview means visual layout cannot PASS.

## Client Pack and manual review

Client Pack Gate writes an immutable exact-input manifest and current binding digest. Any input change invalidates the binding. Gate PASS means ready for independent human review only.

Manual review must be an independently completed receipt bound to current version, PPTX hash, and package digest. Generating an unchecked checklist is NOT_RUN. Send readiness additionally requires separate explicit send authorization on the same fresh digest. No command sends the package.

## Feedback and revision

When feedback arrives:

1. Register the source event and classify supplement/change/rejection/approval.
2. Update feedback map and affected artifacts.
3. Mark affected requirements, assets, references, and package binding stale.
4. Supersede rather than overwrite.
5. Increment the client-visible version for material changes.
6. Update next-version plan and pending confirmations.
7. Re-run only the stages/Gates whose exact inputs changed.

If feedback changes blockers after a previous completion claim, reopen the stage as revision.

## Hygiene

`adco hygiene` is read-only. Treat tracked changes as intentional until reviewed. Report cache/temp pollution, unexpected untracked files, and active/unarchived Thread rows. Use `/tmp` or declared project workspaces for scratch validation. Never reset, delete user material, or clean a project automatically.
