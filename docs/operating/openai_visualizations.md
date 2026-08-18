# OpenAI Visualizations boundary

OpenAI Visualizations is an optional ChatGPT product capability. ADCO may use it
only when the current composer exposes `@Visualize` or an actual Visualize tool
is callable. Availability depends on account, workspace, platform, and rollout.

## What happened in earlier RTBC work

ADCO could generate and test a local HTML fragment, but the current conversation
did not have a verified native Visualize capability or a visible mounted result.
No RTBC visualization was promoted to a durable project artifact. Therefore the
user saw neither a persistent visual nor a reliable fallback. A temporary
`.codex/visualizations` file, when present, was only cache/preview evidence.

This is now fail-visible:

- local preview success is labeled `USER_VISIBLE=UNVERIFIED`;
- the renderer no longer prints a private inline-mount directive;
- Markdown, table, Mermaid, image, or file preview is returned in the same
  response whenever native Visualizations is unavailable or unverified;
- durable truth stays in the project, not in chat cache;
- a persistent Site/App is considered only when the user explicitly needs a
  reusable application rather than a one-turn explanation.

## Surface selection

| User need | Default | Optional upgrade |
|---|---|---|
| Static logic or feedback impact | Mermaid | native Visualize when interaction matters |
| Two or three creative routes | table | native comparison when visibly available |
| One image or slide | exact preview plus findings | bounded native annotations |
| Real quantitative evidence | table/chart | Data Analytics with reproducible definitions |
| Persistent workspace | project artifact | explicitly requested Site/App |

Visualizations is not a Gate, approval, source of truth, or delivery receipt. It
is normally a snapshot rather than a live dashboard. Codex CLI and IDE do not
render ChatGPT Visualizations; desktop preview availability is account-specific.

## Offline verifier

The bundled `adco.chat-visualization@1.0` schemas, fixtures, renderer, and browser
checks remain useful for validating source bindings, escaping, accessibility,
and complete fallbacks. They do not prove that the user saw a native component.

```text
python3 scripts/adco_visualization.py validate <spec.json> --project-root <project>
python3 scripts/adco_visualization.py render-fallback <spec.json> --project-root <project>
python3 scripts/adco_visualization.py render-html <spec.json> \
  --project-root <project> --output <temporary-preview.html>
python3 scripts/adco_visualization.py self-test
```

Only a visibly rendered native result counts as native delivery. Otherwise the
complete text fallback is the user-visible result.

Official reference: https://learn.chatgpt.com/docs/visualizations
