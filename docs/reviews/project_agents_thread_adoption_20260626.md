# Project AGENTS.md Thread Adoption Record

Goal: 为 ad-creative-orchestrator 增加项目级 AGENTS.md 生成与验证机制

CONTROL thread: `019effce-da10-7e30-aa21-47a04f715ecb`

## Dispatch

| thread_class | actual_thread_id | environment | read_scope | write_scope | receipt |
| --- | --- | --- | --- | --- | --- |
| EXECUTION_WORKER | `019effd7-3513-7b71-93bc-2324ea278877` | isolated worktree `/Users/jinjungao/.codex/worktrees/e48f/ad-creative-orchestrator` | `tools/init_project.py`, `tools/ad_creative_operator.py`, `tools/validate_project.py`, `tools/run_checks.py`, `tools/check_distribution.py`, `tools/check_packaged_assets.py`, `tools/test_goal_workflow.py`, `templates/project/**`, `tools/adco_resources/templates/project/**`, `examples/**` | init/validate/operator/distribution/tests/template/example/transcript files only | received |
| DOCS_WORKER | `019effd7-569c-7902-8cdc-05f019b09d8c` | isolated worktree `/Users/jinjungao/.codex/worktrees/ab32/ad-creative-orchestrator` | README and operating docs; code read-only for consistency | `README.md`, `docs/operating/non_developer_quickstart.md`, `docs/operating/first_real_project_runbook.md`, `docs/operating/operating_manual.md` | received |
| QA_REVIEW_WORKER | `019effdd-6106-7333-a462-58013dd5f085` | local checkout, read-only | current diff and listed changed files | none | received |

Both worker receipts incorrectly listed the CONTROL source thread id as `thread_id`; CONTROL verified actual worker ids with `codex_app.read_thread` and uses the actual ids above.

## Adoption Decisions

Accepted from `EXECUTION_WORKER`:

- Add project-root `AGENTS.md` to source and packaged project templates.
- Add root `AGENTS.md` policy validation.
- Add regression coverage for missing policy and existing-file protection.
- Add `AGENTS.md` to doctor/distribution/template checks.
- Add `AGENTS.md` to existing example projects so examples pass without validator exemptions.
- Refresh first-run transcript after CLI output changes.

Rejected or modified from `EXECUTION_WORKER`:

- Rejected root-level merge suggestion path `AGENTS.md.adco-merge-suggestion`.
- Adopted `AD-creative/orchestrator/AGENTS.merge_suggestion.md` so merge guidance stays in the ADCO control plane.
- Rejected coupling validator policy snippets to `init_project.py`; final validation keeps policy checks in `validate_project.py`.
- Rejected receipt's incorrect `thread_id` field and used actual thread id from Codex thread tools.

Accepted from `DOCS_WORKER`:

- Document project-root `AGENTS.md` behavior.
- Document existing `AGENTS.md` non-overwrite and merge suggestion workflow.
- Document `VALIDATION=PASS` as structure/traceability only.
- Document required delivery gates and CONTROL ownership.

Modified from `DOCS_WORKER`:

- Updated wording to match final implementation path `AD-creative/orchestrator/AGENTS.merge_suggestion.md`.
- Rejected receipt's incorrect `thread_id` field and used actual thread id from Codex thread tools.

## Validation Evidence

CONTROL reran validation after adoption:

- `python3 tools/test_goal_workflow.py`
- `python3 tools/check_packaged_assets.py`
- `python3 tools/check_docs_commands.py`
- `python3 tools/render_demo_transcript.py --check`
- `python3 tools/validate_project.py templates/project`
- `python3 tools/validate_project.py examples/moncler_protocol_dry_run`
- `python3 tools/validate_project.py examples/simulated_qingling_outdoor_launch`
- `python3 tools/check_distribution.py`
- `python3 tools/run_checks.py`

## Cold Review

`QA_REVIEW_WORKER` returned `PASS with one non-blocking fix recommended`.

Findings and CONTROL resolution:

- P2: standalone `tools/init_project.py` printed `INIT=PASS` even when an existing custom `AGENTS.md` required merge. Resolved: raw init now runs `validate()` after copy, prints stats plus `INIT=CHECK` / `VALIDATION=CHECK`, and exits non-zero on errors.
- P3: `agents_policy_status()` could continue to print `MERGE_REQUIRED` after the user manually merged the required policy while the suggestion file still existed. Resolved: status now returns `MERGE_REQUIRED` only when the suggestion exists and the root policy is still incomplete.

Post-fix validation:

