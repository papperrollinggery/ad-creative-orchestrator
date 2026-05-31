# Changelog

## Unreleased

- Added `goal-plan` command for durable goal iteration records.
- Added adversarial council Gate policy: clean Gates without council evidence downgrade to `PARTIAL_PASS`.
- Added Goal tab to the local dashboard.
- Added `tools/test_goal_workflow.py` regression checks.
- Added `tools/run_checks.py` unified verification entry point.
- Added open-source readiness files: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `ROADMAP.md`, `.gitignore`, `Makefile`, `requirements.txt`.
- Added GitHub Actions check workflow plus issue and pull request templates.
- Added `pyproject.toml` and console scripts: `adco`, `adco-init`, `adco-validate`, `adco-check`.
- Added source install guide.
- Added `make install-smoke` for editable install verification.
- Added public demo script and desktop/mobile dashboard screenshots.
- Added `adco sample` bundled sample project generator and regression check.
- Added `tools/test_gates.py` structured Gate regression coverage.
- Added GitHub release checklist with local and remote gates.
- Added real-world adoption pattern documentation.
- Added optional positive Gate fixtures for real PNG visual QA and editable PPTX client-pack PASS paths.
- Added generated first-run demo transcript and stale-check verification.
- Improved README public quickstart, value proposition, and safety model.
- Added `make release-check` local release gate.
- Added packaged runtime assets plus normal `pip install .` smoke verification.
- Updated project-local skill draft with installed CLI and release-check entry points.
- Added `adco doctor` install/resource/dependency/release diagnostic command.
- Added `adco --version` for issue reports and install diagnostics.
- Added `make dist-check` wheel content inspection for packaged templates, skill draft, metadata, and entry points.
- Upgraded GitHub Actions to run the full `make release-check` gate on Python 3.10 and 3.12.
- Hardened issue and pull request templates with version, doctor, reproduction, and release-gate evidence.
- Added `adco support-bundle` for sanitized bug-report diagnostics without client material text.
- Added `adco open-dashboard` to render and open the local operation dashboard directly.
- Added `adco demo` as a one-command sample project and dashboard demo.
- Updated the public roadmap to reflect current local release readiness and remote-release next steps.
- Added `adco validate` and `adco check` aliases for the existing validation and verification workflows.
- Updated public docs and templates to use `adco demo`, `adco validate`, and `adco check` as the primary paths.
- Added JSON output for `adco doctor`, `adco status`, and `adco validate`.
- Added `adco init` as the unified project initialization subcommand.
