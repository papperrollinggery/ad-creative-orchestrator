# Install

Status: current GitHub Release, source checkout, and local package install supported

Platform boundary: Python 3.10+ on POSIX (currently macOS or Linux). Secure
project-artifact reads and writes require `dir_fd`, `O_DIRECTORY`, and
`O_NOFOLLOW`; unsupported platforms fail closed rather than silently weakening
the integrity contract.

Current public release: [`v0.3.2`](https://github.com/papperrollinggery/ad-creative-orchestrator/releases/tag/v0.3.2). The Release tag target is the authoritative source commit.

`v0.3.2` packages the public documentation set, so installed-wheel `adco docs` must list real README/operating-document paths and every listed file must exist.

## Recommended

Install the published wheel with `pipx`:

```bash
pipx install --force https://github.com/papperrollinggery/ad-creative-orchestrator/releases/download/v0.3.2/ad_creative_orchestrator-0.3.2-py3-none-any.whl
adco --version
adco doctor
```

Or install from a GitHub source checkout:

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

The installed CLI, packaged Skill draft, global Skill target, repository Skill draft, and the Skill embedded in the public Release wheel must have matching managed-file hashes. A matching version string alone is insufficient provenance.

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
adco docs
adco docs --json
make install-smoke
make package-smoke
make dist-check
```

Expected:

```text
RUN_CHECKS=PASS
adco 0.3.2
ADCO_DOCTOR=PASS
DOCS_MODE=source or installed with every listed document marked PASS
INSTALL_SMOKE=PASS
PACKAGE_SMOKE=PASS
DIST_CHECK=PASS
```

## Uninstall

```bash
python3 -m pip uninstall ad-creative-orchestrator
```
