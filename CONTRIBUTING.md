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
make release-check
```

Faster source-only loop:

```bash
adco check
make check
```

The release gate covers syntax, goal workflow regression, template validation, both example projects, dashboard audit, wheel inspection, editable install smoke, and normal package install smoke.

## Change Rules

- Keep client data local.
- Do not add real client confidential material to examples.
- Do not mark AI images client-visible without explicit approval evidence.
- Do not skip adversarial council notes for stage Gates.
- Do not commit Python caches, temporary generated images, or local environment folders.

## Useful Entry Points

```bash
adco docs
adco doctor
adco release-status
adco demo
adco run <project_dir> --material <material>
adco next <project_dir>
adco goal-plan <project_dir> --title <title> --objective <objective>
adco audit-dashboard <project_dir> --render
adco validate <project_dir>
```
