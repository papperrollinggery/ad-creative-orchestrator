#!/usr/bin/env python3
"""Regression checks for goal-plan and adversarial Gate policy."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from ad_creative_operator import (
    add_reference,
    analyze_profiles,
    command_thread_plan,
    creative_doctor_report,
    ensure_project,
    ensure_profile_work,
    import_creative_production_run,
    register_materials,
    render_goal_iteration_plan,
    render_thread_execution_plan,
    review_film_quality,
    review_reference_pack,
    run_goal,
    workspace_hygiene_report,
)
from init_project import AGENTS_MERGE_SUGGESTION_REL, agents_policy_status
from run_checks import cleanup_python_caches
from validate_project import validate


OPTIONAL_SKIPS: list[str] = []


def optional_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception as exc:  # noqa: BLE001 - tests report optional fixture coverage
        OPTIONAL_SKIPS.append(f"{name}: {exc}")
        return False


def assert_valid(project: Path) -> None:
    errors, _ = validate(project)
    if errors:
        raise AssertionError("\n".join(errors))


def add_clean_reference(project: Path) -> None:
    add_reference(
        project,
        "https://example.com",
        "Example",
        "direction_reference",
        "official_or_public_reference",
        why_relevant="Evidence source for regression testing.",
        borrow="Structure only.",
        do_not_copy="Do not copy visible identity.",
        live_check=False,
    )


def mark_first_execution_receipt_received(project: Path) -> Path:
    registry_path = project / "AD-creative/orchestrator/thread_registry.csv"
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for row in rows:
        if row.get("mode") == "execution_worker":
            row["receipt_status"] = "received"
            row["reconciliation_status"] = "reconciled"
            row["lifecycle_state"] = "returned"
            row["returned_at"] = "2026-06-27T00:00:00Z"
            row["reconciled_at"] = "2026-06-27T00:01:00Z"
            receipt_path = project / row["receipt_path"]
            break
    else:
        raise AssertionError("expected execution_worker row")

    with registry_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return receipt_path


def test_project_agents_policy_created_and_validated() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-agents-policy-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        agents = project / "AGENTS.md"
        assert agents.exists()
        text = agents.read_text(encoding="utf-8")
        assert "ad-creative-orchestrator" in text
        assert "VALIDATION=PASS" in text
        assert "creative-quality-gate" in text
        assert "client-pack-gate" in text
        assert_valid(project)


def test_validate_rejects_missing_project_agents_policy() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-agents-missing-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        (project / "AGENTS.md").unlink()
        errors, _ = validate(project)
        assert any("missing required file: AGENTS.md" in error for error in errors), errors


def test_existing_agents_policy_is_not_overwritten() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-agents-existing-") as raw_project:
        project = Path(raw_project)
        custom_agents = project / "AGENTS.md"
        custom_agents.write_text("# Custom Project Rules\n", encoding="utf-8")
        ensure_project(project)
        assert custom_agents.read_text(encoding="utf-8") == "# Custom Project Rules\n"
        suggestion = project / "AD-creative/orchestrator/AGENTS.merge_suggestion.md"
        assert suggestion.exists()
        errors, _ = validate(project)
        assert any("AGENTS.md missing required policy" in error for error in errors), errors


def test_agents_policy_status_clears_after_manual_merge() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-agents-merged-") as raw_project:
        project = Path(raw_project)
        custom_agents = project / "AGENTS.md"
        custom_agents.write_text("# Custom Project Rules\n", encoding="utf-8")
        ensure_project(project)
        assert agents_policy_status(project).startswith("MERGE_REQUIRED:"), agents_policy_status(project)
        custom_agents.write_text((project / AGENTS_MERGE_SUGGESTION_REL).read_text(encoding="utf-8"), encoding="utf-8")
        assert agents_policy_status(project) == "PRESENT"
        assert_valid(project)


def test_gate_downgrades_without_adversarial_record() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-no-adv-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_clean_reference(project)
        status, findings, _ = review_reference_pack(project)
        assert status == "PARTIAL_PASS", status
        assert any("反驳性议会" in item for item in findings), findings
        assert_valid(project)


def test_goal_plan_allows_clean_gate_pass() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-with-adv-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_goal_iteration_plan(
            project,
            goal_id="GOAL-REGRESSION-001",
            title="Goal regression",
            objective="Verify adversarial council record allows clean Gate PASS.",
            owner="Regression",
        )
        add_clean_reference(project)
        status, findings, _ = review_reference_pack(project)
        assert status == "PASS", (status, findings)
        assert not findings, findings
        assert_valid(project)


def test_goal_run_stops_without_material() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-run-empty-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        result = run_goal(project, goal_id="latest", max_steps=1, allow_generate=False)
        assert result["stop_reason"] == "NEEDS_MATERIAL", result
        assert (project / "AD-creative/handoff/操作台.html").exists()
        assert_valid(project)


def test_thread_plan_creates_control_plane() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-plan-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        payload = render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-001",
            title="ThreadOps regression",
            objective="Create a controlled Codex Thread execution layer.",
            roles=["brand_client", "copy_creative", "qa_review"],
            brand="Regression Brand",
            product="Regression Product",
            deliverable="thread plan",
        )
        assert Path(payload["thread_lane_plan"]).exists()
        assert Path(payload["prompt_dir"]).exists()
        assert len(payload["prompts"]) == 3
        assert len(payload["role_briefs"]) == 3
        assert all(Path(path).exists() for path in payload["prompts"])
        assert all(Path(path).exists() for path in payload["role_briefs"])
        registry = (project / "AD-creative/orchestrator/thread_registry.csv").read_text(encoding="utf-8")
        assert "planned:LANE-01-BRAND_CLIENT" in registry
        assert "mode" in registry
        assert "write_scope" in registry
        assert "receipt_status" in registry
        assert "reconciliation_status" in registry
        assert "COPY_CREATIVE" in registry
        assert "execution_worker" in registry
        assert "isolated_workspace" in registry
        assert (
            "AD-creative/workspaces/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE/copy_drafts.md"
            in registry
        )
        assert "AD-creative/agents/receipts/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE_receipt.md" in registry
        assert "{work_id}" not in registry
        assert "{lane_id}" not in registry
        assert "<work_id>" not in registry
        assert "<lane_id>" not in registry
        plan_text = Path(payload["thread_lane_plan"]).read_text(encoding="utf-8")
        assert "max_active_worker_reviewer: 3" in plan_text
        assert "lane_modes: execution_worker requires exact write_scope" in plan_text
        assert "COPY_CREATIVE" in plan_text
        assert "execution_worker | isolated_workspace" in plan_text
        assert (
            "AD-creative/workspaces/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE/copy_drafts.md"
            in plan_text
        )
        assert "AD-creative/agents/receipts/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE_receipt.md" in plan_text
        assert "{work_id}" not in plan_text
        assert "{lane_id}" not in plan_text
        assert "<work_id>" not in plan_text
        assert "<lane_id>" not in plan_text
        assert "Uses read_only by default" not in plan_text
        assert "read_only by default" not in plan_text
        assert (
            "Uses execution_worker for scoped production/editing work; uses read_only only for explorer, reviewer, research, or cold-review lanes."
            in plan_text
        )
        assert (
            "Execution worker lanes must declare exact write_scope, files_changed, validation_result, dirty_state_impact, and cleanup_actions in the receipt."
            in plan_text
        )
        assert "receipt_status" in plan_text
        assert "Final export allowed" not in plan_text
        prompt_text = (project / "AD-creative/agents/thread_prompts/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE_prompt.md").read_text(encoding="utf-8")
        receipt_text = (project / "AD-creative/agents/receipts/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE_receipt.md").read_text(encoding="utf-8")
        role_brief_text = (project / "AD-creative/agents/role_briefs/COPY_CREATIVE_WORK-GOAL-THREAD-001-THREADS.md").read_text(encoding="utf-8")
        for generated_text in (prompt_text, receipt_text, role_brief_text):
            assert (
                "AD-creative/workspaces/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE/copy_drafts.md"
                in generated_text
            )
            assert "{work_id}" not in generated_text
            assert "{lane_id}" not in generated_text
            assert "<work_id>" not in generated_text
            assert "<lane_id>" not in generated_text
        assert_valid(project)


def test_thread_plan_includes_harness_loop_and_adoption_contracts() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-harness-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        payload = render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-HARNESS",
            title="ThreadOps harness",
            objective="Require typed harness, loop, and adoption contracts.",
            roles=["copy_creative", "qa_review"],
        )
        plan_text = Path(payload["thread_lane_plan"]).read_text(encoding="utf-8")
        prompt_text = (
            project
            / "AD-creative/agents/thread_prompts/WORK-GOAL-THREAD-HARNESS-THREADS/LANE-01-COPY_CREATIVE_prompt.md"
        ).read_text(encoding="utf-8")
        receipt_text = (
            project
            / "AD-creative/agents/receipts/WORK-GOAL-THREAD-HARNESS-THREADS/LANE-01-COPY_CREATIVE_receipt.md"
        ).read_text(encoding="utf-8")
        role_brief_text = (
            project
            / "AD-creative/agents/role_briefs/COPY_CREATIVE_WORK-GOAL-THREAD-HARNESS-THREADS.md"
        ).read_text(encoding="utf-8")
        generated = "\n".join([plan_text, prompt_text, receipt_text, role_brief_text])
        for key in [
            "action_space",
            "observation_contract",
            "error_recovery_contract",
            "context_budget",
            "iteration_budget",
            "eval_gate",
            "adoption_decision",
            "rejection_reason",
            "loop_state",
            "replay_trigger",
            "freeze_trigger",
            "stop_condition",
            "helper_mode",
            "helper_policy",
            "allowed_helper_kinds",
            "helper_write_boundary",
            "helper_evidence_required",
            "helper_failure_policy",
            "helper_invocations",
            "helper_input_refs",
            "helper_output_refs",
            "helper_artifacts",
            "helper_validation_result",
            "helper_adopted_by_worker",
            "helper_failure_reason",
            "worker_synthesis",
        ]:
            assert key in generated
        for loop_mode in ["sequential", "rfc_dag", "continuous_pr", "infinite"]:
            assert loop_mode in generated
        for helper_kind in ["image_generation", "ocr", "layout_lint", "asset_resize", "reference_extraction"]:
            assert helper_kind in generated
        assert "Lane Harness Matrix" in plan_text
        assert "Lane Helper Matrix" in plan_text
        assert "Codex Threads are not subagents" in prompt_text
        assert "A helper invocation may be backed by a stateless helper/subagent-style call" in prompt_text
        assert "has no thread_id" in generated
        assert "TOOL_BLOCKED" in prompt_text
        assert "prompt_only_output: invalid" in receipt_text
        assert "helper_mode: none" in receipt_text
        assert "Production worker receipts cannot be prompt-only" in plan_text
        assert_valid(project)


def test_execution_worker_receipt_cannot_be_prompt_only() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-receipt-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        payload = render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-RECEIPT",
            title="ThreadOps receipt",
            objective="Production receipts prove files and validation.",
            roles=["copy_creative"],
        )
        receipt_text = Path(payload["receipts"][0]).read_text(encoding="utf-8")
        assert "mode: execution_worker" in receipt_text
        assert "files_changed: required_non_empty_for_adopt" in receipt_text
        assert "prompt-only output is invalid for production workers" in receipt_text
        assert "## Validation Result" in receipt_text
        assert "## Dirty-State Impact" in receipt_text
        assert "## Manifest / Index Updates" in receipt_text
        assert "## QA / Gate Status" in receipt_text
        assert "## Adoption / Rejection Recommendation" in receipt_text
        assert "## Cleanup Actions" in receipt_text
        assert_valid(project)


def test_threadops_validation_allows_pending_execution_worker_receipt_template() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-pending-receipt-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        payload = render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-PENDING-RECEIPT",
            title="ThreadOps pending receipt",
            objective="Pending receipt placeholders must not block generated plans.",
            roles=["copy_creative"],
        )
        receipt_text = Path(payload["receipts"][0]).read_text(encoding="utf-8")
        registry_text = (project / "AD-creative/orchestrator/thread_registry.csv").read_text(encoding="utf-8")
        assert "status: pending" in receipt_text
        assert "receipt_status" in registry_text
        assert "missing" in registry_text
        assert_valid(project)


def test_threadops_validation_rejects_prompt_only_received_execution_receipt() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-prompt-receipt-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-PROMPT-RECEIPT",
            title="ThreadOps prompt-only receipt",
            objective="Received production receipts must prove execution.",
            roles=["copy_creative"],
        )
        receipt_path = mark_first_execution_receipt_received(project)
        receipt_path.write_text(
            """# LANE-01-COPY_CREATIVE Receipt

