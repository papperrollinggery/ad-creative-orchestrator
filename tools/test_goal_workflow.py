#!/usr/bin/env python3
"""Regression checks for goal-plan and adversarial Gate policy."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path

from ad_creative_operator import (
    ARTIFACT_INDEX_FIELDS,
    CLIENT_OUTLINE_FIELDS,
    add_reference,
    add_visual_asset,
    analyze_profiles,
    append_csv_row,
    build_parser,
    command_thread_plan,
    cleanup_plan,
    client_outline_confirmed_content_sha256,
    confirm_client_outline,
    creative_doctor_report,
    ensure_project,
    ensure_profile_work,
    export_editable_pptx,
    file_sha256,
    final_delivery_lock,
    import_creative_production_run,
    inspect_pptx,
    migrate_control_plane,
    now_iso,
    perform_intake,
    register_materials,
    render_goal_iteration_plan,
    render_handoff,
    render_human_workspace_indexes,
    render_creative_proposal,
    render_thread_execution_plan,
    record_thread_dispatch,
    record_thread_observation,
    reconcile_thread_receipt,
    declared_thread_changed_paths,
    refresh_asset_current_manifest,
    read_csv_rows,
    review_client_language,
    review_client_outline,
    review_film_quality,
    review_reference_pack,
    review_visual_layout,
    run_goal,
    specialist_manifest_digest,
    specialist_scope_manifest,
    validate_thread_receipt_scope_and_semantics,
    workspace_hygiene_report,
    write_pptx_check,
    write_csv_rows,
    write_json_object,
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


def add_independent_adversarial_review(project: Path, stage: str, target: Path) -> None:
    report = project / f"AD-creative/gates/ADVERSARIAL_REVIEW_{stage.upper()}.md"
    report.write_text(
        f"""# Independent Adversarial Review

stage: {stage}
status: PASS
reviewer_id: regression-cold-reviewer
reviewer_role: independent evidence reviewer
independent: true
reviewed_at: {now_iso()}
target_ref: {target.relative_to(project)}
target_sha256: {file_sha256(target)}

