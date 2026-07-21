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

Visualizations availability depends on the active product surface, account, workspace, rollout, and whether `@Visualize` is selected or exposed. A thread-scoped visualization directory is only a host signal; writing a file there does not display it.

- Supported Codex conversation: build and validate `adco.chat-visualization@1.0`, render one fragment inside the current thread's `.codex/visualizations` directory, then emit `::codex-inline-vis{file="<title>.html"}` on its own line exactly where the visual should appear. Never substitute a Markdown file link.
- Unsupported Codex CLI, IDE, account, or failed render: use the spec's complete Markdown, table, or Mermaid fallback without asking the user to change clients.
- A generated HTML file, browser screenshot, Playwright pass, or successful tool result is not user-visible delivery. Do not claim the visual was shown until the host actually renders the inline surface in the conversation.
- Do not replace this path with raw HTML in the answer, a file link, an unrelated plugin card, or a Data Analytics widget that does not answer a genuine quantitative question.

## Host-native surface routing

Choose the surface by the user's current job, not by which renderer is easiest to call.

| User job | First choice | Use when | Do not use when |
| --- | --- | --- | --- |
| Understand a static relationship | Mermaid | labeled nodes and edges fully explain it | adjustable state, image inspection, or direct choice is needed |
| Make one decision or inspect one bounded state | Codex inline Visualizations | a compact choice, phase rail, impact path, timeline, or review surface materially reduces ambiguity | the result is merely decorative or repeats the reply |
| Choose visual language, shots, or mood-board routes | Creative Production native Widget | the installed tool matches the exact intake/review job and can return a readable conversation selection | generic project status, approvals, or control-plane evidence |
| Examine a real numeric trend, composition, ranking, or distribution | Data Analytics native chart/table/artifact | reviewed structured data and reproducible definitions exist | invented scores, ordinary creative comparison, or status reporting |
| Explore a dense graph, large slide set, or long-lived editor | Fullscreen MCP App / Widget | the task genuinely needs persistent state, repeated tool calls, or deep spatial exploration | a single inline decision can finish the job |

Creative Production and Data Analytics are optional host capabilities. Feature-detect or inspect the callable tool surface; preserve the same user question in the fallback. Never make plugin availability a project blocker.

## Capability router for ADCO

OpenAI's conversation UI can support more than cards: charts and curves, maps, diagrams, calculators, simulations, image-rich carousels, audio/video players, 3D views, file selection, modals, fullscreen workspaces, and picture-in-picture sessions. Availability does not make each form appropriate for ADCO. Route by the user's decision and the amount of state that must remain visible:

| ADCO job | Default surface | Upgrade when | User-visible result |
| --- | --- | --- | --- |
| Review one current image or one slide | inline `asset-review` or `ppt-slide-review` | multiple views must stay comparable or annotations become dense | exact inspected preview, plain-language region findings, one feedback action |
| Compare 3-8 image-led routes | Creative Production mood-board/style/shot Widget or image carousel | the set is larger, hierarchical, or repeatedly filtered | consistent thumbnails, title, at most two lines of relevant metadata, one choice per item |
| Review a large image set, long deck, storyboard, or spatial annotation set | fullscreen MCP App / Widget | only when one bounded inline review is no longer legible | visual canvas or gallery plus the native conversation composer |
| Show a real numeric trend | Data Analytics chart or a focused inline SVG plot | adjustable assumptions or repeated server calls are required | labeled axes, units, source definition, visible values, text alternative |
| Compare adjustable scenarios | stateful MCP App / Widget | the user must change inputs and see curves recompute | bounded controls, overlaid scenario curves, assumptions, readable selected state |
| Explain schedule, dependencies, or feedback effects | Mermaid for static logic; inline timeline/lanes for interactive emphasis | a dense graph needs repeated exploration | labeled relationships, current point, preserved and affected work |
| Continue a live playback, teaching, or review session while chatting | picture-in-picture App | the activity genuinely continues in parallel with conversation | persistent compact player/session that responds to chat |

Do not use maps, 3D, PiP, animation, or charts as decoration. Do not manufacture numeric scores, time series, confidence curves, or progress percentages from qualitative project state. The first render must already answer the user's current question; interaction deepens it rather than revealing the basic answer.

### Curve and chart rule