status: received

## Summary

Completed the prompt and recommend adoption.
""",
            encoding="utf-8",
        )
        errors, _ = validate(project)
        assert any(
            "received execution worker receipt lacks concrete proof fields" in error
            and "files_changed" in error
            and "evidence_refs" in error
            for error in errors
        ), errors


def test_threadops_validation_rejects_missing_helper_evidence() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-helper-missing-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-HELPER-MISSING",
            title="ThreadOps helper evidence",
            objective="Enabled helper mode must prove helper output and worker synthesis.",
            roles=["copy_creative"],
        )
        receipt_path = mark_first_execution_receipt_received(project)
        receipt_path.write_text(
            """# LANE-01-COPY_CREATIVE Receipt

status: received
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-MISSING-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
adoption_decision: ADOPT
loop_state: reconciled
cleanup_actions: archived worker thread after receipt reconciliation
evidence_refs: thread_registry.csv row LANE-01-COPY_CREATIVE; receipt path; validation command above
helper_mode: stateless_secondary_helper

## Summary

Worker claims a helper was used but did not record helper evidence.
""",
            encoding="utf-8",
        )
        errors, _ = validate(project)
        assert any(
            "received execution worker receipt lacks concrete helper evidence fields" in error
            and "helper_invocations" in error
            and "helper_input_refs" in error
            and "helper_output_refs" in error
            and "helper_artifacts" in error
            and "worker_synthesis" in error
            for error in errors
        ), errors
        assert any(
            "received execution worker receipt lacks recorded helper receipt fields" in error
            and "helper_failure_reason" in error
            for error in errors
        ), errors


def test_threadops_validation_rejects_helper_thread_id_claim() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-helper-thread-id-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-HELPER-THREAD-ID",
            title="ThreadOps helper thread boundary",
            objective="Stateless helpers must not claim Codex Thread identity.",
            roles=["copy_creative"],
        )
        receipt_path = mark_first_execution_receipt_received(project)
        receipt_path.write_text(
            """# LANE-01-COPY_CREATIVE Receipt

