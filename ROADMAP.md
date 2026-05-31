# Roadmap

## Goal

Make Ad Creative Orchestrator a usable, credible, open-source project for Codex-first advertising creative operations, with the quality bar expected of a project that can earn 2k+ GitHub stars.

## Now

- Local project template and non-developer launcher
- Installable `adco` CLI with `demo`, `sample`, `doctor`, `support-bundle`, and dashboard commands
- Dashboard, Goal tab, and direct dashboard open flow
- Intake, reference, visual, PPT, client-pack, and handoff Gates
- Goal iteration plans and adversarial council Gate policy
- Example projects, demo screenshots, first-run transcript, and regression checks
- Local release gate covering source checks, wheel inspection, editable install, and normal package install

## Next

1. Add a GitHub remote and push `main`.
2. Verify GitHub Actions runs `make release-check` on Python 3.10 and 3.12.
3. Run the first external-user trial from `adco demo` to real project intake.
4. Turn external trial issues into focused CLI/dashboard/docs improvements.

## Done In Local Baseline

- Package the operator as an editable install CLI.
- Package runtime templates and skill draft for normal `pip install .`.
- Add desktop/mobile dashboard screenshots.
- Add a minimal sample project generator.
- Add a one-command demo flow.
- Add direct dashboard open command.
- Add install/release diagnostics and sanitized support bundle.
- Add structured regression coverage for every Gate command.
- Add issue templates and a GitHub release checklist.
- Add GitHub Actions workflow for the full release gate.
- Add documentation for real-world adoption patterns.
- Expand Gate tests into fixture-level positive cases for PPTX and image PASS paths.
- Add richer demo media for the first-run flow.
- Add wheel content inspection and local release-check target.

## Not Planned

- SaaS hosting
- automatic client deck sending
- automatic upload of client materials to external platforms
- automatic global skill installation
- replacing human creative judgment