| stage | objection | rebuttal | revision | gate_status |
|---|---|---|---|---|
| {stage} | Source could be too generic. | The reference record is traceable and scoped. | Keep scope-only use and forbid identity copying. | PASS |
""",
        encoding="utf-8",
    )


def mark_first_execution_receipt_received(project: Path) -> Path:
    registry_path = project / "AD-creative/orchestrator/thread_registry.csv"
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for row in rows:
        if row.get("mode") == "execution_worker":
            real_thread_id = "019f1111-2222-7333-8444-555555555555"
            row["receipt_status"] = "received"
            row["reconciliation_status"] = "reconciled"
            row["lifecycle_state"] = "archived"
            row["returned_at"] = "2026-06-27T00:00:00Z"
            row["reconciled_at"] = "2026-06-27T00:01:00Z"
            row["archived"] = "true"
            row["archived_at"] = "2026-06-27T00:02:00Z"
            row["cleanup_action"] = "archived_after_receipt_reconcile"
            row["planned_thread_id"] = row.get("planned_thread_id") or row.get("thread_id", "")
            row["thread_id"] = real_thread_id
            row["real_thread_id"] = real_thread_id
            row["dispatch_status"] = "dispatched"
            row["title_action"] = "dispatcher_set"
            row["title_verified_at"] = "2026-06-27T00:00:30Z"
            row["dispatch_receipt_path"] = "AD-creative/orchestrator/thread_dispatch_TEST.md"
            row["dispatch_evidence"] = "read_thread title matched execution worker lane"
            baseline_path = (
                project
                / "AD-creative/orchestrator/thread_scope_baselines"
                / f"{row['work_id']}_{row['lane_id']}.json"
            )
            baseline_exclusions = [
                "AD-creative/orchestrator/thread_scope_baselines",
                "AD-creative/orchestrator/thread_scope_proofs",
                "AD-creative/orchestrator/thread_registry.csv",
                "AD-creative/orchestrator/agent_runs.csv",
                "AD-creative/orchestrator/thread_dispatch_TEST.md",
                row["receipt_path"],
            ]
            baseline_files = specialist_scope_manifest(
                project, excluded_roots=baseline_exclusions
            )
            write_json_object(
                baseline_path,
                {
                    "protocol_id": "adco.thread-scope-baseline",
                    "version": "1.0",
                    "work_id": row["work_id"],
                    "lane_id": row["lane_id"],
                    "real_thread_id": real_thread_id,
                    "write_scope": row["write_scope"],
                    "excluded_roots": baseline_exclusions,
                    "files": baseline_files,
                    "manifest_sha256": specialist_manifest_digest(baseline_files),
                    "created_at": "2026-06-27T00:00:30Z",
                },
            )
            row["scope_baseline_path"] = str(baseline_path.relative_to(project))
            row["scope_baseline_sha256"] = file_sha256(baseline_path)
            row["absolute_deadline_at"] = "2026-06-27T00:05:00Z"
            row["convergence_state"] = "receipt_received"
            row["bounded_extension_used"] = "false"
            row["rescue_count"] = "0"
            row["receipt_thread_id"] = real_thread_id
            row["adoption_decision"] = "ADOPT"
            row["rejection_reason"] = ""
            receipt_path = project / row["receipt_path"]
            lane_id = row["lane_id"]
            work_id = row["work_id"]
            break
    else:
        raise AssertionError("expected execution_worker row")

    with registry_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    agent_runs_path = project / "AD-creative/orchestrator/agent_runs.csv"
    with agent_runs_path.open(newline="", encoding="utf-8") as handle:
        agent_reader = csv.DictReader(handle)
        agent_fields = list(agent_reader.fieldnames or [])
        agent_rows = list(agent_reader)
    for row in agent_rows:
        if row.get("lane_id") == lane_id and row.get("work_id") == work_id:
            row["thread_id"] = real_thread_id
            row["status"] = "reconciled"
            row["completed_at"] = "2026-06-27T00:01:00Z"
            row["proof_status"] = "receipt_identity_verified"
            row["reconciliation_status"] = "reconciled"
            break
    else:
        raise AssertionError("expected matching agent_runs row")
    with agent_runs_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=agent_fields)
        writer.writeheader()
        writer.writerows(agent_rows)
    (project / "AD-creative/orchestrator/thread_dispatch_TEST.md").write_text(
        "real_thread_id: 019f1111-2222-7333-8444-555555555555\n"
        "title_verified_at: 2026-06-27T00:00:30Z\n",
        encoding="utf-8",
    )
    return receipt_path


def attach_host_scope_proof_fixture(project: Path, receipt_path: Path) -> None:
    registry_path = project / "AD-creative/orchestrator/thread_registry.csv"
    fields, rows = read_csv_rows(registry_path)
    target = next(row for row in rows if row.get("receipt_path") == str(receipt_path.relative_to(project)))
    receipt_text = receipt_path.read_text(encoding="utf-8")
    for rel_path in declared_thread_changed_paths(receipt_text):
        output = project / rel_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("host-observed fixture output", encoding="utf-8")
    proof = validate_thread_receipt_scope_and_semantics(
        project,
        target,
        receipt_text,
        decision="ADOPT",
        cleanup_action=target["cleanup_action"],
        archived_at=target["archived_at"],
    )
    proof_path = (
        project
        / "AD-creative/orchestrator/thread_scope_proofs"
        / f"{target['work_id']}_{target['lane_id']}.json"
    )
    write_json_object(proof_path, proof)
    target["scope_proof_path"] = str(proof_path.relative_to(project))
    target["scope_proof_sha256"] = file_sha256(proof_path)
    write_csv_rows(registry_path, fields, rows)


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


def test_human_workspace_indexes_mirror_control_plane() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-human-index-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        material = project / "incoming_client_brief.md"
        material.write_text("客户希望输出一版客户审阅 PPT。", encoding="utf-8")
        source_ids = register_materials(project, [material], "整理客户资料")
        append_csv_row(
            project / "AD-creative/orchestrator/artifact_index.csv",
            {
                "artifact_id": "ART-TEST-WIP",
                "artifact_type": "proposal_structure",
                "path": "AD-creative/proposal_architecture/proposal_structure.md",
                "stage": "proposal_architecture",
                "version": "v001",
                "status": "draft",
                "visibility": "internal_only",
                "source_event_ids": ";".join(source_ids),
                "linked_requirements": "",
                "linked_work_items": "",
                "linked_references": "",
                "linked_assets": "",
                "gate_status": "PARTIAL_PASS",
                "supersedes_artifact_id": "",
                "created_at": "2026-07-03T00:00:00+08:00",
                "updated_at": "2026-07-03T00:00:00+08:00",
            },
        )
        append_csv_row(
            project / "AD-creative/orchestrator/artifact_index.csv",
            {
                "artifact_id": "ART-TEST-CLIENT",
                "artifact_type": "client_review_deck",
                "path": "AD-creative/ppt/exports/client_review_v001.pptx",
                "stage": "ppt_gate",
                "version": "v001",
                "status": "draft",
                "visibility": "client_visible_pending",
                "source_event_ids": ";".join(source_ids),
                "linked_requirements": "",
                "linked_work_items": "",
                "linked_references": "",
                "linked_assets": "",
                "gate_status": "PARTIAL_PASS",
                "supersedes_artifact_id": "",
                "created_at": "2026-07-03T00:00:00+08:00",
                "updated_at": "2026-07-03T00:00:00+08:00",
            },
        )

        written = render_human_workspace_indexes(project)
        assert len(written) == 6
        source_index_path = project / "00_项目资料_ProjectMaterials/目录索引.md"
        wip_index_path = project / "03_阶段成果_WorkInProgress/目录索引.md"
        client_index_path = project / "04_客户审阅_ClientReview/目录索引.md"
        source_index = source_index_path.read_text(encoding="utf-8")
        wip_index = wip_index_path.read_text(encoding="utf-8")
        client_index = client_index_path.read_text(encoding="utf-8")
        assert "incoming_client_brief.md" in source_index
        assert "ART-TEST-WIP" in wip_index
        assert "proposal_structure.md" in wip_index
        assert "ART-TEST-CLIENT" in client_index
        assert "client_review_v001.pptx" in client_index

        render_handoff(project, "更新人类可读索引", source_ids)
        assert "incoming_client_brief.md" in source_index_path.read_text(encoding="utf-8")


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


def test_intake_preserves_version_truth_and_custom_sections() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-intake-merge-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        truth_path = project / "AD-creative/orchestrator/current_truth.md"
        truth_path.write_text(
            """# Current Truth

