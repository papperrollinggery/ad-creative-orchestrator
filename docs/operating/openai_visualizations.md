# OpenAI Visualizations integration

Status: implementation contract for the unreleased ADCO Skill upgrade.

## Goal

Make the current Codex or ChatGPT conversation the clearest place to understand and operate ADCO. The user should be able to see:

1. where the project is;
2. what exact work is under review;
3. what decision or feedback is needed;
4. what the recommended choice changes downstream;
5. what ADCO actually recorded after revalidation.

The integration upgrades the existing Skill. It does not introduce a new product or replace project files.

## Capability composition

| Layer | Primary job | Use when | Do not use for |
| --- | --- | --- | --- |
| OpenAI Visualizations | stage, logic, choices, inspection context, feedback impact, confirmation echo | a compact interactive view makes the current ADCO decision clearer | source truth, approval, Gate passage, send authorization |
| Creative Production native Widgets | image-led style, shot, route, and mood-board intake/review | the installed Widget matches the exact visual decision and real images exist | generic workflow state, authority, or replacing project files |
| Data Analytics | reviewed numeric evidence | a real trend, distribution, ranking, correlation, composition, coverage, or repeated-row audit supports the decision | generic workflow state, invented scores, UI controls, authority |
| File preview and annotations | exact page/slide/file inspection | a document, deck, PDF, image, code, or Markdown artifact needs region-specific review | silently changing the current version or treating a comment as approval |
| Markdown/table/Mermaid | universal fallback | Visualizations is unsupported, unavailable, failed, or unnecessary | hiding required decision fields |
| Existing local dashboard | durable local fallback and file browser | the user wants a persistent local operational view | duplicating inline controls or receiving authoritative clicks |

Visualizations is the default compact interaction layer. Creative Production is preferred for image-led selection/review. Data Analytics is reserved for real quantitative evidence; neither is a universal card renderer.

For asset review, physical path and hash verification only prove which bytes were inspected. The visualization must also classify the item as a `real-candidate` or `illustrative-placeholder`. Placeholders are visibly labeled and cannot offer a use-confirmation action. A real candidate reaches `可进入使用确认` only after its source, usage authorization, and target-channel fit are all confirmed and each confirmed status binds a separate current evidence record; the preview cannot certify itself.

## ADCO surface ladder

| Need | Use first | Escalate only when |
| --- | --- | --- |
| One image or slide review | inline preview with region findings and one feedback action | annotations or cross-page context no longer fit legibly |
| 3-8 image-led routes | Creative Production Widget or image carousel | the collection becomes large, hierarchical, or repeatedly filtered |
| Large deck, storyboard, mood board, or annotation canvas | fullscreen MCP App / Widget | inline review cannot finish the task |
| Real observed curve | Data Analytics chart or focused inline SVG | assumptions must be adjustable or server tools must be called repeatedly |
| Adjustable scenario curves | stateful MCP App / Widget | the user needs bounded controls and recomputation |
| Static dependency or impact | Mermaid | state must change interactively |

The Skill may also encounter maps, calculators, simulations, audio/video, 3D, modals, file selection, and picture-in-picture. These remain optional specialist surfaces, not default ADCO chrome. Use them only when the user's task inherently needs geography, adjustable modeling, playback, spatial inspection, file input, or a live parallel session.

## Product model

Each conversation turn may show one small stage-specific surface:

    exact-current control plane
    -> versioned visualization spec
    -> validation
    -> thread-scoped HTML fragment
    -> exact ::codex-inline-vis directive in the response
    -> local inspect/select/annotate state
    -> human-readable follow-up
    -> controller stale/hash/Gate/authority validation
    -> authoritative write through existing ADCO paths
    -> read-only confirmation echo

No component action directly edits the control plane. Writing the fragment is not delivery: the current conversation must visibly mount the directive. A Markdown file link, browser screenshot, and renderer success are test evidence, not the user interface.

## First-release surfaces

- current status and P0-P8 stage context;
- phase/Gate dependency and invalidation flow;
- one real blocking decision with two or three options;
- creative direction or route comparison;
- requirement-to-asset evidence review;
- exact-current PPT/PDF slide review;
- client-pack/send-readiness inspection without send action;
- feedback impact and post-write confirmation echo.

Inline views have one primary action and at most one secondary action. Fullscreen is reserved for dense slide, lineage, reference, or feedback inspection.

## Data and authority

Every visible current claim must resolve to current truth, version map, active artifact index, physical SHA-256, latest exact-target Gate evidence, or registered feedback. Missing, stale, ambiguous, inactive, or path-unsafe evidence is displayed as blocked or unverified.

Selection and annotation remain presentation state until submitted as conversation intent. ADCO then re-reads the current project. Only the controller may update decisions, gaps, feedback, versions, artifacts, Gate results, package bindings, FinalDelivery, or send readiness.

## Quality and accessibility

- 736 px and 320 px layouts;
- light and dark host themes;
- keyboard operation and visible focus;
- no color-only state;
- no nested scrolling or deep navigation;
- text alternative for every visual;
- no external network or untrusted iframe;
- HTML and embedded JSON escaping;
- complete fallback with the same stage, evidence, decision, effect, and next action.

## Release acceptance

The upgrade is releasable only when:

1. the schema, registry, renderer, writeback validator, positive fixtures, and negative fixtures pass;
2. a real fragment is generated in the active thread visualization directory, wrapped with the bundled official renderer, and audited at 736 px light plus 320 px dark;
3. the current Codex conversation visibly mounts `::codex-inline-vis{file="<title>.html"}` and a primary action sends one readable follow-up back to the conversation;
4. stale source, mismatched hash, action overflow, authority escalation, unsafe path, hostile text, and incomplete fallback are rejected;
5. source and packaged Skill trees match;
6. the globally installed Skill tree matches the source tree;
7. existing ADCO tests and distribution checks pass;
8. an independent forward test and cold review return no blocking findings.

## Sources

- OpenAI Visualizations: https://learn.chatgpt.com/docs/visualizations
- OpenAI Apps SDK UI principles: https://developers.openai.com/apps-sdk/concepts/ui-guidelines
- OpenAI Apps SDK examples: https://github.com/openai/openai-apps-sdk-examples
- MCP Apps examples and host lifecycle: https://github.com/modelcontextprotocol/ext-apps
- OpenAI file preview and annotations: https://learn.chatgpt.com/docs/artifacts-viewer
- ChatGPT data analysis: https://help.openai.com/en/articles/8437071-advanced-data-analysis-chatgpt