status: received
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-THREAD-ID-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
adoption_decision: ADOPT
loop_state: reconciled
cleanup_actions: archived worker thread after receipt reconciliation
evidence_refs: thread_registry.csv row LANE-01-COPY_CREATIVE; receipt path; validation command above
helper_mode: stateless_secondary_helper
helper_invocations: image_generation helper_thread_id: 019fake-helper-thread
helper_output_refs: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-THREAD-ID-THREADS/LANE-01-COPY_CREATIVE/helper_outputs/image_generation_result.json
helper_validation_result: PASS - worker checked dimensions and internal-only visibility
helper_adopted_by_worker: yes, adopted as internal draft reference only
worker_synthesis: Worker used the helper output as bounded reference evidence and retained adoption authority.
""",
            encoding="utf-8",
        )
        errors, _ = validate(project)
        assert any(
            "helper invocation claims thread_id" in error
            for error in errors
        ), errors


def test_threadops_validation_rejects_observation_only_evidence_refs() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-observation-evidence-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-OBSERVATION-EVIDENCE",
            title="ThreadOps observation evidence",
            objective="Observation text must not prove receipt evidence refs.",
            roles=["copy_creative"],
        )
        receipt_path = mark_first_execution_receipt_received(project)
        receipt_path.write_text(
            """# LANE-01-COPY_CREATIVE Receipt