## Project
old

## Confirmed
- old

## Current Version Truth

```text
current_version_id: VER-007
current_pptx_artifact_id: ART-PPTX-007
version_map_status: active
```

## Custom Operator Notes
keep-this-note
""",
            encoding="utf-8",
        )
        material = project / "incoming.md"
        material.write_text("客户需要一份可编辑的广告创意提案。", encoding="utf-8")
        source_ids = register_materials(project, [material], "整理客户资料")
        perform_intake(project, source_ids, "整理客户资料")
        text = truth_path.read_text(encoding="utf-8")
        assert "current_version_id: VER-007" in text
        assert "current_pptx_artifact_id: ART-PPTX-007" in text
        assert "version_map_status: active" in text
        assert "## Custom Operator Notes\nkeep-this-note" in text
        assert "## Project\n" + project.name in text


def test_pptx_export_uses_immutable_version_transaction() -> None:
    if not optional_module("pptx"):
        return
    with tempfile.TemporaryDirectory(prefix="adco-ppt-version-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        material = project / "brief.md"
        material.write_text(
            "客户需要面向城市通勤人群的广告创意提案，强调轻便产品优势，并保留可编辑文本。",
            encoding="utf-8",
        )
        source_ids = register_materials(project, [material], "整理客户资料")
        perform_intake(project, source_ids, "整理客户资料")
        render_creative_proposal(project)
        confirm_client_outline(
            project,
            confirmed_by="fixture-project-owner",
            confirmed_at="2026-07-05T00:00:00Z",
            evidence_ref="user_confirmation:ppt-version-fixture",
        )

        first = export_editable_pptx(project)
        first_bytes = first.read_bytes()
        second = export_editable_pptx(project)
        assert first.name == "client_review_v001.pptx"
        assert second.name == "client_review_v002.pptx"
        assert first.read_bytes() == first_bytes
        assert first != second

        truth = (project / "AD-creative/orchestrator/current_truth.md").read_text(encoding="utf-8")
        assert "current_version_id: VER-PPT-002" in truth
        assert "current_pptx_artifact_id: ART-PPTX-002" in truth
        assert "current_pdf_artifact_id:\n" in truth
        with (project / "AD-creative/orchestrator/version_map.csv").open(newline="", encoding="utf-8") as handle:
            versions = list(csv.DictReader(handle))
        assert next(row for row in versions if row["version_id"] == "VER-PPT-001")["status"] == "superseded"
        assert next(row for row in versions if row["version_id"] == "VER-PPT-002")["status"] == "draft"
        with (project / "AD-creative/orchestrator/artifact_index.csv").open(newline="", encoding="utf-8") as handle:
            artifacts = list(csv.DictReader(handle))
        assert any(row["artifact_id"] == "ART-PPTX-001" and row["path"].endswith(first.name) for row in artifacts)
        assert any(row["artifact_id"] == "ART-PPTX-002" and row["path"].endswith(second.name) for row in artifacts)
        assert_valid(project)

        control_paths = [
            project / "AD-creative/orchestrator/current_truth.md",
            project / "AD-creative/orchestrator/version_map.csv",
            project / "AD-creative/orchestrator/artifact_index.csv",
        ]
        before_check = {path: path.read_bytes() for path in control_paths}
        diagnostic = write_pptx_check(project, first, inspect_pptx(first))
        assert diagnostic.exists()
        assert {path: path.read_bytes() for path in control_paths} == before_check

        first.write_bytes(first_bytes + b"tamper")
        errors, _ = validate(project)
        assert any("ART-PPTX-001 content changed after registration" in error for error in errors), errors
        first.write_bytes(first_bytes)
        assert_valid(project)

        try:
            export_editable_pptx(project, first)
        except RuntimeError as exc:
            assert "canonical version path" in str(exc)
        else:
            raise AssertionError("export-pptx must reject a non-current canonical target")


def test_pptx_export_blocks_unconfirmed_generated_outline() -> None:
    if not optional_module("pptx"):
        return
    with tempfile.TemporaryDirectory(prefix="adco-ppt-unconfirmed-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        material = project / "brief.md"
        material.write_text(
            "客户需要一份城市轻户外广告创意提案，先确认客户可读文本，再制作可编辑演示稿。",
            encoding="utf-8",
        )
        source_ids = register_materials(project, [material], "整理客户资料")
        perform_intake(project, source_ids, "整理客户资料")
        render_creative_proposal(project)
        status, findings, _ = review_client_outline(project)
        assert status == "BLOCKED"
        assert any("确认" in item or "pending" in item for item in findings), findings
        try:
            export_editable_pptx(project)
        except RuntimeError as exc:
            assert "client-outline-gate BLOCKED" in str(exc)
        else:
            raise AssertionError("unconfirmed generated outline must not reach PPT export")


def test_outline_confirmation_binds_presented_bytes_and_stable_content_digest() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-outline-confirmation-basis-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        material = project / "brief.md"
        material.write_text(
            "客户需要城市轻户外广告提案，先确认客户可读文本，再制作可编辑演示稿。",
            encoding="utf-8",
        )
        source_ids = register_materials(project, [material], "整理客户资料")
        perform_intake(project, source_ids, "整理客户资料")
        render_creative_proposal(project)
        outline_path = project / "AD-creative/client_review/client_outline.csv"
        fields, rows = read_csv_rows(outline_path)
        presented_sha = file_sha256(outline_path)
        content_sha = client_outline_confirmed_content_sha256(fields, rows)
        receipt_path = confirm_client_outline(
            project,
            confirmed_by="fixture-project-owner",
            confirmed_at="2026-07-05T00:00:00Z",
            evidence_ref="user_confirmation:outline-basis-fixture",
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert receipt["presented_outline_sha256"] == presented_sha
        assert receipt["confirmed_content_sha256"] == content_sha
        assert receipt["outline_sha256"] == file_sha256(outline_path)
        assert receipt["outline_sha256"] != presented_sha
        fields, rows = read_csv_rows(outline_path)
        assert client_outline_confirmed_content_sha256(fields, rows) == content_sha

        rows[0]["body_copy"] += " 未经再次确认的改动。"
        write_csv_rows(outline_path, fields, rows)
        status, findings, _ = review_client_outline(project)
        assert status == "BLOCKED"
        assert any("内容 digest" in item for item in findings), findings


def test_gate_downgrades_without_adversarial_record() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-no-adv-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_clean_reference(project)
        status, findings, _ = review_reference_pack(project)
        assert status == "PARTIAL_PASS", status
        assert any("反驳性议会" in item for item in findings), findings
        assert_valid(project)


def test_independent_adversarial_review_allows_clean_gate_pass() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-with-adv-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_clean_reference(project)
        add_independent_adversarial_review(
            project,
            "reference_research",
            project / "AD-creative/references/reference_cards.csv",
        )
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
        assert "planned:WORK-GOAL-THREAD-001-THREADS:LANE-01-BRAND_CLIENT" in registry
        assert "mode" in registry
        assert "write_scope" in registry
        assert "receipt_status" in registry
        assert "reconciliation_status" in registry
        assert "COPY_CREATIVE" in registry
        assert "execution_worker" in registry
        assert "isolated_workspace" in registry
        assert (
            "AD-creative/workspaces/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE"
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
            "AD-creative/workspaces/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE"
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
                "AD-creative/workspaces/WORK-GOAL-THREAD-001-THREADS/LANE-02-COPY_CREATIVE"
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


def test_thread_progress_invalidates_stale_convergence_reminder() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-stale-reminder-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        payload = render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-STALE-REMINDER",
            title="Thread progress freshness",
            objective="A stale reminder must not kill a worker after new progress.",
            roles=["copy_creative"],
        )
        work_id = str(payload["work_id"])
        _, registry = read_csv_rows(
            project / "AD-creative/orchestrator/thread_registry.csv"
        )
        lane_id = next(row["lane_id"] for row in registry if row["work_id"] == work_id)
        record_thread_dispatch(
            project,
            lane_id=lane_id,
            work_id=work_id,
            real_thread_id="019f1234-5678-7000-8000-000000000001",
            title_action="dispatcher_set",
            title_verified_at="2026-07-05T00:00:00Z",
            dispatch_evidence="read_thread title and id matched fixture",
            dispatch_status="dispatched",
            absolute_deadline_at="2026-07-05T00:05:00Z",
        )
        record_thread_observation(
            project,
            lane_id=lane_id,
            work_id=work_id,
            state="silent",
            observed_at="2026-07-05T00:04:00Z",
            evidence="initial silence",
            convergence_reminder_sent=True,
        )
        progress = record_thread_observation(
            project,
            lane_id=lane_id,
            work_id=work_id,
            state="active_with_progress",
            observed_at="2026-07-05T00:04:30Z",
            evidence="worker produced new analysis",
        )
        assert progress["convergence_reminder_at"] == "", progress
        try:
            record_thread_observation(
                project,
                lane_id=lane_id,
                work_id=work_id,
                state="thread_not_converged",
                observed_at="2026-07-05T00:05:01Z",
                evidence="stale reminder must not count",
            )
        except ValueError as exc:
            assert "fresh prior silent" in str(exc), exc
        else:
            raise AssertionError("new progress must invalidate a stale reminder")
        record_thread_observation(
            project,
            lane_id=lane_id,
            work_id=work_id,
            state="silent",
            observed_at="2026-07-05T00:05:02Z",
            evidence="fresh silence after latest progress",
            convergence_reminder_sent=True,
        )
        result = record_thread_observation(
            project,
            lane_id=lane_id,
            work_id=work_id,
            state="thread_not_converged",
            observed_at="2026-07-05T00:05:03Z",
            evidence="fresh reminder produced no receipt",
        )
        assert result["state"] == "thread_not_converged", result


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
thread_id: 019f1111-2222-7333-8444-555555555555

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


def test_thread_reconcile_rejects_failed_or_out_of_scope_self_report() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-thread-reconcile-forged-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        payload = render_thread_execution_plan(
            project,
            goal_id="GOAL-THREAD-FORGED",
            title="Reject forged thread receipt",
            objective="Host proof must override worker self-report.",
            roles=["copy_creative"],
        )
        work_id = str(payload["work_id"])
        _, registry = read_csv_rows(
            project / "AD-creative/orchestrator/thread_registry.csv"
        )
        lane_id = next(row["lane_id"] for row in registry if row["work_id"] == work_id)
        real_thread_id = "019f6666-7777-7888-8999-aaaaaaaaaaaa"
        record_thread_dispatch(
            project,
            lane_id=lane_id,
            work_id=work_id,
            real_thread_id=real_thread_id,
            title_action="dispatcher_set",
            title_verified_at="2026-07-05T00:00:00Z",
            dispatch_evidence="read_thread title matched forged-receipt fixture",
            dispatch_status="dispatched",
            absolute_deadline_at="2026-07-05T00:05:00Z",
        )
        _, registry = read_csv_rows(
            project / "AD-creative/orchestrator/thread_registry.csv"
        )
        row = next(item for item in registry if item["lane_id"] == lane_id)
        receipt = project / row["receipt_path"]
        receipt.write_text(
            f"""# Forged Receipt

