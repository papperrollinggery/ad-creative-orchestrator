# OpenAI Visualizations in ADCO Chat

Read this reference when a supported Codex or ChatGPT conversation can make ADCO status, logic, comparison, review, or feedback easier to operate visually.

## Product boundary

This integration is specifically for OpenAI Visualizations / `@Visualize`. It is not a redesign of `AD-creative/handoff/操作台.html`, not a Data Analytics widget workflow, and not a new persistent dashboard.

Visualizations progressively enhance the existing ADCO conversation:

    exact-current project files
    -> one hash-bound visualization spec
    -> validate
    -> one small thread-scoped visual decision surface
    -> human-readable follow-up message
    -> ADCO re-reads current truth and validates authority
    -> project write, affected Gate re-run, and confirmation echo

The visualization is a snapshot and review surface. It is never source truth, approval, send authorization, or completion evidence.

The frontstage is for the user, not the controller. Show customer-readable work, judgment, choices, effects, and next steps. Keep artifact IDs, hashes, Gate names, receipts, locks, authority fields, source bindings, and control-plane terminology backstage in the spec, validator, and audit output.

Translate internal P0-P8 phases into readable labels such as `资料与目标`, `提案框架`, `方向确认`, `创意与素材`, `提案制作`, `视觉与内容检查`, `交付包检查`, `发送准备`, and `反馈与下一版`. Do not make users decode phase codes.

## Availability

Visualizations availability depends on the active product surface, account, workspace, rollout, and whether `@Visualize` is selected or exposed. A thread-scoped visualization directory is a positive host signal; its absence is not an error.

- Supported conversation: build and validate `adco.chat-visualization@1.0`, render one fragment inside the current thread's `.codex/visualizations` directory, and show it with the normal chat explanation.
- Unsupported Codex CLI, IDE, account, or failed render: use the spec's complete Markdown, table, or Mermaid fallback without asking the user to change clients.
- Do not replace this path with raw HTML in the answer, an unrelated plugin card, or a Data Analytics widget that does not answer a genuine quantitative question.

## Smallest useful surface

Use a visualization only when it makes the current decision materially clearer than concise text. Keep one current stage, one primary decision, one primary action, and at most one secondary action. No tabs, file browser, nested scrolling, deep navigation, or multi-stage Workbench inside an inline response.

| ADCO need | Visualizations surface | Required visible evidence | Fallback |
| --- | --- | --- | --- |
| Resume or status | `current-status` | current stage, current work, unresolved issue, review state, next safe action | Markdown |
| Explain logic | `phase-logic` | completed/current/blocked stages, what is needed, what must be revisited | Mermaid |
| Ask one blocker | `blocking-decision` | question, 2-3 mutually exclusive options, recommendation, tradeoff, decision owner in normal language | Markdown |
| Compare routes | `option-comparison` | 2-3 options, criteria, evidence status, production impact, recommendation | Table |
| Review a visual asset | `asset-review` | current asset, intended role, inspected preview, visible issue, proposed action | Markdown |
| Review PPT/PDF | `ppt-slide-review` | current deck preview, slide/page, region finding, importance, user-facing effect | Table |
| Understand feedback impact | `feedback-impact` | received feedback, affected content, work to revisit, preserved content, next review | Mermaid |
| Confirm recorded change | read-only confirmation view | recorded choice, updated content, preserved content, items to recheck, next stage | Markdown |

Use fullscreen only when an inline view cannot remain legible, such as a long slide review, dense artifact graph, or large feedback impact map.

## Source-truth binding

Build every spec from current project files, never chat memory:

| Visible claim | Authoritative source |
| --- | --- |
| Current phase and next action | `current_truth.md`, `work_items.csv`, `gaps.csv` |
| Current version | `current_truth.md#Current Version Truth` plus the unique current row in `version_map.csv` |
| Artifact identity and preview | active/current `artifact_index.csv` row plus physical file SHA-256 |
| Gate state and freshness | latest applicable `gate_log.csv` row bound to exact target/hash |
| Pending question | open blocking gap or explicit handoff confirmation; never infer from prose alone |
| Feedback impact | `source_events.csv`, `feedback_map.csv`, affected requirements/artifacts, invalidated Gate/package bindings |

Every source artifact in a spec needs a stable artifact ID, version, project-relative path, lifecycle state, and 64-character SHA-256. Recompute the physical hash before rendering. Reject missing files, path traversal, symlink escape, duplicate current versions, inactive artifacts presented as current, and stale preview/version bindings.

Fields are either:

- `source_bound`: include an `artifact_id#/field` source reference;
- `presentation_only`: explanatory layout or label with a null source reference.

Never put secrets, private account data, internal prompts, raw capability evidence, or hidden reasoning into a visualization.

## Visual conversation loop

1. Read the current control plane and identify the one decision or inspection task.
2. Choose the registered surface; do not invent a generic dashboard.
3. Build the versioned spec with exact source bindings and a complete fallback.
4. Validate the spec before rendering.
5. Render a new lowercase-hyphenated HTML fragment inside the current thread visualization directory. Never overwrite an earlier fragment.
6. Show the result, one production judgment, and one decision question. Translate every internal status into customer language.
7. Local selection, compare, expand, focus, or draft annotation remains component-only state.
8. A primary action sends a human-readable follow-up through `window.openai.sendFollowUpMessage`.
9. ADCO re-reads current truth, checks the target Gate and authority, and rejects stale or conflicting input.
10. Only then register the source event/decision/feedback, create a new client-visible version when required, invalidate affected evidence, and show `confirmation-echo`.

If the host bridge is unavailable, the component must display the exact plain-language message the user can send in chat.

## Blocking decisions

Use `blocking-decision` only when progress genuinely depends on the user:

- ask one question;
- offer two or three mutually exclusive options;
- show the recommended option first;
- explain one concrete tradeoff and downstream effect per option;
- name who has authority to decide;
- do not bundle approval, send authorization, publishing, deletion, migration, payment, or global installation into a visual click.

The component action records conversation intent only. It cannot write `decisions.csv`, close a gap, pass a Gate, approve a deck, or authorize a send.

## Option comparison

Comparison criteria must be decision-relevant and comparable. For scored or numeric criteria, disclose definition, direction, unit, evaluator/source, unknown handling, and evidence status. Never turn unknown into zero or manufacture a score merely to make the view more visual.

Show the recommendation and its reasoning, but keep all two or three options inspectable. A visual recommendation never becomes the selected route until the user submits intent and ADCO validates it.

## Optional Data Analytics evidence

Data Analytics can complement, but never replace, the Visualizations interaction surface. Use it only when the user needs a real quantitative answer such as a trend, distribution, ranking, correlation, composition, workload, coverage rate, or repeated-row audit.

Use a native analytical table or chart only when all are true:

- the input is structured data or an exact reviewed lookup;
- the calculation, grouping, unit, denominator, exclusions, and unknown handling are explicit;
- the renderer's required query/source provenance is real and reproducible;
- the result changes or supports the current decision more clearly than a short table;
- the current host mode supports that analytical renderer.

Interactive Data Analysis charts are best suited to bar, line, pie, and scatter views; other chart forms may be static. Keep the analysis code, assumptions, and source reviewable. Do not invent SQL lineage, scores, time series, or zeros merely to satisfy a widget contract.

Keep ownership separate:

- Visualizations explains the ADCO state, options, downstream effects, and action.
- Data Analytics supplies a bounded numeric evidence view when warranted.
- The Visualizations action still sends the conversation intent and remains the only component mapped to the ADCO decision loop.

For status, Gate state, version lineage, authority, asset/PPT review, and ordinary creative comparison, use the Visualizations surface or its fallback; Data Analytics is normally unnecessary.

## Asset and PPT review

For `asset-review` and `ppt-slide-review`:

1. Resolve the exact active artifact and physical file.
2. Verify version and hash against current truth, version map, and artifact index.
3. For PPT review, verify PPTX, PDF, slide preview, text extract, and editability evidence derive from the same exact-current PPTX/version.
4. Embed only an inspected preview with useful alternative text. Do not show a stale alias, contact sheet, unregistered browser image, or previous export as current.
5. Bind every finding to slide/page plus region or object description, severity, evidence, proposed change, and affected requirement.
6. A visual annotation is staged feedback only.
7. On submit, register it through the normal source-event and feedback path. Material client-visible changes create a new version and invalidate stale package/Gate bindings.

If the preview is missing or stale, render the missing evidence and safe next action instead of a fake placeholder image.

## Feedback return

A feedback action must send a readable intent containing:

- the work being reviewed in normal language;
- slide/page and region when applicable;
- the user's selected option or annotation text;
- requested action;
- the visible content likely to change;
- a request for ADCO to check the latest project state before recording it.

ADCO then records feedback in `source_events.csv` and `AD-creative/feedback/feedback_map.csv`, maps affected artifacts and requirements, marks invalid evidence stale, and creates the next-version route. If the target is no longer current, preserve the feedback but do not silently apply it to the newer version.

The confirmation echo must stay user-facing. Say `已记录你的选择`, `将保留`, `需要重新检查`, and `下一步`. Do not show Gate IDs, artifact IDs, hashes, receipts, locks, write owners, or validator vocabulary.

## Spec, renderer, and registry

The installed Skill carries:

    schemas/chat-visualization-spec.schema.json
    assets/visualizations/surface-registry.json
    assets/visualizations/decision-surface.css
    assets/visualizations/decision-surface.js
    scripts/adco_visualization.py
    fixtures/chat-visualization/

Validate:

    python3 scripts/adco_visualization.py validate <spec.json> --project-root <project-dir>

Render the text fallback:

    python3 scripts/adco_visualization.py render-fallback <spec.json>

Render for the current supported conversation:

    python3 scripts/adco_visualization.py render-html <spec.json> \
      --project-root <project-dir> \
      --output <current-thread-visualization-dir>/<lowercase-title>.html

Run the contract and hostile-input suite:

    python3 scripts/adco_visualization.py self-test

Resolve these paths relative to this installed Skill root. Do not assume the source repository is present after global installation.

## Rendering and accessibility gate

Before showing a fragment, verify:

- spec validation passes;
- source artifact paths, lifecycle, versions, and hashes are current;
- action count is one or two;
- every action targets the current decision/Gate;
- no action directly writes authoritative state or makes forbidden claims;
- the fallback preserves current stage, exact work, decision, downstream effect, and next action;
- hostile text cannot escape HTML or JSON boundaries;
- no network access, `fetch`, WebSocket, external script, or untrusted iframe;
- 736 px and 320 px light/dark layouts have no clipping, horizontal overflow, nested scroll, or invisible focus;
- keyboard selection and action submission work;
- SVG/image/diagram content has an accessible text summary;
- reduced-motion preferences are respected.

If the fragment cannot be read back or visually inspected, report visualization rendering as `未验证`.

## Local dashboard boundary

The existing local dashboard remains a durable, read-only operational fallback and file browser. It may expose the same current files, but it must not copy the inline component, receive its click as authority, or become a second source of truth. This Visualizations upgrade does not redesign the dashboard.

## Official reference

- OpenAI Visualizations: https://learn.chatgpt.com/docs/visualizations
- File preview and annotations: https://learn.chatgpt.com/docs/artifacts-viewer