status: received
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-OBSERVATION-EVIDENCE-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
adoption_decision: ADOPT
loop_state: reconciled
cleanup_actions: archived worker thread after receipt reconciliation
evidence_refs: pending

## Observation

Reviewed validator behavior and found this receipt has a non-empty observation section.
""",
            encoding="utf-8",
        )
        errors, _ = validate(project)
        assert any(
            "received execution worker receipt lacks concrete proof fields" in error
            and "evidence_refs" in error
            for error in errors
        ), errors


def test_threadops_validation_rejects_adopt_without_file_output() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-adopt-no-files-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-ADOPT-NO-FILES",
            title="ThreadOps adopt no files",
            objective="Adopted production receipts must name file output.",
            roles=["copy_creative"],
        )
        receipt_path = mark_first_execution_receipt_received(project)
        receipt_path.write_text(
            """# LANE-01-COPY_CREATIVE Receipt

status: received
files_changed: no files changed
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: no tracked or untracked files changed
adoption_decision: ADOPT
loop_state: reconciled
cleanup_actions: archived worker thread after receipt reconciliation
evidence_refs: thread_registry.csv row LANE-01-COPY_CREATIVE; receipt path; validation command above

## Summary

The worker recommends adoption but did not produce file output.
""",
            encoding="utf-8",
        )
        errors, _ = validate(project)
        assert any(
            "received execution worker receipt adopts without file output" in error
            for error in errors
        ), errors


def test_threadops_validation_accepts_received_execution_receipt_with_proof() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-proof-receipt-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-PROOF-RECEIPT",
            title="ThreadOps proof receipt",
            objective="Received production receipts include concrete proof.",
            roles=["copy_creative"],
        )
        receipt_path = mark_first_execution_receipt_received(project)
        receipt_path.write_text(
            """# LANE-01-COPY_CREATIVE Receipt