Use a curve only when named numeric observations or an explicitly labeled simulation exist.

- For exact reviewed observations, show the plot first. Label axes, units, important points, missing values, denominator, and source definition. Use a native Data Analytics line/scatter view when available and reproducible.
- For a small exact dataset already bound to the visualization spec, a focused inline SVG is acceptable. Keep one plot, directly label important values, expose a keyboard-readable selected value, and provide a text/table fallback.
- For adjustable assumptions, use a calculator or scenario-modeler App with bounded native controls and overlaid curves. Mark simulated values as scenarios, not facts, and keep input state separate from authoritative project records.
- For schedules and production timing, use aligned lanes on one time axis rather than a decorative smooth curve.

### Image-review rule

Image review can be completed inside the conversation when the target and feedback remain bounded:

1. Resolve and inspect the exact-current image or slide; verify path, version, and hash.
2. Show the preview at a useful size with alt text and a caption naming what is under review.
3. Bind each finding to a visible region or object description. Use coordinate overlays only when their geometry is verified against that exact preview; otherwise use a clear region label beside the image.
4. Let local selection, zoom, compare, or draft annotation remain presentation state.
5. Submit one readable feedback message to the conversation. ADCO revalidates the target before recording or changing anything.

Before rendering `asset-review`, classify the inspected item as either `real-candidate` or `illustrative-placeholder`. This is structured source metadata, not a visual guess.

- A real candidate must separately state whether its source, usage authorization, and target-channel fit are confirmed. Only a real candidate with all three confirmed may show `可进入使用确认`; the user still decides whether to use it.
- An illustrative placeholder must be visibly labeled `演示占位图`, show `暂不能确认使用`, and offer a route to provide or locate a real candidate. It must never inherit `画面检查通过`, authorization, channel-readiness, or use-selection language merely because its local file and hash are valid.
- Physical file verification proves which bytes were inspected. It does not turn a generated fixture, mockup, contact sheet, or placeholder into a licensed production asset.

An ADCO `asset-review` is not a generic file-status card. Its first screen must follow the advertising judgment order:

1. State the image's role in the proposal or campaign.
2. Read the customer moment, product proof, and brand memory it must create.
3. Mark visible regions as `保留`, `调整`, or `待真实素材复查`; verified coordinates may appear as focusable image hotspots.
4. Show how the same creative direction lands in the named target formats, normally including the relevant horizontal, feed, and vertical placements.
5. Keep source, direct-use authorization, channel fit, and current usability together under a later `使用前提` section.
6. Return a creative action such as preserving a composition while replacing the candidate, not a generic approval action.

The `creative_review` object binds the asset role, customer moment, product proof, brand memory, and channel plan to current project JSON records. The renderer resolves every JSON Pointer and requires the displayed value to equal the structured source value. These bindings remain backstage; the user sees the advertising intent, visual judgment, placement consequence, and next creative action. A placeholder may preserve a composition principle, but it cannot prove a person, product, emotion, packaging detail, crop, or production usability.

Use `binding_mode: fixture-placeholder` only for an explicitly illustrative fixture. A real candidate must use `binding_mode: adco-control-plane` and resolve the same project/version/bytes through `project.yml`, `current_truth.md`, the unique current `version_map.csv` row, `artifact_index.csv`, `source_events.csv`, `asset_authorizations.csv`, and an exact-asset PASS row in `gate_log.csv`. A `user_confirmation:<id>` must resolve to a `user`-owned, `user_confirmation`, `user_confirmed`, direct-use row and `approved_by=user`; the client form must analogously use the `client` authority class. Free-text names, local evidence files, and a prefix alone are never authority. A typed JSON record is supplemental context, not authority by itself. The renderer keeps the exact bytes read for SHA verification and uses those immutable bytes for structured-source parsing, SVG checks, and base64 rendering; it never reopens the path after verification.

Classify each region finding with both `scope` and `basis`. Placeholder findings may preserve only `composition-principle` from `composition-reading`; person, product, emotion, packaging, crop, and usage readiness remain revise/recheck findings with `placeholder-limitation`. Real-candidate findings use `real-file-observation`. A real candidate is usable only when every displayed channel placement is `verified-fit` from `real-candidate-check`.

