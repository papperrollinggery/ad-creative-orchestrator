#!/usr/bin/env python3
"""Regression checks for evidence-bound facts and non-inverted gaps."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from ad_creative_operator import (
    ensure_delivery_project,
    ensure_project,
    gap_templates,
    perform_intake,
    read_csv_rows,
    register_materials,
    write_csv_rows,
)
from adco_core.facts import (
    classify_requirement,
    export_intake_analysis_request,
    import_intake_analysis,
    run_evidence_intake,
)
from adco_core.ingestion import load_evidence_chunks
from validate_project import validate_client_delivery_readiness


def _row(source_id: str, path: Path, project: Path) -> dict[str, str]:
    return {
        "source_event_id": source_id,
        "file_paths": path.relative_to(project).as_posix(),
        "declared_semantics": "fact fixture",
    }


def test_present_assets_do_not_become_false_gaps() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-present-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "brief.md"
        source.write_text(
            "客户已提供产品图，附件中有品牌 logo。客户要求交付可编辑 PPTX。",
            encoding="utf-8",
        )
        result = run_evidence_intake(project, [_row("SRC-001", source, project)])
        facts = {fact.fact_key: fact for fact in result.facts}
        assert facts["asset.product_images"].state == "present"
        assert facts["brand.logo"].state == "present"
        assert all("asset.product_images" not in gap["description"] for gap in result.new_gaps)
        assert all("brand.logo" not in gap["description"] for gap in result.new_gaps)
        assert gap_templates([], source.read_text(encoding="utf-8")) == []


def test_evidence_claim_client_and_asset_authorization_axes_stay_independent() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-independent-axes-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        source = project / "brief.md"
        source.write_text(
            "客户已提供产品图。客户要求宣传续航 10 小时，但宣称措辞、法务审批和素材客户可见授权仍待分别确认。",
            encoding="utf-8",
        )
        result = run_evidence_intake(project, [_row("SRC-AXES-001", source, project)])
        facts = {fact.fact_key: fact for fact in result.facts}
        assert facts["asset.product_images"].state == "present"

        _, requirements = read_csv_rows(
            project / "AD-creative/orchestrator/requirements.csv"
        )
        assert requirements
        assert all(not row.get("confirmation_ref", "") for row in requirements)
        assert all(not row.get("confirmed_by", "") for row in requirements)
        _, authorizations = read_csv_rows(
            project / "AD-creative/visual_assets/asset_authorizations.csv"
        )
        _, decisions = read_csv_rows(
            project / "AD-creative/orchestrator/decisions.csv"
        )
        assert authorizations == []
        assert decisions == []
        truth = (
            project / "AD-creative/orchestrator/current_truth.md"
        ).read_text(encoding="utf-8")
        assert "evidence_source_authority" in truth
        assert "claim_wording_authority" in truth
        assert "client_legal_approval_authority" in truth
        assert "asset_authorization_authority" in truth


def test_conflict_and_blocking_unknown_create_evidence_bound_gaps() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-conflict-") as raw:
        project = Path(raw)
        ensure_project(project)
        present = project / "present.md"
        missing = project / "missing.md"
        present.write_text("客户已提供产品图。", encoding="utf-8")
        missing.write_text("客户尚未提供产品图。", encoding="utf-8")
        first = run_evidence_intake(project, [_row("SRC-001", present, project)])
        second = run_evidence_intake(project, [_row("SRC-002", missing, project)])
        facts = {fact.fact_key: fact for fact in second.facts}
        assert facts["asset.product_images"].state == "conflicting"
        assert len(facts["asset.product_images"].evidence_refs) == 2
        assert any("asset.product_images 冲突" in gap["description"] for gap in second.new_gaps)

        request, request_path = export_intake_analysis_request(project)
        assert request_path.is_file()
        evidence_id = request["evidence_chunks"][0]["chunk_id"]
        analysis_path = project / "analysis.json"
        analysis_path.write_text(
            json.dumps(
                {
                    "analysis_version": "1.0",
                    "evidence_snapshot_sha256": request["evidence_snapshot_sha256"],
                    "facts": [
                        {
                            "fact_key": "legal.claims",
                            "state": "unknown",
                            "value": "",
                            "evidence_refs": [evidence_id],
                            "confidence": 0.6,
                            "owner": "client",
                            "blocking": True,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        _, gaps, _ = import_intake_analysis(project, analysis_path)
        assert any("legal.claims 待确认" in gap["description"] for gap in gaps)

        invalid = project / "invalid-analysis.json"
        invalid.write_text(
            json.dumps(
                {
                    "analysis_version": "1.0",
                    "evidence_snapshot_sha256": request["evidence_snapshot_sha256"],
                    "facts": [
                        {
                            "fact_key": "invalid.ref",
                            "state": "present",
                            "value": "x",
                            "evidence_refs": ["EVC-NOT-REAL"],
                            "confidence": 1.0,
                            "owner": "model",
                            "blocking": False,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        try:
            import_intake_analysis(project, invalid)
        except ValueError as exc:
            assert "evidence_refs" in str(exc)
        else:
            raise AssertionError("analysis with stale evidence_refs must fail")
        assert first.ingestion.chunks


def test_import_rejects_analysis_bound_to_an_older_evidence_snapshot() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-analysis-snapshot-") as raw:
        project = Path(raw)
        ensure_project(project)
        first = project / "first.md"
        second = project / "second.md"
        first.write_text("客户要求面向城市通勤人群。", encoding="utf-8")
        second.write_text("客户补充：目标人群改为亲子家庭。", encoding="utf-8")
        run_evidence_intake(project, [_row("SRC-001", first, project)])
        request, _ = export_intake_analysis_request(project)
        stale = project / "stale-analysis.json"
        stale.write_text(
            json.dumps(
                {
                    "analysis_version": "1.0",
                    "evidence_snapshot_sha256": request["evidence_snapshot_sha256"],
                    "facts": [
                        {
                            "fact_key": "campaign.audience",
                            "state": "present",
                            "value": "城市通勤人群",
                            "evidence_refs": [request["evidence_chunks"][0]["chunk_id"]],
                            "confidence": 0.9,
                            "owner": "model",
                            "blocking": False,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        legacy = project / "legacy-analysis.json"
        legacy_payload = json.loads(stale.read_text(encoding="utf-8"))
        legacy_payload.pop("evidence_snapshot_sha256")
        legacy.write_text(json.dumps(legacy_payload, ensure_ascii=False), encoding="utf-8")
        facts_path = project / "AD-creative/orchestrator/fact_inventory.jsonl"
        gaps_path = project / "AD-creative/orchestrator/gaps.csv"
        before = (facts_path.read_bytes(), gaps_path.read_bytes())
        try:
            import_intake_analysis(project, legacy)
        except ValueError as exc:
            assert "evidence snapshot" in str(exc)
        else:
            raise AssertionError("analysis without a snapshot binding must fail")
        assert (facts_path.read_bytes(), gaps_path.read_bytes()) == before
        run_evidence_intake(project, [_row("SRC-002", second, project)])
        before = (facts_path.read_bytes(), gaps_path.read_bytes())
        try:
            import_intake_analysis(project, stale)
        except ValueError as exc:
            assert "evidence snapshot" in str(exc)
        else:
            raise AssertionError("analysis from an older evidence snapshot must fail")
        assert (facts_path.read_bytes(), gaps_path.read_bytes()) == before


def test_registration_reuses_unchanged_material_and_replaces_changed_source_evidence() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-registration-") as raw:
        project = Path(raw)
        ensure_project(project)
        material = project / "brief.md"
        material.write_text("客户已提供产品图。客户要求白天拍摄。", encoding="utf-8")
        first_ids = register_materials(project, [material], "首次 intake")
        assert len(first_ids) == 1
        perform_intake(project, first_ids, "首次 intake")
        initial_chunks = load_evidence_chunks(project)
        assert len(initial_chunks) == 1

        assert register_materials(project, [material], "重复运行") == []
        assert load_evidence_chunks(project) == initial_chunks

        material.write_text("客户尚未提供产品图。客户要求日间拍摄，禁止夜景。", encoding="utf-8")
        changed_ids = register_materials(project, [material], "资料更新")
        assert changed_ids == first_ids
        perform_intake(project, changed_ids, "资料更新")
        changed_chunks = load_evidence_chunks(project)
        assert len(changed_chunks) == 1
        assert changed_chunks[0].source_event_id == first_ids[0]
        assert "禁止夜景" in changed_chunks[0].text
        facts = {
            fact.fact_key: fact
            for fact in run_evidence_intake(
                project,
                [],
            ).facts
        }
        assert facts["asset.product_images"].state == "missing"
        assert facts["asset.product_images"].evidence_refs == [changed_chunks[0].chunk_id]
        _, requirements = read_csv_rows(
            project / "AD-creative/orchestrator/requirements.csv"
        )
        assert [row["statement"] for row in requirements] == [
            "客户尚未提供产品图。客户要求日间拍摄，禁止夜景。"
        ]


def test_registration_retries_after_budget_overflow_with_a_new_budget() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-budget-retry-") as raw:
        project = Path(raw)
        ensure_project(project)
        material = project / "large.md"
        material.write_text("客户要求完整读取资料。" * 100, encoding="utf-8")
        source_ids = register_materials(
            project, [material], "低预算 intake", max_total_chars=100
        )
        low = perform_intake(project, source_ids, "低预算 intake", max_total_chars=100)
        assert low["over_budget_files"] == 1
        retry_ids = register_materials(
            project, [material], "提高预算", max_total_chars=20_000
        )
        assert retry_ids == source_ids
        high = perform_intake(project, retry_ids, "提高预算", max_total_chars=20_000)
        assert high["over_budget_files"] == 0
        assert high["evidence_chunks"] > 0


def test_registration_retries_after_parser_failure_at_the_same_budget() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-parser-retry-") as raw:
        project = Path(raw)
        ensure_project(project)
        material = project / "brief.md"
        material.write_text("客户要求白天拍摄。", encoding="utf-8")
        source_ids = register_materials(project, [material], "首次 intake")
        with patch("adco_core.ingestion.parse_file", side_effect=ValueError("fixture parser failure")):
            failed = perform_intake(project, source_ids, "首次 intake")
        assert failed["parser_errors"] == 1
        retry_ids = register_materials(project, [material], "恢复后重试")
        assert retry_ids == source_ids
        recovered = perform_intake(project, retry_ids, "恢复后重试")
        assert recovered["parser_errors"] == 0
        assert recovered["evidence_chunks"] == 1


def test_ambiguous_legacy_same_path_history_blocks_before_mutation() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-ambiguous-source-") as raw:
        project = Path(raw) / "project"
        ensure_project(project)
        material = project / "brief.md"
        material.write_text("客户要求白天拍摄。", encoding="utf-8")
        source_ids = register_materials(project, [material], "首次 intake")
        perform_intake(project, source_ids, "首次 intake")
        source_path = project / "AD-creative/orchestrator/source_events.csv"
        source_fields, source_rows = read_csv_rows(source_path)
        duplicate = dict(source_rows[0])
        duplicate["source_event_id"] = "SRC-LEGACY-002"
        source_rows.append(duplicate)
        write_csv_rows(source_path, source_fields, source_rows)
        run_evidence_intake(project, [_row("SRC-LEGACY-002", material, project)])
        tracked = [
            source_path,
            project / "AD-creative/orchestrator/evidence_chunks.jsonl",
            project / "AD-creative/orchestrator/requirements.csv",
        ]
        before = {path: path.read_bytes() for path in tracked}
        material.write_text("客户禁止夜景。", encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("ad_creative_operator.py")),
                "run",
                str(project),
                "--material",
                str(material),
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 1
        payload = json.loads(completed.stdout)
        assert payload["run"] == "CHECK"
        assert payload["error"]["code"] == "runtime_error"
        assert "ambiguous" in payload["error"]["message"]
        assert {path: path.read_bytes() for path in tracked} == before


def test_mixed_batch_marks_only_successful_sources_reusable() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-mixed-batch-") as raw:
        project = Path(raw)
        ensure_project(project)
        small = project / "small.md"
        large = project / "large.md"
        small.write_text("客户要求白天拍摄。", encoding="utf-8")
        large.write_text("客户要求完整读取资料。" * 100, encoding="utf-8")
        source_ids = register_materials(
            project,
            [small, large],
            "混合 intake",
            max_total_chars=100,
        )
        result = perform_intake(
            project,
            source_ids,
            "混合 intake",
            max_total_chars=100,
        )
        assert result["materials"] == 1
        assert result["over_budget_files"] == 1
        assert register_materials(
            project, [small], "重复 small", max_total_chars=100
        ) == []
        assert register_materials(
            project, [large], "重试 large", max_total_chars=100
        ) == [source_ids[1]]


def test_changed_source_preserves_confirmed_requirement_for_reconfirmation() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-confirmed-source-change-") as raw:
        project = Path(raw)
        ensure_project(project)
        material = project / "brief.md"
        material.write_text("客户要求白天拍摄。", encoding="utf-8")
        source_ids = register_materials(project, [material], "首次 intake")
        perform_intake(project, source_ids, "首次 intake")
        requirements_path = project / "AD-creative/orchestrator/requirements.csv"
        fields, rows = read_csv_rows(requirements_path)
        rows[0].update(
            {
                "status": "confirmed_by_workflow",
                "confirmation_ref": "LOCAL-ASSERTION-001",
                "confirmed_by": "fixture-user",
                "confirmed_at": "2026-09-05T00:00:00+08:00",
            }
        )
        write_csv_rows(requirements_path, fields, rows)
        material.write_text("客户禁止夜景。", encoding="utf-8")
        changed_ids = register_materials(project, [material], "资料更新")
        perform_intake(project, changed_ids, "资料更新")
        _, updated = read_csv_rows(requirements_path)
        confirmed = next(row for row in updated if row["requirement_id"] == "REQ-001")
        assert confirmed["status"] == "needs_reconfirmation"
        assert confirmed["confirmation_ref"] == "LOCAL-ASSERTION-001"
        assert "source evidence was replaced" in confirmed["open_questions"]


def test_current_truth_excludes_closed_gaps_from_open_questions() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-closed-gap-") as raw:
        project = Path(raw)
        ensure_project(project)
        material = project / "brief.md"
        material.write_text("客户希望做一支通勤广告。", encoding="utf-8")
        source_ids = register_materials(project, [material], "首次 intake")
        perform_intake(project, source_ids, "首次 intake")
        gap_path = project / "AD-creative/orchestrator/gaps.csv"
        fields, rows = read_csv_rows(gap_path)
        rows.append(
            {
                **{field: "" for field in fields},
                "gap_id": "GAP-CLOSED",
                "description": "已解决的历史问题，不应再追问",
                "status": "closed",
                "impact": "blocking",
                "question_for_client": "历史问题已解决",
                "recommended_action": "无需操作",
                "owner": "client",
            }
        )
        write_csv_rows(gap_path, fields, rows)
        perform_intake(project, ["SRC-NOT-REGISTERED"], "刷新摘要")
        truth = (project / "AD-creative/orchestrator/current_truth.md").read_text(
            encoding="utf-8"
        )
        assert "历史问题已解决" not in truth


def test_missing_delivery_assets_are_deferred_on_content_and_block_delivery() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-surface-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "missing-assets.md"
        source.write_text(
            "客户尚未提供产品图，客户未提供品牌 logo，且不允许 AI 生成图用于客户审阅。",
            encoding="utf-8",
        )
        result = run_evidence_intake(project, [_row("SRC-001", source, project)])
        assert result.new_gaps
        content_impacts = {
            gap["impact"]
            for gap in result.new_gaps
            if any(
                key in gap["description"]
                for key in (
                    "asset.product_images",
                    "brand.logo",
                    "policy.ai_client_visibility",
                )
            )
        }
        assert content_impacts == {"low"}, (content_impacts, result.new_gaps)

        gap_path = project / "AD-creative/orchestrator/gaps.csv"
        gap_fields, content_gap_rows = read_csv_rows(gap_path)
        for row in content_gap_rows:
            if any(
                key in row["description"]
                for key in (
                    "asset.product_images",
                    "brand.logo",
                    "policy.ai_client_visibility",
                )
            ):
                row["status"] = "closed"
        write_csv_rows(gap_path, gap_fields, content_gap_rows)

        ensure_delivery_project(project)
        delivery_errors_before_resync = validate_client_delivery_readiness(
            project,
            [],
            [],
            [],
        )
        assert any(
            "unresolved blocking facts" in item
            and "asset.product_images" in item
            for item in delivery_errors_before_resync
        ), delivery_errors_before_resync
        rerun = run_evidence_intake(project, [_row("SRC-001", source, project)])
        assert rerun.new_gaps == []
        _, gap_rows = read_csv_rows(project / "AD-creative/orchestrator/gaps.csv")
        impacts = {
            row["impact"]
            for row in gap_rows
            if any(
                key in row["description"]
                for key in (
                    "asset.product_images",
                    "brand.logo",
                    "policy.ai_client_visibility",
                )
            )
        }
        assert impacts == {"blocking"}, impacts
        statuses = {
            row["status"]
            for row in gap_rows
            if any(
                key in row["description"]
                for key in (
                    "asset.product_images",
                    "brand.logo",
                    "policy.ai_client_visibility",
                )
            )
        }
        assert statuses == {"open"}, statuses
        delivery_errors = validate_client_delivery_readiness(project, [], [], [])
        assert any("unresolved blocking gaps" in item for item in delivery_errors)


def test_only_uses_word_boundaries_in_english_requirements() -> None:
    assert classify_requirement("A lonely commuter opens the product.")[0] == "brief"
    assert classify_requirement("Shoot only in the apartment living room.")[0] == "constraint"
    with tempfile.TemporaryDirectory(prefix="adco-facts-only-boundary-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "brief.md"
        source.write_text("A lonely commuter opens the product after work.", encoding="utf-8")
        result = run_evidence_intake(project, [_row("SRC-ONLY-001", source, project)])
        assert result.new_requirements == []


def main() -> int:
    test_present_assets_do_not_become_false_gaps()
    test_evidence_claim_client_and_asset_authorization_axes_stay_independent()
    test_conflict_and_blocking_unknown_create_evidence_bound_gaps()
    test_import_rejects_analysis_bound_to_an_older_evidence_snapshot()
    test_registration_reuses_unchanged_material_and_replaces_changed_source_evidence()
    test_registration_retries_after_budget_overflow_with_a_new_budget()
    test_registration_retries_after_parser_failure_at_the_same_budget()
    test_ambiguous_legacy_same_path_history_blocks_before_mutation()
    test_mixed_batch_marks_only_successful_sources_reusable()
    test_changed_source_preserves_confirmed_requirement_for_reconfirmation()
    test_current_truth_excludes_closed_gaps_from_open_questions()
    test_missing_delivery_assets_are_deferred_on_content_and_block_delivery()
    test_only_uses_word_boundaries_in_english_requirements()
    print("TEST_FACT_INVENTORY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