status: received
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-PROOF-RECEIPT-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
adoption_decision: ADOPT
loop_state: reconciled
cleanup_actions: archived worker thread after receipt reconciliation
evidence_refs: thread_registry.csv row LANE-01-COPY_CREATIVE; receipt path; validation command above

## Summary

Production worker returned file-level proof and validation evidence.
""",
            encoding="utf-8",
        )
        assert_valid(project)


def test_threadops_validation_accepts_received_execution_receipt_with_helper_proof() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-helper-proof-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-HELPER-PROOF",
            title="ThreadOps helper proof",
            objective="Received helper-enabled receipts include concrete helper evidence.",
            roles=["copy_creative"],
        )
        receipt_path = mark_first_execution_receipt_received(project)
        receipt_path.write_text(
            """# LANE-01-COPY_CREATIVE Receipt

status: received
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-PROOF-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
adoption_decision: ADOPT
loop_state: reconciled
cleanup_actions: archived worker thread after receipt reconciliation
evidence_refs: thread_registry.csv row LANE-01-COPY_CREATIVE; receipt path; validation command above
helper_mode: stateless_secondary_helper
helper_invocations: image_generation helper IMG-HELPER-001 for a bounded local reference draft
helper_input_refs: AD-creative/image_jobs/image_prompt_pack.json item PROMPT-001
helper_output_refs: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-PROOF-THREADS/LANE-01-COPY_CREATIVE/helper_outputs/image_generation_result.json
helper_artifacts: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-PROOF-THREADS/LANE-01-COPY_CREATIVE/helper_outputs/reference_preview.png
helper_validation_result: PASS - worker checked dimensions, prompt trace, and internal-only visibility
helper_adopted_by_worker: yes, adopted as internal draft reference only
helper_failure_reason: none
worker_synthesis: Worker used the image_generation helper output as bounded reference evidence, then wrote copy_drafts.md and recommended ADOPT through this receipt.

## Summary

