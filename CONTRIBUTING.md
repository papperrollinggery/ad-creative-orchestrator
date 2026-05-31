# Contributing

## Project Contract

Ad Creative Orchestrator is file-driven. Changes must preserve:

- project state in `AD-creative/orchestrator/`
- human handoff in `AD-creative/handoff/`
- gate evidence in `AD-creative/gates/`
- no client-visible artifact without traceable requirement, asset, reference, and Gate

## Local Check

Run:

```bash
make check
```

Equivalent:

```bash
python3 tools/run_checks.py
```

The check covers syntax, goal workflow regression, template validation, both example projects, and dashboard audit.

## Change Rules

- Keep client data local.
- Do not add real client confidential material to examples.
- Do not mark AI images client-visible without explicit approval evidence.
- Do not skip adversarial council notes for stage Gates.
- Do not commit Python caches, temporary generated images, or local environment folders.

## Useful Entry Points

```bash
python3 tools/ad_creative_operator.py run <project_dir> --material <material>
python3 tools/ad_creative_operator.py goal-plan <project_dir> --title <title> --objective <objective>
python3 tools/ad_creative_operator.py audit-dashboard <project_dir> --render
python3 tools/validate_project.py <project_dir>
```