- `python3 -m py_compile tools/init_project.py tools/test_goal_workflow.py`
- `python3 tools/test_goal_workflow.py`
- raw `python3 tools/init_project.py <project-with-existing-AGENTS>` produced `INIT=CHECK`, `VALIDATION=CHECK`, and exit code `1`
- `python3 tools/validate_project.py templates/project`
- `python3 tools/validate_project.py examples/moncler_protocol_dry_run`
- `python3 tools/validate_project.py examples/simulated_qingling_outdoor_launch`

## Cleanup

CONTROL archived these worker/reviewer threads after receipt review:

- `019effd7-3513-7b71-93bc-2324ea278877`
- `019effd7-569c-7902-8cdc-05f019b09d8c`
- `019effdd-6106-7333-a462-58013dd5f085`

Cleanup status: complete.

---

# Creative Proposal / Quality Gate Thread Adoption Addendum

Goal update: 让 ad-creative-orchestrator 具备稳定产出专业广告创意方案内容的能力，并强化项目级规则加载、创意质量标准、反驳型审核和交付验证。

CONTROL thread: `019effce-da10-7e30-aa21-47a04f715ecb`

## Rebuttal Council Dispatch

| thread_class | actual_thread_id | environment | read_scope | write_scope | receipt |
| --- | --- | --- | --- | --- | --- |
| STRATEGY_REVIEW_THREAD | `019effea-8045-79f1-98f5-7b633072354c` | local checkout, read-only | repo docs/templates/gates plus public-methodology notes | none | received |
| ENGINEERING_ARCHITECT_THREAD | `019effea-b085-7730-8a9a-825cc1250a84` | local checkout, read-only | tools/templates/tests/docs boundaries | none | received |
| ADVERSARIAL_QA_THREAD | `019effea-e08c-75a2-ac47-626810c638e9` | local checkout, read-only | proposal plan, thread constraints, validation scope | none | received |

Council adoption:

- Accepted: build a traceable internal creative proposal engine, not a subjective taste oracle.
- Accepted: add a real `creative-quality-gate` with PASS / PARTIAL_PASS / BLOCKED and reason codes.
- Accepted: sparse evidence must remain TBD/open question and downgrade gate status instead of fabricating claims.
- Accepted: keep adco as project control plus strategy/proposal draft owner; route video/storyboard to `dircreative`, image/KV to `imagegen` or Creative Production, and fixed document templates to Template Creator.
- Rejected: score-only or file-exists-only gate.
- Rejected: claiming `VALIDATION=PASS` proves creative, aesthetic, or client-ready quality.

Council cleanup: all three read-only council threads were archived after CONTROL consumed receipts.

## Implementation / Docs Dispatch

| thread_class | actual_thread_id | environment | read_scope | write_scope | receipt |
| --- | --- | --- | --- | --- | --- |
| IMPLEMENTATION_WORKER | `019effec-67dd-7871-ad97-9506e4f18017` | isolated worktree `/Users/jinjungao/.codex/worktrees/1d4a/ad-creative-orchestrator` | existing source/templates/tests plus docs read-only | `tools/ad_creative_operator.py`, `tools/test_gates.py`, `tools/run_checks.py`, proposal templates and packaged mirrors, skill drafts | received |
| DOCS_WORKER | `019effec-ad25-7bc0-8c80-cd1d1f1615b3` | isolated worktree `/Users/jinjungao/.codex/worktrees/5bda/ad-creative-orchestrator` | docs plus implementation names read-only | `README.md`, `docs/operating/**` scoped docs | received |

Both workers reported `actual_thread_id_unknown_in_worker`; CONTROL recorded actual worker ids with Codex thread tools.

## Adoption Decisions

Accepted from `IMPLEMENTATION_WORKER`:

- Add `adco creative-proposal <project> [--work-id <id>] [--json]`.
- Add `adco creative-quality-gate <project>`.
- Write traceable internal proposal artifacts to:
  - `AD-creative/creative/creative_directions.md`
  - `AD-creative/creative/option_matrix.csv`
  - `AD-creative/proposal_architecture/proposal_structure.md`
  - `AD-creative/client_review/slide_spec.md`
- Register proposal artifacts and gate reports through existing artifact/gate helpers.
- Block or downgrade generic, unsupported, thin, missing-evidence, missing-benefit, missing-key-visual/action, missing-choice-rationale, and internal-language leakage cases.
- Add regression coverage for proposal fields, generic proposal blocking, complete fixture pass, unsupported case claim blocking, and `VALIDATION=PASS` not implying creative quality pass.
- Add `run_checks.py` smoke coverage for `creative-proposal --json` and `creative-quality-gate`.
- Sync project templates, packaged mirrors, and skill drafts.

Accepted from `DOCS_WORKER`:

