# Install

Status: source and local package install supported

## Recommended

Install from GitHub:

```bash
git clone https://github.com/papperrollinggery/ad-creative-orchestrator.git
cd ad-creative-orchestrator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

Install from an existing repository root:

```bash
python3 -m pip install .
```

Then use:

```bash
adco --help
adco --version
adco doctor
adco doctor --json
adco release-status
adco release-status --json
adco docs
adco docs --json
adco init <project_dir>
adco-init <project_dir>
adco quickstart [project_dir]
adco quickstart [project_dir] --json
adco demo [project_dir]
adco sample <project_dir>
adco support-bundle <project_dir>
adco support-bundle <project_dir> --json
adco open-dashboard <project_dir>
adco audit-dashboard <project_dir> --render --json
adco run <project_dir> --material <material_file_or_folder>
adco goal-plan <project_dir> --title "<goal title>" --objective "<goal objective>"
adco status <project_dir>
adco next <project_dir>
adco validate <project_dir>
adco validate <project_dir> --json
adco check
```

Compatibility entrypoints remain available: `adco-init`, `adco-check`, `adco-validate`.

## Install the Codex Skill

After the operator explicitly approves a global Skill update, install the packaged canonical copy and verify its hash:

```bash
adco install-skill
```

If the environment also loads the compatibility Skillshub catalog, synchronize that mirror through the same verified command:

```bash
adco install-skill --target ~/.skillshub/ad-creative-orchestrator
```

Both commands print the packaged source path plus source and target SHA-256 values. A successful install requires matching hashes.

## Development Install

Use editable mode while changing templates or code:

```bash
python3 -m pip install -e .
```

Runtime templates and the project skill draft are also packaged, so `adco init`, `adco sample`, and `adco-init` work after normal `pip install .`.

## Verify

```bash
adco check
adco --version
adco doctor
adco doctor --json
make install-smoke
make package-smoke
make dist-check
```

Expected:

```text
RUN_CHECKS=PASS
adco 0.3.1
ADCO_DOCTOR=PASS
INSTALL_SMOKE=PASS
PACKAGE_SMOKE=PASS
DIST_CHECK=PASS
```

## Uninstall

```bash
python3 -m pip uninstall ad-creative-orchestrator
```