For 3-8 visual alternatives, prefer a native image carousel or Creative Production mood-board Widget instead of shrinking every image into one inline card. For a long deck, large mood board, before/after slider, pixel-level annotation canvas, or repeated revision session, use fullscreen. File preview remains useful for opening the exact source at page/slide level, but it complements rather than replaces the ADCO feedback and version loop.

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

Keep the complete rendered fragment below 2 MB. If the exact-current source image would exceed the limit after embedding, register a smaller preview derivative in `artifact_index.csv`, bind it to the same version/source event, and inspect that derivative; never silently substitute an unregistered thumbnail.

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
6. Put the concise title and production judgment in normal Markdown, then emit the exact `::codex-inline-vis` directive. The fragment itself must not repeat the title or prompt.
7. Confirm that the current conversation visibly mounted the surface. If it did not, use the fallback and report rendering as `验证失败` or `未验证`; never point at the file as if it were the interface.
8. Local selection, compare, expand, focus, or draft annotation remains component-only state.
9. A primary action sends a human-readable follow-up through `window.openai.sendFollowUpMessage`.
10. ADCO re-reads current truth, checks the active decision and authority, and rejects stale or conflicting input.
11. Only then register the source event/decision/feedback, create a new client-visible version when required, invalidate affected evidence, and show `confirmation-echo`.

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

Asset actions are capability-limited to structured creative revision, creative recheck, or an eligible use selection. Reject any label or intent that asks to deliver, send, share, publish, upload, release, hand off, or otherwise operate outside review, regardless of which of the two action positions contains it.

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

For `asset-review`, the preview artifact also carries `review_classification`, `source_status`, `authorization_status`, and `channel_fit_status`. A confirmed status must bind a separate current source, authorization, or channel-fit record through `source_evidence_ref`, `authorization_evidence_ref`, or `channel_fit_evidence_ref`; the preview file cannot certify itself. The visible fields `asset-status`, `source-status`, `authorization-status`, `channel-fit`, and `availability` must be derived from those structured values. Never hand-write a more optimistic frontstage status, and never offer `submit-selection` until every required status and evidence binding is complete.

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
    scripts/adco_visualization_browser_audit.cjs
    fixtures/chat-visualization/

Validate:

    python3 scripts/adco_visualization.py validate <spec.json> --project-root <project-dir>

Render the text fallback:

    python3 scripts/adco_visualization.py render-fallback <spec.json> \
      --project-root <project-dir>

Render for the current supported conversation:

    python3 scripts/adco_visualization.py render-html <spec.json> \
      --project-root <project-dir> \
      --output <current-thread-visualization-dir>/<lowercase-title>.html

The successful render command prints the exact inline directive. Copy that directive into the response without a code fence or Markdown link:

    ::codex-inline-vis{file="<lowercase-title>.html"}

Run the contract and hostile-input suite:

    python3 scripts/adco_visualization.py self-test

Wrap a generated fragment with the bundled official Visualizations `scripts/render.py`, then run the browser interaction audit against that standalone wrapper:

    node scripts/adco_visualization_browser_audit.cjs <officially-wrapped-standalone.html> [screenshot-dir]

The browser audit checks 736 px light and 320 px dark layouts, reduced motion, horizontal overflow, nested scrolling, preview loading and alt text, keyboard option changes, and one follow-up message. It does not prove that the current conversation mounted the directive; host-visible delivery remains a separate check.

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
- the response contains the exact inline directive and the host visibly mounts it;
- the user can see the first useful state without clicking, change the primary selection with mouse and keyboard, and submit one readable follow-up;
- the visual does not repeat the response title, recreate host `.card` / `.btn` styling, or expose controller evidence.

If the fragment cannot be read back or visually inspected, report visualization rendering as `未验证`. If it passes browser checks but is not visibly mounted in the current conversation, report user-visible delivery as `验证失败`; browser validation and host delivery are separate gates.

## Local dashboard boundary

The existing local dashboard remains a durable, read-only operational fallback and file browser. It may expose the same current files, but it must not copy the inline component, receive its click as authority, or become a second source of truth. This Visualizations upgrade does not redesign the dashboard.

## Official reference

- OpenAI Visualizations: https://learn.chatgpt.com/docs/visualizations
- File preview and annotations: https://learn.chatgpt.com/docs/artifacts-viewer
