# Goal Iteration Plan

goal_id:
goal_title:
status:
owner:
created_at:
updated_at:
loop_mode: sequential
helper_mode: none

## Objective

## Scope

## Loop Mode Contract

```text
loop_mode: sequential
allowed_loop_modes: sequential,rfc_dag,continuous_pr,infinite
sequential: default; finish one bounded lane step before the next handoff
rfc_dag: use only when an RFC-style dependency graph is written in the lane plan
continuous_pr: use only for controlled PR/check cycles with explicit validation commands
infinite: bounded internal exploration only; must declare iteration_budget, freeze_trigger, replay_trigger, and stop_condition
safe_stop: stop before client-visible send, paid/private/upload actions, destructive edits, global install, validation failure, or missing receipt proof
replay_trigger: validation_result FAIL, missing receipt schema, stale evidence, out-of-scope edit, or reopened feedback
freeze_trigger: thread confusion, wrong thread, heat/cost spike, budget exceeded, repeated same root cause, or cleanup request
stop_condition: receipt reconciled, eval_gate passed or blocker recorded, adoption_decision recorded, and cleanup action planned
```

## Non Scope

## Stateless Secondary Helper Contract

```text
helper_mode: none by default
optional_helper_mode: stateless_secondary_helper
allowed_helper_kinds: image_generation,ocr,layout_lint,asset_resize,reference_extraction
helper_policy: only a real Codex Thread worker may invoke a stateless helper for bounded local subtasks
helper_write_boundary: helper is not a Codex Thread, has no thread_id, no thread_registry row, no write_scope, and no adoption authority
helper_evidence_required: helper_invocations, helper_input_refs, helper_output_refs, helper_artifacts, helper_validation_result, helper_adopted_by_worker, helper_failure_reason, worker_synthesis
worker_synthesis: worker adopts/rejects helper output before main/control adopts through the worker receipt
```

## Source Of Truth

- current_truth:
- requirements:
- gaps:
- work_items:
- gate_log:
- handoff_board:
- pending_decisions:

## Execution Batches

| batch_id | objective | owner | inputs | outputs | gate | status | exit_condition |
|---|---|---|---|---|---|---|---|
| B1 |  |  |  |  |  |  |  |

## Text-First Delivery Mapping

| phase | primary_work | optional_specialist_or_asset_lane | dependency | exit_condition | next_phase |
|---|---|---|---|---|---|
| P0 | truth / gaps / FinalDelivery lock | asset inventory | source events | structure verified without mutating final files | P1 |
| P1 | client-readable page outline | research / material gaps | P0 truth | outline complete and client-safe | P2 |
| P2 | hash-bound human/client outline confirmation | none | P1 outline | confirmation receipt valid | P3 |
| P3 | creative / references / proposal | neutral specialist exchange / internal-only assets | P2 confirmation | quality gates have evidence | P4 |
| P4 | immutable versioned PPT export | exact-current asset binding | P2-P3 | version chain and editability proof valid | P5 |
| P5 | language / visual / authorization / PPT gates | independent review | P4 package | corresponding gates have fresh evidence | P6 |
| P6 | fresh client-pack manifest and binding | none | P5 | package digest current and Client Pack PASS | P7 |
| P7 | independent human review and send authorization | none | P6 | send-readiness PASS; no send performed | P8 |
| P8 | feedback merge and next-version plan | revalidate adopted specialist/asset outputs | feedback | supersede chain recorded | next goal |

## Adversarial Council

| stage | objection | rebuttal_path | revision_decision | gate_status |
|---|---|---|---|---|
|  |  |  |  |  |

## Pause / Continue / Rollback Rules

continue_when:
pause_when:
rollback_path:
resume_when:
safe_stop:
replay_trigger:
freeze_trigger:

## Verification

| check | method | threshold | result | evidence |
|---|---|---|---|---|
|  |  |  |  |  |

## Execution Log

| time | action | artifact | result | next |
|---|---|---|---|---|
|  |  |  |  |  |

## Next Iteration Queue

| priority | task | owner | trigger | exit_condition |
|---|---|---|---|---|
|  |  |  |  |  |
