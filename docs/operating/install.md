# Install

Status: source and local package install supported

## Recommended

Install from the repository root:

```bash
python3 -m pip install .
```

Then use:

```bash
adco --help
adco --version
adco doctor
adco-init <project_dir>
adco demo [project_dir]
adco sample <project_dir>
adco support-bundle <project_dir>
adco open-dashboard <project_dir>
adco run <project_dir> --material <material_file_or_folder>
adco goal-plan <project_dir> --title "<goal title>" --objective "<goal objective>"
adco-check
```

## Development Install

Use editable mode while changing templates or code:

```bash
python3 -m pip install -e .
```

Runtime templates and the project skill draft are also packaged, so `adco sample` and `adco-init` work after normal `pip install .`.

## Verify

```bash
adco-check
adco --version
adco doctor
make install-smoke
make package-smoke
make dist-check
```

Expected:

```text
RUN_CHECKS=PASS
adco 0.1.0
ADCO_DOCTOR=PASS
INSTALL_SMOKE=PASS
PACKAGE_SMOKE=PASS
DIST_CHECK=PASS
```

## Uninstall

```bash
python3 -m pip uninstall ad-creative-orchestrator
```