- Add `docs/operating/creative_proposal_quality_standard.md`.
- Document public methodology as local reusable checks, not copied campaign wording.
- Document implemented `adco creative-proposal` and `adco creative-quality-gate` commands.
- Preserve boundaries: internal draft only, `VALIDATION=PASS` structural only, human review still required for creative taste, search/imagegen aesthetics, and final send.
- Document module routing across adco, `dircreative`, image/imagegen/Creative Production, and Template Creator.

Deferred:

- Installed global skill update is out of scope for this goal because it modifies global skill installation; only repo and packaged skill drafts were updated.

## Worker Verification Evidence

`IMPLEMENTATION_WORKER` reported:

- `python3 -m py_compile ...`: PASS
- `python3 tools/check_packaged_assets.py`: PASS
- mirror `cmp` checks: PASS
- `python3 tools/test_gates.py`: PASS
- `python3 tools/test_goal_workflow.py`: PASS
- CLI smoke `sample -> creative-proposal --json -> creative-quality-gate`: PASS, sample gate returned `PARTIAL_PASS` because evidence gaps remain open
- `python3 tools/run_checks.py`: PASS
- `git diff --check` on touched files: PASS

`DOCS_WORKER` reported:

- stale "not a CLI / no same-name CLI" caveats removed: PASS
- docs command forms aligned with implementation: PASS
- `git diff --check -- README.md docs/operating/creative_proposal_quality_standard.md docs/operating/non_developer_quickstart.md docs/operating/first_real_project_runbook.md docs/operating/operating_manual.md`: PASS

## CONTROL Merge Status

CONTROL merged accepted implementation and docs diffs into the main checkout after receipt review.

## Final QA / Fix Adoption

`QA_REVIEW_WORKER` `019efff8-7889-7363-98d6-b731a149e593` returned `ACCEPT_WITH_NOTES`.

Accepted QA findings:

- P2: project AGENTS templates omitted `adco creative-quality-gate <project>` from the handoff gate list. Adopted.
- P3: this addendum still marked final QA pending. Adopted and resolved by this section.

Corrective dispatch:

| thread_class | actual_thread_id | environment | read_scope | write_scope | receipt |
| --- | --- | --- | --- | --- | --- |
| IMPLEMENTATION_FIX_WORKER | `019efffa-a127-75a0-b9d5-0dfa7671803f` | isolated worktree `/Users/jinjungao/.codex/worktrees/10bd/ad-creative-orchestrator` | AGENTS templates, validator, AGENTS policy tests, example AGENTS after stricter validation failed | AGENTS templates, `tools/validate_project.py`, `tools/test_goal_workflow.py`, example AGENTS only | received |

Accepted from `IMPLEMENTATION_FIX_WORKER`:

- Add `adco creative-quality-gate <project>` to source and packaged AGENTS templates.
- Add `creative-quality-gate` to required AGENTS policy snippets.
- Add test coverage so the required command is asserted.
- After CONTROL validation found example AGENTS drift, add the same gate command to both example AGENTS files.

## Final CONTROL Validation

CONTROL validation after final QA fixes:

- `python3 tools/validate_project.py templates/project`: PASS
- `python3 tools/validate_project.py tools/adco_resources/templates/project`: PASS
- `python3 tools/test_goal_workflow.py`: PASS
- `python3 tools/check_packaged_assets.py`: PASS
- `python3 tools/validate_project.py examples/moncler_protocol_dry_run`: PASS
- `python3 tools/validate_project.py examples/simulated_qingling_outdoor_launch`: PASS
- `python3 tools/run_checks.py`: failed once after stricter validator because example AGENTS files lacked the new `creative-quality-gate` snippet; corrective worker fixed both examples; rerun PASS
- `make release-check`: PASS; optional dependency warnings for `PIL` and `pptx` were reported inside the isolated release-check venv only
- `git diff --check`: PASS

Final cleanup:

- Archived `STRATEGY_REVIEW_THREAD` `019effea-8045-79f1-98f5-7b633072354c`.
- Archived `ENGINEERING_ARCHITECT_THREAD` `019effea-b085-7730-8a9a-825cc1250a84`.
- Archived `ADVERSARIAL_QA_THREAD` `019effea-e08c-75a2-ac47-626810c638e9`.
- Archived `IMPLEMENTATION_WORKER` `019effec-67dd-7871-ad97-9506e4f18017`.
- Archived `DOCS_WORKER` `019effec-ad25-7bc0-8c80-cd1d1f1615b3`.
- Archived `QA_REVIEW_WORKER` `019efff8-7889-7363-98d6-b731a149e593`.
- Archived `IMPLEMENTATION_FIX_WORKER` `019efffa-a127-75a0-b9d5-0dfa7671803f`.

Final QA status: `ACCEPT_WITH_NOTES`; P2 fixed, P3 fixed by this adoption record. No P0/P1 blockers remain.