Production worker returned file-level proof, helper evidence, and validation evidence.
""",
            encoding="utf-8",
        )
        assert_valid(project)


def test_threadops_validation_rejects_invalid_execution_worker_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-contract-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-CONTRACT",
            title="ThreadOps contract",
            objective="Validate execution worker contracts.",
            roles=["qa_review"],
        )
        registry_path = project / "AD-creative/orchestrator/thread_registry.csv"
        registry = registry_path.read_text(encoding="utf-8")
        registry = registry.replace("cold_review,read_only,not_applicable_for_read_only,receipt only", "execution_worker,read_only,not_applicable_for_read_only,receipt only")
        registry_path.write_text(registry, encoding="utf-8")
        plan_path = project / "AD-creative/orchestrator/thread_lane_plan.md"
        plan = plan_path.read_text(encoding="utf-8")
        plan = plan.replace("cold_review | read_only | not_applicable_for_read_only |", "execution_worker | read_only | not_applicable_for_read_only |")
        plan_path.write_text(plan, encoding="utf-8")
        errors, _ = validate(project)
        assert any("thread_registry" in error and "missing exact write_scope" in error for error in errors), errors
        assert any("thread_lane_plan" in error and "uses read_only environment" in error for error in errors), errors


def test_thread_plan_production_roles_use_isolated_workspaces() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-production-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        payload = render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-PRODUCTION",
            title="ThreadOps production roles",
            objective="Production lanes draft only in isolated workspaces.",
            roles=["film_director", "art_design", "producer_risk"],
        )
        plan_text = Path(payload["thread_lane_plan"]).read_text(encoding="utf-8")
        registry = (project / "AD-creative/orchestrator/thread_registry.csv").read_text(encoding="utf-8")
        combined = plan_text + "\n" + registry
        assert "FILM_DIRECTOR" in combined
        assert "ART_DESIGN" in combined
        assert "PRODUCER_RISK" in combined
        assert "LANE-01-FILM_DIRECTOR |" in plan_text
        assert "LANE-02-ART_DESIGN |" in plan_text
        assert "execution_worker | isolated_workspace" in plan_text
        assert (
            "AD-creative/workspaces/WORK-GOAL-THREAD-PRODUCTION-THREADS/LANE-01-FILM_DIRECTOR/film_notes.md"
            in combined
        )
        assert (
            "AD-creative/workspaces/WORK-GOAL-THREAD-PRODUCTION-THREADS/LANE-02-ART_DESIGN/art_direction_notes.md"
            in combined
        )
        producer_lane = next(
            line
            for line in plan_text.splitlines()
            if line.startswith("| LANE-03-PRODUCER_RISK |") and "read_only_review" in line
        )
        assert "PRODUCER_RISK" in producer_lane
        assert "| read_only_review | read_only | not_applicable_for_read_only |" in producer_lane
        assert "| receipt only |" in producer_lane
        assert "{work_id}" not in combined
        assert "{lane_id}" not in combined
        assert "<work_id>" not in combined
        assert "<lane_id>" not in combined
        assert_valid(project)


def test_thread_plan_rejects_over_budget_before_init() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-plan-budget-") as raw_root:
        project = Path(raw_root) / "new-project"
        for max_active in (0, 4):
            try:
                render_thread_execution_plan(
                    project,
                    goal_id="GOAL-THREAD-BUDGET",
                    title="ThreadOps over budget",
                    objective="Reject invalid active worker budget.",
                    roles=["brand_client"],
                    max_active=max_active,
                )
            except ValueError as exc:
                assert "max_active_worker_reviewer" in str(exc)
            else:
                raise AssertionError("expected max_active budget rejection")
            assert not project.exists()


def test_thread_plan_rejects_empty_roles_before_init() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-plan-empty-") as raw_root:
        project = Path(raw_root) / "new-project"
        try:
            render_thread_execution_plan(
                project,
                goal_id="GOAL-THREAD-EMPTY",
                title="ThreadOps empty roles",
                objective="Reject empty ThreadOps role set.",
                roles=[],
            )
        except ValueError as exc:
            assert "at least one ThreadOps role" in str(exc)
        else:
            raise AssertionError("expected empty roles rejection")
        assert not project.exists()


def test_thread_plan_rejects_existing_plan_before_schema_upgrade() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-plan-existing-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        plan_path = project / "AD-creative/orchestrator/thread_lane_plan.md"
        plan_path.write_text("# Existing plan\n", encoding="utf-8")
        registry_path = project / "AD-creative/orchestrator/thread_registry.csv"
        old_header = "thread_id,title,role,lane_id,work_id,lifecycle_state,pinned,archived,created_at,updated_at,cleanup_action,notes\n"
        registry_path.write_text(old_header, encoding="utf-8")
        try:
            render_thread_execution_plan(
                project,
                goal_id="GOAL-THREAD-EXISTING",
                title="ThreadOps existing plan",
                objective="Reject without mutating registry schema.",
                roles=["brand_client"],
            )
        except FileExistsError:
            pass
        else:
            raise AssertionError("expected existing thread_lane_plan rejection")
        assert registry_path.read_text(encoding="utf-8") == old_header
        errors, _ = validate(project)
        assert any("thread_registry missing ThreadOps columns" in error for error in errors)


def test_thread_plan_invalid_role_returns_check() -> None:
    import argparse

    with tempfile.TemporaryDirectory(prefix="adco-thread-plan-role-") as raw_root:
        project = Path(raw_root) / "new-project"
        args = argparse.Namespace(
            project=str(project),
            goal_id="GOAL-THREAD-BAD-ROLE",
            work_id="",
            task_signature_id="",
            title="Bad role",
            objective="Reject invalid role.",
            roles="not_a_role",
            brand="",
            product="",
            talent_or_ip="",
            platform_or_channel="",
            deliverable="",
            stage="threadops",
            primary_risks="",
            evidence_needed="",
            master_thread_id="",
            current_version_id="",
            max_active=3,
            read_first=[],
            force=False,
            json=False,
        )
        assert command_thread_plan(args) == 1
        assert not project.exists()


def test_profile_analyze_creates_knowledge_base() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-profile-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        material = project / "00_项目资料_ProjectMaterials/01_客户资料_ClientMaterials/meeting_notes.md"
        material.parent.mkdir(parents=True, exist_ok=True)
        material.write_text(
            """# 会议记录

