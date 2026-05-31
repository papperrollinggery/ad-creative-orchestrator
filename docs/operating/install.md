# Install

Status: source install supported

## Recommended

Install from the repository root:

```bash
python3 -m pip install -e .
```

Then use:

```bash
adco --help
adco-init <project_dir>
adco sample <project_dir>
adco run <project_dir> --material <material_file_or_folder>
adco goal-plan <project_dir> --title "<goal title>" --objective "<goal objective>"
adco-check
```

## Why Editable Install

This project is local-first and template-heavy. The supported install mode keeps the CLI connected to the checked-out `templates/`, `examples/`, `docs/`, and `skill_drafts/` directories.

Wheel packaging is intentionally not claimed yet. See `docs/operating/open_source_release_plan.md`.

## Verify

```bash
adco-check
make install-smoke
```

Expected:

```text
RUN_CHECKS=PASS
INSTALL_SMOKE=PASS
```

## Uninstall

```bash
python3 -m pip uninstall ad-creative-orchestrator
```
