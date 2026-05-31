# Open Source Release Plan

Status: active goal plan

## Target

Make this project useful enough for public GitHub adoption. The quality target is a credible 2k+ star open-source project, not just a local script folder.

## Current Positioning

Ad Creative Orchestrator is a local-first, Codex-first workflow for advertising creative projects:

- messy client materials in
- structured requirements and gaps
- reference planning and evidence chain
- visual/image workflow
- client review/PPT handoff
- Gate review and adversarial council
- reusable project-local skill mining

## Release Requirements

| Area | Required State | Current Evidence | Status |
|---|---|---|---|
| Install/run clarity | user can start without reading code | README Quickstart, `adco --version`, `adco init`, `adco quickstart`, `adco demo`, `adco sample`, `adco doctor`, `adco release-status`, `adco docs`, `adco support-bundle`, `adco open-dashboard`, `adco status`, `adco next`, `adco validate`, `adco check`, launcher, operator CLI | PASS |
| One-command verification | contributors can verify changes | `adco check`, `make check`, `tools/run_checks.py` | PASS |
| Gate regression coverage | every Gate has a command-level regression path | `tools/test_gates.py`; PNG/PPTX positive fixtures when optional deps exist; no-deps skip path | PASS |
| Safety model | client-visible risk is blocked | Gate policy, adversarial council, security doc | PASS |
| Example quality | examples prove workflow | Moncler and Qingling examples validate | PASS |
| Dashboard usability | non-developer can inspect state | dashboard audit PASS, Goal tab, `adco open-dashboard` | PASS |
| Packaging | installable CLI | `pyproject.toml`, packaged runtime assets, `adco init`, `make install-smoke`, `make package-smoke`, `make dist-check` | PASS |
| Sample generation | user can try without real material | `adco demo`, `adco sample`, `tools/run_checks.py` temp sample | PASS |
| GitHub readiness | license, contribution, security, roadmap, release checklist, diagnostics | public remote, `docs/operating/github_release_checklist.md`, `adco --version`, `adco doctor --json`, `adco support-bundle`, `make dist-check`, `make release-check` | PASS |
| CI | automated checks on push | `.github/workflows/check.yml` runs `make release-check` on Python 3.10 and 3.12; GitHub Actions PASS | PASS |
| Public appeal | screenshots, demo, concise pitch | README pitch, `docs/assets/dashboard-*.png`, `docs/assets/first-run-transcript.md`, `docs/operating/demo_script.md` | PASS |
| Discoverability | GitHub users can understand, find, and verify the project quickly | status badge, project URLs, repo topics, GitHub-first quickstart | PASS |
| Adoption docs | new users can map the tool to real workflows | `docs/operating/adoption_patterns.md`; public clone trial to `adco quickstart` and validation PASS | PASS |

## Execution Order

1. Stabilize local checks and examples.
2. Initialize repository and commit baseline.
3. Harden source install and CLI smoke tests. Status: local smoke PASS.
4. Add screenshots/demo media. Status: initial desktop/mobile dashboard screenshots PASS.
5. Add minimal sample project generator. Status: `adco sample` local PASS.
6. Add structured Gate regression coverage. Status: no-deps Gate paths PASS.
7. Add GitHub release checklist. Status: local release gate ready.
8. Push repository so GitHub Actions can run remotely. Status: public remote PASS; GitHub Actions PASS.
9. Add real-world adoption patterns. Status: adoption doc PASS.
10. Expand Gate tests into PPTX/image positive fixtures. Status: local fixture PASS, no-deps skip PASS.
11. Add richer first-run demo transcript. Status: generated transcript PASS and stale-check wired into `run_checks`.
12. Publish public README with clear problem, demo, and safety story. Status: local README release pitch PASS.
13. Add single-command local release check. Status: `make release-check` PASS.
14. Add normal package install support. Status: `pip install .` smoke PASS.
15. Add install/release diagnostics. Status: `adco doctor` PASS.
16. Add CLI version diagnostics. Status: `adco --version` PASS.
17. Add wheel distribution inspection. Status: `make dist-check` PASS.
18. Add sanitized support bundle diagnostics. Status: `adco support-bundle` PASS.
19. Add direct dashboard open command. Status: `adco open-dashboard --no-open` PASS.
20. Add one-command demo. Status: `adco demo --no-open` PASS.
21. Add unified `adco validate` and `adco check` subcommands. Status: local and install smoke PASS.
22. Add JSON output for core diagnostics and validation. Status: `doctor/status/validate --json` local and install smoke PASS.
23. Add unified `adco init` subcommand. Status: source and install smoke PASS.
24. Add `adco next` next-action decision command. Status: source and package smoke PASS.
25. Reduce `adco check` JSON output noise while preserving JSON validation. Status: source and package smoke PASS.
26. Add `adco release-status` release readiness summary. Status: source and package smoke PASS.
27. Add `adco docs` local docs and quickstart locator. Status: source and package smoke PASS.
28. Refresh contributor, release, roadmap, and non-developer quickstart docs around current `adco` commands. Status: source and package smoke PASS.
29. Make wheel distribution inspection deterministic with no build isolation, a timeout, and a static manifest fallback. Status: source and package smoke PASS.
30. Add docs command regression check to keep onboarding docs on the installed `adco` path. Status: source and package smoke PASS.
31. Publish public GitHub remote and verify Actions on Python 3.10/3.12. Status: PASS.
32. Verify public clone trial from `git clone` to `adco demo` and validation. Status: PASS.
33. Add GitHub-first onboarding, project URLs, status badges, and repo topics. Status: PASS.
34. Add `adco quickstart` one-command first run with validation and next-step output. Status: PASS.
35. Iterate on issues from real users.

## Stop Conditions

- Do not upload real client materials.
- Do not make AI images client-visible without explicit evidence.
- Do not claim CI/GitHub release until a remote repository exists.
- Do not mark the long-term goal complete until the project is demonstrably usable and public-release ready.