thread_id: {real_thread_id}
files_changed: /tmp/outside-scope-does-not-exist
validation_result: FAILED all tests
dirty_state_impact: unknown
worker_recommendation: ADOPT
loop_state: blocked
cleanup_actions: did not clean
evidence_refs: made-up
""",
            encoding="utf-8",
        )
        result = reconcile_thread_receipt(
            project,
            lane_id=lane_id,
            work_id=work_id,
            receipt_path_value=row["receipt_path"],
            adoption_decision="ADOPT",
            rejection_reason="",
            reconciled_at="2026-07-05T00:02:00Z",
            cleanup_action="archived_after_rejected_evidence",
            archived_at="2026-07-05T00:02:10Z",
        )
        assert result["status"] == "rejected_evidence", result
        assert "project-relative path" in result["error"], result
        _, registry = read_csv_rows(
            project / "AD-creative/orchestrator/thread_registry.csv"
        )
        row = next(item for item in registry if item["lane_id"] == lane_id)
        assert row["adoption_decision"] == "REJECT"
        assert row["reconciliation_status"] == "rejected_evidence"


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
thread_id: 019f1111-2222-7333-8444-555555555555
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-MISSING-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
worker_recommendation: ADOPT
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
thread_id: 019f1111-2222-7333-8444-555555555555
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-THREAD-ID-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
worker_recommendation: ADOPT
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
thread_id: 019f1111-2222-7333-8444-555555555555
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-OBSERVATION-EVIDENCE-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
worker_recommendation: ADOPT
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
thread_id: 019f1111-2222-7333-8444-555555555555
files_changed: no files changed
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: no tracked or untracked files changed
worker_recommendation: ADOPT
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
thread_id: 019f1111-2222-7333-8444-555555555555
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-PROOF-RECEIPT-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
worker_recommendation: ADOPT
loop_state: reconciled
cleanup_actions: archived worker thread after receipt reconciliation
evidence_refs: thread_registry.csv row LANE-01-COPY_CREATIVE; receipt path; validation command above

## Summary

Production worker returned file-level proof and validation evidence.
""",
            encoding="utf-8",
        )
        attach_host_scope_proof_fixture(project, receipt_path)
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
thread_id: 019f1111-2222-7333-8444-555555555555
files_changed: AD-creative/workspaces/WORK-GOAL-THREAD-HELPER-PROOF-THREADS/LANE-01-COPY_CREATIVE/copy_drafts.md
validation_result: PASS - PYTHONDONTWRITEBYTECODE=1 python3 tools/test_goal_workflow.py
dirty_state_impact: only declared isolated workspace and receipt were changed
worker_recommendation: ADOPT
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
        attach_host_scope_proof_fixture(project, receipt_path)
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
            "AD-creative/workspaces/WORK-GOAL-THREAD-PRODUCTION-THREADS/LANE-01-FILM_DIRECTOR"
            in combined
        )
        assert (
            "AD-creative/workspaces/WORK-GOAL-THREAD-PRODUCTION-THREADS/LANE-02-ART_DESIGN"
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


def test_duffy_hardening_cli_commands_are_exposed() -> None:
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices  # type: ignore[attr-defined]
    for command in [
        "agency-audit",
        "migrate-control-plane",
        "preflight-skill",
        "preflight-asset",
        "dispatch-record",
        "thread-observe",
        "thread-reconcile",
        "confirm-client-outline",
        "client-outline-gate",
        "client-language-gate",
        "asset-current-manifest",
        "browser-asset-intake",
        "visual-layout-gate",
        "dedupe-audit",
        "cleanup-plan",
        "final-delivery-lock",
    ]:
        assert command in commands


def test_client_outline_gate_blocks_until_page_framework_exists() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-client-outline-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        status, findings, _ = review_client_outline(project)
        assert status == "BLOCKED"
        assert any("客户可读文本框架" in item for item in findings)

        append_csv_row(
            project / "AD-creative/client_review/client_outline.csv",
            {
                "slide_id": "S01",
                "page_title": "十年友谊的第一个记忆点",
                "body_copy": "用客户能读懂的故事段落说明这一页要解决的传播问题。",
                "client_confirmation_point": "确认这页是否作为开篇方向。",
                "material_role": "使用已登记主视觉作为情绪锚点。",
                "visual_slot": "横屏主视觉占位，低密度留白。",
                "visual_asset_status": "placeholder",
                "asset_ids": "",
                "visibility": "client_visible_ready",
                "status": "ready",
                "notes": "",
            },
        )
        confirm_client_outline(
            project,
            confirmed_by="fixture-project-owner",
            confirmed_at="2026-07-05T00:00:00Z",
            evidence_ref="user_confirmation:outline-gate-fixture",
        )
        status, findings, _ = review_client_outline(project)
        assert status == "PASS", findings


def test_client_language_gate_blocks_internal_execution_terms() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-client-language-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        append_csv_row(
            project / "AD-creative/client_review/client_outline.csv",
            {
                "slide_id": "S01",
                "page_title": "客户稿标题",
                "body_copy": "这里不能写 prompt 或 thread 执行过程。",
                "client_confirmation_point": "确认表达。",
                "material_role": "主图。",
                "visual_slot": "横屏主图占位。",
                "visual_asset_status": "placeholder",
                "asset_ids": "",
                "visibility": "client_visible_ready",
                "status": "ready",
                "notes": "",
            },
        )
        status, findings, _ = review_client_language(project)
        assert status == "BLOCKED"
        assert any("prompt" in item or "thread" in item for item in findings)


def test_asset_current_manifest_and_visual_layout_gate_use_real_assets() -> None:
    if not optional_module("PIL"):
        return

    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="adco-asset-current-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        source = project / "source.png"
        Image.new("RGB", (1200, 800), color=(100, 120, 160)).save(source)
        asset_id, _ = add_visual_asset(
            project,
            source,
            "KV-01",
            "",
            "pending",
            "browser_download",
            "internal_only",
            "PASS",
            "low",
            "browser evidence",
            "layout ready",
            selected=True,
        )
        rows, _ = refresh_asset_current_manifest(project)
        assert any(row.get("asset_id") == asset_id and row.get("sha256") for row in rows)
        status, findings, _ = review_visual_layout(project)
        assert status == "BLOCKED"
        assert any("client_outline" in item for item in findings)


def test_final_delivery_lock_protects_user_placed_files() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-final-lock-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        final_file = project / "05_最终交付_FinalDelivery/client_final.pdf"
        final_file.write_bytes(b"%PDF-1.4\n")
        errors, _ = validate(project)
        assert any("FinalDelivery file is not locked" in error for error in errors), errors
        locked, lock_path = final_delivery_lock(project)
        assert lock_path.exists()
        assert any(row.get("path", "").endswith("client_final.pdf") and row.get("protected") == "yes" for row in locked)
        original_hash = next(
            row["sha256"] for row in locked if row.get("path", "").endswith("client_final.pdf")
        )
        plan_path, actions = cleanup_plan(project)
        assert plan_path.exists()
        assert any("LOCKED_DO_NOT_MOVE_OR_DELETE" in action for action in actions)
        assert_valid(project)

        final_file.write_bytes(b"%PDF-1.4\nchanged\n")
        errors, _ = validate(project)
        assert any("FinalDelivery protected file changed" in error for error in errors), errors
        try:
            final_delivery_lock(project)
        except RuntimeError as exc:
            assert "protected file changed" in str(exc)
        else:
            raise AssertionError("FinalDelivery lock must not refresh a changed baseline")
        with lock_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert next(row["sha256"] for row in rows if row.get("path", "").endswith("client_final.pdf")) == original_hash

        final_file.write_bytes(b"%PDF-1.4\n")
        assert_valid(project)
        final_file.unlink()
        errors, _ = validate(project)
        assert any("FinalDelivery locked file missing" in error for error in errors), errors
        try:
            final_delivery_lock(project)
        except RuntimeError as exc:
            assert "protected file missing" in str(exc)
        else:
            raise AssertionError("FinalDelivery lock must not hide a missing protected file")


def test_migrate_control_plane_creates_new_gate_files() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-migrate-control-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        for rel_path in [
            "AD-creative/client_review/client_outline.csv",
            "AD-creative/visual_assets/asset_current_manifest.csv",
            "AD-creative/orchestrator/final_delivery_lock.csv",
            "AD-creative/orchestrator/agency/specialist_preflight.csv",
        ]:
            (project / rel_path).unlink()
        dry = migrate_control_plane(project, dry_run=True)
        assert len(dry["changes"]) >= 4
        result = migrate_control_plane(project, dry_run=False)
        assert result["warnings"] == []
        assert (project / "AD-creative/client_review/client_outline.csv").exists()
        assert (project / "AD-creative/orchestrator/agency/specialist_preflight.csv").exists()
        assert_valid(project)


def test_migrate_control_plane_normalizes_legacy_short_rows() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-migrate-short-row-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        artifact_path = project / "AD-creative/orchestrator/artifact_index.csv"
        legacy_fields = ARTIFACT_INDEX_FIELDS[:-4]
        legacy_row = {field: "" for field in legacy_fields}
        legacy_row.update(
            {
                "artifact_id": "ART-LEGACY-001",
                "artifact_type": "legacy_fixture",
                "path": "AD-creative/orchestrator/current_truth.md",
                "stage": "migration_test",
                "version": "v001",
                "status": "internal_review",
                "visibility": "internal_only",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        )
        write_csv_rows(artifact_path, legacy_fields, [legacy_row])
        header = artifact_path.read_text(encoding="utf-8").splitlines()[0]
        artifact_path.write_text(
            ",".join(ARTIFACT_INDEX_FIELDS) + "\n" + artifact_path.read_text(encoding="utf-8").splitlines()[1] + "\n",
            encoding="utf-8",
        )
        assert header == ",".join(legacy_fields)

        dry = migrate_control_plane(project, dry_run=True)
        assert "normalize_csv_rows:AD-creative/orchestrator/artifact_index.csv" in dry["changes"]
        migrate_control_plane(project, dry_run=False)
        fields, rows = read_csv_rows(artifact_path)
        assert fields == ARTIFACT_INDEX_FIELDS
        assert all(row.get(field) is not None for row in rows for field in fields)
        assert None not in rows[0]


def test_migrate_control_plane_adds_missing_current_truth_keys_without_overwrite() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-migrate-truth-keys-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        truth_path = project / "AD-creative/orchestrator/current_truth.md"
        truth = truth_path.read_text(encoding="utf-8").replace(
            "version_map_status:\n", "version_map_status: legacy-preserve\n"
        )
        removed = {
            "current_pdf_artifact_id",
            "current_preview_artifact_id",
            "current_text_extract_artifact_id",
        }
        truth_path.write_text(
            "\n".join(
                line
                for line in truth.splitlines()
                if line.partition(":")[0].strip() not in removed
            )
            + "\n",
            encoding="utf-8",
        )
        dry = migrate_control_plane(project, dry_run=True)
        assert any(
            item.startswith("add_current_truth_keys:") for item in dry["changes"]
        ), dry
        migrate_control_plane(project)
        migrated = truth_path.read_text(encoding="utf-8")
        assert "version_map_status: legacy-preserve" in migrated
        for key in removed:
            assert migrated.count(f"{key}:") == 1
        assert_valid(project)


def test_duffy_v2_regression_allows_long_low_density_client_outline() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-duffy-v2-outline-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        rows = []
        for index in range(1, 25):
            rows.append(
                {
                    "slide_id": f"S{index:02d}",
                    "page_title": f"十年友谊章节 {index:02d}",
                    "body_copy": "这一页只讲一个客户能判断的故事节点：记忆、关系、画面动作和下一步确认，避免生产表和短 pitch。",
                    "client_confirmation_point": "确认这一页是否保留为客户方案叙事页。",
                    "material_role": "让画面辅助客户判断故事关系，不替代正文。",
                    "visual_slot": "横屏低密度画面占位；已有图或待生成图必须在资产表登记。",
                    "visual_asset_status": "to_generate",
                    "asset_ids": "",
                    "visibility": "client_visible_ready",
                    "status": "ready",
                    "notes": "duffy_v2_regression_low_density_page",
                }
            )
        write_csv_rows(project / "AD-creative/client_review/client_outline.csv", CLIENT_OUTLINE_FIELDS, rows)
        confirm_client_outline(
            project,
            confirmed_by="fixture-project-owner",
            confirmed_at="2026-07-05T00:00:00Z",
            evidence_ref="user_confirmation:duffy-outline-fixture",
        )
        status, findings, _ = review_client_outline(project)
        assert status == "PASS", findings

        rows[0]["visual_slot"] = ""
        write_csv_rows(project / "AD-creative/client_review/client_outline.csv", CLIENT_OUTLINE_FIELDS, rows)
        status, findings, _ = review_client_outline(project)
        assert status == "BLOCKED"
        assert any("visual_slot" in item for item in findings)

        rows[0]["visual_slot"] = "横屏低密度画面占位。"
        rows[0]["body_copy"] = "过密内容" * 130
        write_csv_rows(project / "AD-creative/client_review/client_outline.csv", CLIENT_OUTLINE_FIELDS, rows)
        status, findings, _ = review_client_outline(project)
        assert status == "BLOCKED"
        assert any("过密" in item for item in findings)


def test_browser_asset_current_manifest_records_platform_conversation_and_qa_flags() -> None:
    if not optional_module("PIL"):
        return

    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="adco-browser-asset-current-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        source = project / "grok_candidate.png"
        Image.new("RGB", (1600, 900), color=(180, 150, 120)).save(source)
        asset_id, _ = add_visual_asset(
            project,
            source,
            "DUFFY-KV-01",
            "",
            "pending",
            "grok_browser_download",
            "internal_only",
            "PASS",
            "low",
            "Grok browser canvas evidence",
            "candidate from existing browser project",
            selected=True,
        )
        rows, _ = refresh_asset_current_manifest(project)
        row = next(item for item in rows if item.get("asset_id") == asset_id)
        assert row.get("platform") == "grok"
        assert row.get("local_file")
        assert row.get("qa_flags")


def main() -> int:
    test_project_agents_policy_created_and_validated()
    test_validate_rejects_missing_project_agents_policy()
    test_existing_agents_policy_is_not_overwritten()
    test_human_workspace_indexes_mirror_control_plane()
    test_intake_preserves_version_truth_and_custom_sections()
    test_pptx_export_uses_immutable_version_transaction()
    test_pptx_export_blocks_unconfirmed_generated_outline()
    test_outline_confirmation_binds_presented_bytes_and_stable_content_digest()
    test_agents_policy_status_clears_after_manual_merge()
    test_gate_downgrades_without_adversarial_record()
    test_independent_adversarial_review_allows_clean_gate_pass()
    test_goal_run_stops_without_material()
    test_thread_plan_creates_control_plane()
    test_thread_plan_includes_harness_loop_and_adoption_contracts()
    test_thread_progress_invalidates_stale_convergence_reminder()
    test_execution_worker_receipt_cannot_be_prompt_only()
    test_threadops_validation_allows_pending_execution_worker_receipt_template()
    test_threadops_validation_rejects_prompt_only_received_execution_receipt()
    test_thread_reconcile_rejects_failed_or_out_of_scope_self_report()
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
    test_duffy_hardening_cli_commands_are_exposed()
    test_client_outline_gate_blocks_until_page_framework_exists()
    test_client_language_gate_blocks_internal_execution_terms()
    test_asset_current_manifest_and_visual_layout_gate_use_real_assets()
    test_final_delivery_lock_protects_user_placed_files()
    test_migrate_control_plane_creates_new_gate_files()
    test_migrate_control_plane_normalizes_legacy_short_rows()
    test_migrate_control_plane_adds_missing_current_truth_keys_without_overwrite()
    test_duffy_v2_regression_allows_long_low_density_client_outline()
    test_browser_asset_current_manifest_records_platform_conversation_and_qa_flags()
    if OPTIONAL_SKIPS:
        print("TEST_GOAL_WORKFLOW_OPTIONAL_SKIPS=" + "; ".join(OPTIONAL_SKIPS))
    print("TEST_GOAL_WORKFLOW=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
