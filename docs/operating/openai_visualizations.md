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
| OpenAI Visualizations / `@Visualize` | stage, logic, choices, inspection context, feedback impact, confirmation echo | a compact interactive view makes the current ADCO decision clearer | source truth, approval, Gate passage, send authorization |
| Data Analytics | reviewed numeric evidence | a real trend, distribution, ranking, correlation, composition, coverage, or repeated-row audit supports the decision | generic workflow state, invented scores, UI controls, authority |
| File preview and annotations | exact page/slide/file inspection | a document, deck, PDF, image, code, or Markdown artifact needs region-specific review | silently changing the current version or treating a comment as approval |
| Markdown/table/Mermaid | universal fallback | Visualizations is unsupported, unavailable, failed, or unnecessary | hiding required decision fields |
| Existing local dashboard | durable local fallback and file browser | the user wants a persistent local operational view | duplicating inline controls or receiving authoritative clicks |

Visualizations is the primary interaction layer. Data Analytics and file preview provide evidence to it when appropriate.

## Product model

Each conversation turn may show one small stage-specific surface:

    exact-current control plane
    -> versioned visualization spec
    -> validation
    -> thread-scoped HTML fragment
    -> local inspect/select/annotate state
    -> human-readable follow-up
    -> controller stale/hash/Gate/authority validation
    -> authoritative write through existing ADCO paths
    -> read-only confirmation echo

No component action directly edits the control plane.

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
2. a real fragment is generated in the active thread visualization directory and visually audited;
3. stale source, mismatched hash, action overflow, authority escalation, unsafe path, hostile text, and incomplete fallback are rejected;
4. source and packaged Skill trees match;
5. the globally installed Skill tree matches the source tree;
6. existing ADCO tests and distribution checks pass;
7. an independent forward test and cold review return no blocking findings.

## Sources

- OpenAI Visualizations: https://learn.chatgpt.com/docs/visualizations
- OpenAI file preview and annotations: https://learn.chatgpt.com/docs/artifacts-viewer
- ChatGPT data analysis: https://help.openai.com/en/articles/8437071-advanced-data-analysis-chatgpt
