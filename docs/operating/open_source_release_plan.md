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
| Install/run clarity | user can start without reading code | `README.md`, quickstart, launcher, operator CLI | PARTIAL |
| One-command verification | contributors can verify changes | `make check`, `tools/run_checks.py` | PASS |
| Safety model | client-visible risk is blocked | Gate policy, adversarial council, security doc | PASS |
| Example quality | examples prove workflow | Moncler and Qingling examples validate | PASS |
| Dashboard usability | non-developer can inspect state | dashboard audit PASS, Goal tab | PASS |
| Packaging | installable CLI | not packaged yet | TODO |
| GitHub readiness | license, contribution, security, roadmap | added core files | PASS |
| CI | automated checks on push | `.github/workflows/check.yml` | PASS once pushed |
| Public appeal | screenshots, demo, concise pitch | not built yet | TODO |

## Execution Order

1. Stabilize local checks and examples.
2. Initialize repository and commit baseline.
3. Package CLI.
4. Add screenshots/demo media.
5. Push repository so GitHub Actions can run remotely.
6. Publish public README with clear problem, demo, and safety story.
7. Iterate on issues from real users.

## Stop Conditions

- Do not upload real client materials.
- Do not make AI images client-visible without explicit evidence.
- Do not claim CI/GitHub release until a remote repository exists.
- Do not mark the long-term goal complete until the project is demonstrably usable and public-release ready.