张总: 我们希望这次广告先突出品牌年轻化，但不要像普通快消广告。
李经理: 产品卖点必须清楚，客户内部还没统一到底偏功能还是偏情绪。
王总监: 我担心预算和周期，最终我来确认能不能拍。
品牌调性希望真实、清爽、有专业感。
公司内部需要先统一意见，再给老板看。
""",
            encoding="utf-8",
        )
        source_ids = register_materials(project, [material], "profile regression")
        work_id = ensure_profile_work(project, source_ids, "profile regression")
        stats = analyze_profiles(
            project,
            source_ids=source_ids,
            work_id=work_id,
            brand="NOVA Trail",
            company="NOVA Client",
            client="NOVA Team",
        )
        assert stats["subjects"] >= 4, stats
        assert stats["voices"] == 3, stats
        assert stats["conflicts"] >= 1, stats
        profile_truth = project / "AD-creative/orchestrator/profile_knowledge/profile_current_truth.md"
        handoff = project / "AD-creative/handoff/画像分析简报.md"
        assert "张总" in profile_truth.read_text(encoding="utf-8")
        assert "分歧怎么合" in handoff.read_text(encoding="utf-8")
        assert_valid(project)


def test_workspace_hygiene_detects_cache_pollution() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-hygiene-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        cache_dir = project / "tools/__pycache__"
        cache_dir.mkdir(parents=True)
        (cache_dir / "stale.pyc").write_bytes(b"cache")
        (project / ".mypy_cache").mkdir()
        (project / ".ruff_cache").mkdir()
        (project / ".DS_Store").write_text("local metadata\n", encoding="utf-8")
        report = workspace_hygiene_report(project)
        assert report["status"] == "CHECK", report
        assert any("__pycache__" in path for path in report["pollution_paths"]), report
        assert any(".mypy_cache" in path for path in report["pollution_paths"]), report
        assert any(".ruff_cache" in path for path in report["pollution_paths"]), report
        cleanup_python_caches(project)
        assert workspace_hygiene_report(project)["pollution_paths"] == []


def test_creative_doctor_respects_env_root() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-cp-root-") as raw_root:
        root = Path(raw_root)
        for rel in [
            "skills/ads-explorer/scripts/build_ads_explorer.py",
            "skills/shot-explorer/scripts/create_shot_explorer.py",
            "skills/moodboard-explorer/scripts/create_mood_board.py",
            "scripts/review_renderer.py",
        ]:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# fixture\n", encoding="utf-8")
        old = os.environ.get("ADCO_CREATIVE_PRODUCTION_ROOT")
        os.environ["ADCO_CREATIVE_PRODUCTION_ROOT"] = str(root)
        try:
            status, issues, _, evidence = creative_doctor_report()
        finally:
            if old is None:
                os.environ.pop("ADCO_CREATIVE_PRODUCTION_ROOT", None)
            else:
                os.environ["ADCO_CREATIVE_PRODUCTION_ROOT"] = old
        assert status == "PASS", (status, issues, evidence)


def test_import_creative_production_run_registers_assets() -> None:
    if not optional_module("PIL"):
        return

    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="adco-cp-import-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        run_dir = project / "cp-run"
        run_dir.mkdir()
        image_path = run_dir / "01-hero.png"
        Image.new("RGB", (900, 640), color=(120, 150, 180)).save(image_path)
        (run_dir / "prompts-manifest.json").write_text(
            """[
  {"id":"hero","title":"Hero","output":"01-hero.png","prompt":"single commercial frame"}
]
""",
            encoding="utf-8",
        )
        (run_dir / "jobs.jsonl").write_text(
            '{"id":"hero","output":"01-hero.png","prompt":"single commercial frame"}\n',
            encoding="utf-8",
        )
        (run_dir / "review-board.html").write_text("<!doctype html><title>Review</title>\n", encoding="utf-8")
        asset_ids, metadata_dir = import_creative_production_run(
            project,
            run_dir=run_dir,
            kind="ads",
            slot_prefix="CP",
        )
        assert len(asset_ids) == 1
        assert (metadata_dir / "manifest.json").exists()
        assert_valid(project)


def test_film_quality_gate_writes_report() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-film-gate-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        status, findings, report = review_film_quality(project)
        assert status == "BLOCKED", (status, findings)
        assert report.exists()
        assert_valid(project)


def main() -> int:
    test_project_agents_policy_created_and_validated()
    test_validate_rejects_missing_project_agents_policy()
    test_existing_agents_policy_is_not_overwritten()
    test_agents_policy_status_clears_after_manual_merge()
    test_gate_downgrades_without_adversarial_record()
    test_goal_plan_allows_clean_gate_pass()
    test_goal_run_stops_without_material()
    test_thread_plan_creates_control_plane()
    test_thread_plan_includes_harness_loop_and_adoption_contracts()
    test_execution_worker_receipt_cannot_be_prompt_only()
    test_threadops_validation_allows_pending_execution_worker_receipt_template()
    test_threadops_validation_rejects_prompt_only_received_execution_receipt()
    test_threadops_validation_rejects_missing_helper_evidence()
    test_threadops_validation_rejects_helper_thread_id_claim()
    test_threadops_validation_rejects_observation_only_evidence_refs()
    test_threadops_validation_rejects_adopt_without_file_output()
    test_threadops_validation_accepts_received_execution_receipt_with_proof()
    test_threadops_validation_accepts_received_execution_receipt_with_helper_proof()
    test_threadops_validation_rejects_invalid_execution_worker_contract()
    test_thread_plan_production_roles_use_isolated_workspaces()
    test_thread_plan_rejects_over_budget_before_init()
    test_thread_plan_rejects_empty_roles_before_init()
    test_thread_plan_rejects_existing_plan_before_schema_upgrade()
    test_thread_plan_invalid_role_returns_check()
    test_profile_analyze_creates_knowledge_base()
    test_workspace_hygiene_detects_cache_pollution()
    test_creative_doctor_respects_env_root()
    test_import_creative_production_run_registers_assets()
    test_film_quality_gate_writes_report()
    if OPTIONAL_SKIPS:
        print("TEST_GOAL_WORKFLOW_OPTIONAL_SKIPS=" + "; ".join(OPTIONAL_SKIPS))
    print("TEST_GOAL_WORKFLOW=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
