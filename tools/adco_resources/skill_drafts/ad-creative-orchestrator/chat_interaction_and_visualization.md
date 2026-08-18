# Chat Visualization Boundary

Read this file only when a visual relationship, comparison, timeline, asset, or
slide would be materially clearer than concise prose.

## Capability check first

OpenAI Visualizations is a product capability, not a file format. Use it only
when the current composer visibly exposes `@Visualize` or the current tool
surface provides an actual Visualize capability. Account, workspace, platform,
and rollout can differ.

The Skill cannot activate Visualizations by writing HTML, creating a
`.codex/visualizations` directory, or printing a private/raw directive. Those
actions prove only that a local preview exists. They do not prove that the user
saw anything in the conversation.

Route in this order:

1. If a small Mermaid diagram, table, file preview, or ordinary image answers
   the question, use it directly in the response.
2. If `@Visualize` is actually available and interaction improves the task,
   invoke that native capability and verify that the result is visible.
3. If native visualization is unavailable or fails, immediately return the
   complete Markdown/table/Mermaid fallback. Do not ask the user to switch
   clients and do not silently leave only an HTML file.
4. Use a Site or other explicitly requested durable app only when the user needs
   persistent, reusable application state. Do not escalate a one-turn review.

Codex CLI and IDE surfaces do not render ChatGPT Visualizations. Desktop preview
availability is account-dependent. A visualization is normally a snapshot, not
a live project dashboard.

## Persistence and project truth

Visualizations never become ADCO storage, approval, delivery, or source truth.
Durable state remains in the exact project files. If the user explicitly asks to
preserve a visual, save one reviewed spec or exported artifact in the project;
do not copy the same source media into the chat cache, meeting packs, QA folders,
and delivery folders.

Treat `.codex/visualizations` as an ephemeral host/cache location. Never use it
for project evidence, FinalDelivery, or a long-lived asset library. A missing
cache entry after the task does not mean project truth was lost; it means no
durable visual artifact was promoted.

## Smallest useful surface

| Need | Default | Native upgrade only when available |
|---|---|---|
| Explain dependencies or feedback impact | Mermaid | interactive exploration is needed |
| Compare 2-3 routes | table | interaction materially changes the decision |
| Review one image | exact image/file preview plus findings | bounded annotations improve review |
| Review a deck | exact page/slide preview plus findings | many pages must stay inspectable |
| Show real numbers | table or simple chart | reproducible Data Analytics evidence exists |
| Keep a reusable workspace | project artifact | user explicitly requests a durable Site/App |

Do not manufacture scores, time series, progress percentages, maps, animation,
3D, or interactivity for decoration.

## Source binding

Every current claim must resolve to current project truth:

- phase and next action: current truth, work items, and open gaps;
- artifact: active/current artifact row plus the physical SHA-256;
- version: unique current version plus exact file;
- Gate: latest applicable result bound to the same target/hash;
- feedback: registered source event and affected requirements/artifacts.

Reject missing files, path traversal, symlink escape, stale hashes, ambiguous
current versions, inactive artifacts presented as current, and placeholders
presented as usable production assets.

The frontstage is for the user: show the work, judgment, options, consequences,
and next action in normal language. Keep artifact IDs, hashes, receipts, locks,
and validator vocabulary backstage.

## Asset and slide review

For one image or slide:

1. Resolve and inspect the exact-current bytes.
2. Name its intended advertising job before discussing technical status.
3. Describe the customer moment, product proof, and brand memory.
4. Bind each finding to a visible region and classify it as keep, revise, or
   recheck on real material.
5. Separate `real-candidate` from `illustrative-placeholder`. A placeholder can
   preserve only a composition principle; it cannot prove people, product,
   emotion, pack, crop, rights, channel fit, or production usability.
6. Submit feedback as a readable chat message. Re-read current truth before any
   authoritative project write.

No visual click can approve a deck, pass a Gate, authorize sending, install
globally, move/delete files, or publish externally.

## Bundled offline verifier

The installed Skill retains the `adco.chat-visualization@1.0` schema, fixtures,
and renderer as an offline preview and hostile-input verifier. It is not a host
integration and does not redesign the dashboard.

```text
python3 scripts/adco_visualization.py validate <spec.json> --project-root <project>
python3 scripts/adco_visualization.py render-fallback <spec.json> --project-root <project>
python3 scripts/adco_visualization.py render-html <spec.json> \
  --project-root <project> --output <temporary-preview.html>
python3 scripts/adco_visualization.py self-test
```

`render-html` reports `USER_VISIBLE=UNVERIFIED` and the preview path. It never
prints an inline-mount directive. The fallback is the required user-visible
result unless native `@Visualize` was actually invoked and visibly rendered.

If a verified native component sends feedback through
`window.openai.sendFollowUpMessage`, treat that message as conversation intent
only. ADCO must re-read the target and authority before writing anything.

## Acceptance

- The first response already answers the question without requiring a click.
- A complete text alternative exists.
- Exact current assets and facts are used; no invented metrics or UI.
- Native availability and user-visible rendering are separately verified.
- Offline renderer success is never reported as native display success.
- Durable project records do not depend on a chat cache.

Official reference: https://learn.chatgpt.com/docs/visualizations
