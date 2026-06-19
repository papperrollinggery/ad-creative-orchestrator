# Workspace Hygiene Protocol

This protocol keeps ADCO runs from polluting the repo or leaving stale execution state.

## What Counts As Dirty

Expected work:

- tracked source, docs, template, or test changes for the current task
- project-local AD-creative artifacts created by an explicit command

Pollution:

- `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `*.pyc`
- untracked scratch files in the repo root
- validation output written outside `/tmp` or `AD-creative/workspaces/<work_id>/`
- consumed Codex Thread rows that are not archived or reconciled
- source template and packaged mirror drift

## Default Plan

Before work:

```text
git status --short --untracked-files=all
adco hygiene <project_dir>
```

During work:

```text
Use /tmp for smoke projects and generated validation fixtures.
Use AD-creative/workspaces/<work_id>/ for isolated project drafts.
Workers write only receipts unless the lane plan grants exact write paths.
Do not create files in the repo root for one-off verification.
```

After work:

```text
Run relevant tests.
Delete Python caches.
Archive consumed Codex Threads.
Run adco hygiene <project_dir>.
Report remaining tracked changes explicitly.
```

## Command Contract

`adco hygiene` is read-only. It reports:

```text
tracked git changes
untracked git files
cache/temp pollution
active thread registry rows
cleanup plan
```

It must not delete files, reset git state, or archive threads by itself. The main/control thread performs cleanup and reports evidence.
