#!/usr/bin/env python3
"""Regression checks for creative brief, candidate, and Critic boundaries."""

from __future__ import annotations

import copy
import csv
import json
import os
import threading
import tempfile
from pathlib import Path
from unittest.mock import patch

from ad_creative_operator import ensure_project, render_creative_proposal
from adco_core.creative_contract import (
    BRIEF_CONTRACT_REL,
    BRIEF_MANIFEST_REL,
    BRIEF_SNAPSHOT_REL,
    CANDIDATE_IMPORT_RECEIPT_REL,
    CANDIDATE_SCHEMA_REL,
    CREATIVE_DIRECTIONS_REL,
    CREATIVE_DIRECTION_FIELDS,
    CREATIVE_ROOT,
    CURRENT_CANDIDATE_REL,
    OPTION_MATRIX_REL,
    _prohibited_claims,
    confirm_creative_requirement,
    create_creative_brief,
    file_sha256,
    import_creative_candidate,
    payload_sha256,
    resolve_creative_constraint,
    review_creative_candidate,
)
from adco_core.facts import run_evidence_intake as _run_evidence_intake_impl
from adco_core.safe_write import atomic_write_bytes as real_atomic_write_bytes
from adco_core.safe_write import atomic_write_text, read_project_bytes


def run_evidence_intake(
    project: Path,
    source_rows: list[dict[str, str]],
    *,
    max_total_chars: int = 2_000_000,
):
    """Register fixture sources before exercising the real intake path."""
    source_path = project / "AD-creative/orchestrator/source_events.csv"
    with source_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        existing = [dict(row) for row in reader]
    existing_ids = {row.get("source_event_id") for row in existing}
    for source in source_rows:
        source_id = source["source_event_id"]
        if source_id in existing_ids:
            continue
        existing.append(
            {
                "source_event_id": source_id,
                "received_at": "2026-07-22T00:00:00+08:00",
                "source_owner": "fixture-human",
                "source_type": "file",
                "declared_semantics": source.get("declared_semantics", "test fixture"),
                "file_paths": source["file_paths"],
                "raw_summary": "registered test fixture",
                "trust_level": "human_reviewed",
                "affects_requirements": "yes",
                "affects_artifacts": "",
                "supersedes_event_ids": "",
                "notes": "test-only registration",
            }
        )
        existing_ids.add(source_id)
    with source_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(existing)
    return _run_evidence_intake_impl(
        project,
        source_rows,
        max_total_chars=max_total_chars,
    )


def _append_confirmation_event(
    project: Path,
    *,
    event_id: str,
    authority_class: str,
    semantics: str,
    affects_requirements: set[str],
    affects_artifacts: set[str] | None = None,
) -> str:
    evidence_path = project / "confirmations" / f"{event_id}.md"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        f"Confirmation event {event_id}\nsemantics: {semantics}\n",
        encoding="utf-8",
    )
    source_path = project / "AD-creative/orchestrator/source_events.csv"
    with source_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    rows.append(
        {
            "source_event_id": event_id,
            "received_at": "2026-07-22T01:00:00+08:00",
            "source_owner": authority_class,
            "source_type": f"{authority_class}_confirmation",
            "declared_semantics": semantics,
            "file_paths": evidence_path.relative_to(project).as_posix(),
            "raw_summary": "typed fixture confirmation",
            "trust_level": f"{authority_class}_confirmed",
            "affects_requirements": ";".join(sorted(affects_requirements)),
            "affects_artifacts": ";".join(sorted(affects_artifacts or set())),
            "supersedes_event_ids": "",
            "notes": "test-only typed authority event",
        }
    )
    with source_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return f"{authority_class}_confirmation:{event_id}"


def _prepare(project: Path) -> tuple[str, str]:
    ensure_project(project)
    source = project / "brief.md"
    source.write_text(
        "客户已提供产品图和品牌 logo。客户要求面向雨天通勤人群制作可编辑广告提案。",
        encoding="utf-8",
    )
    result = run_evidence_intake(
        project,
        [
            {
                "source_event_id": "SRC-001",
                "file_paths": source.name,
                "declared_semantics": "creative fixture",
            }
        ],
    )
    brief = create_creative_brief(project)
    return brief.snapshot_sha256, result.ingestion.chunks[0].chunk_id


def _confirm_requirements(project: Path) -> None:
    path = project / "AD-creative/orchestrator/requirements.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    for index, row in enumerate(rows, start=1):
        confirmation_ref = _append_confirmation_event(
            project,
            event_id=f"CONFIRM-REQ-{index:03d}",
            authority_class="user",
            semantics="creative_requirement_confirmation",
            affects_requirements={row["requirement_id"]},
        )
        confirm_creative_requirement(
            project,
            row["requirement_id"],
            confirmation_ref=confirmation_ref,
        )


def _prepare_hard_constraints(
    project: Path, *, confirm: bool = True
) -> tuple[str, str]:
    ensure_project(project)
    source = project / "hard-constraint-brief.md"
    source.write_text(
        "\n".join(
            [
                "视频时长必须控制在20秒以内。",
                "最多2位演员。",
                "拍摄只能在公寓客厅和便利店门口。",
                "必须有真实产品露出。",
                "不得使用睡眠、醒酒、减肥、健康或医疗宣称。",
            ]
        ),
        encoding="utf-8",
    )
    result = run_evidence_intake(
        project,
        [
            {
                "source_event_id": "SRC-HARD-001",
                "file_paths": source.name,
                "declared_semantics": "hard-constraint fixture",
            }
        ],
    )
    if confirm:
        _confirm_requirements(project)
    brief = create_creative_brief(project)
    return brief.snapshot_sha256, result.ingestion.chunks[0].chunk_id


def _direction(number: int, evidence_ref: str) -> dict[str, object]:
    values: dict[str, object] = {
        "direction_id": f"DIR-{number:02d}",
        "name": "雨线显形" if number == 1 else "收纳时刻",
        "human_tension": "通勤者不相信泛泛的防水承诺，只相信眼前可见的具体变化。",
        "brand_truth": "品牌的三层防水结构和可收纳设计均由已绑定资料支持。",
        "audience_truth": "城市通勤人群会在出门前快速判断装备是否值得携带。",
        "single_minded_proposition": "让防护价值在真实动作中被看见。",
        "creative_mechanism": "雨滴路径实时显形" if number == 1 else "一镜到底折叠收纳",
        "key_visual": "雨水沿夹克表面形成清晰分流线并在胸前定格。" if number == 1 else "夹克从穿着状态连续折叠进入通勤包侧袋。",
        "story_or_behavior": "镜头跟随通勤者穿过雨幕，防护效果通过连续动作而非旁白完成证明。" if number == 1 else "镜头从办公室门口跟随人物收纳夹克并切换到周末步道使用。",
        "product_role": "产品是完成防护或收纳动作的因果核心，不是背景道具。",
        "channel_execution": "15 秒竖屏视频与一张动作中段关键视觉。",
        "why_brand_can_own_it": "该机制直接依赖资料中已确认的三层面料与可收纳结构，替换普通品牌后因果链会失效。",
        "production_risk": "需要可控降雨、连续动作排练和面料反光测试。",
        "evidence_refs": [evidence_ref],
        "runtime_seconds": 15,
        "cast_count": 1,
        "locations": ["办公室门口", "周末步道"],
        "product_exposure": {
            "physical_product_visible": True,
            "description": "真实夹克持续出镜并展示防水或收纳动作。",
        },
        "claims": [],
    }
    assert set(values) == set(CREATIVE_DIRECTION_FIELDS)
    return values


def _hard_constraint_direction(number: int, evidence_ref: str) -> dict[str, object]:
    values = _direction(number, evidence_ref)
    values.update(
        {
            "key_visual": "便利店门口出现真实产品罐身特写，包装在画面中央清晰可见。",
            "story_or_behavior": "两位演员在便利店门口拿起真实产品，随后回到公寓客厅开罐饮用。",
            "channel_execution": "抖音和小红书使用18秒竖屏视频，保留产品特写。",
            "production_risk": "两位演员、两个许可场景和真实产品均需在拍摄前确认。",
            "runtime_seconds": 18,
            "cast_count": 2,
            "locations": ["便利店门口", "公寓客厅"],
            "product_exposure": {
                "physical_product_visible": True,
                "description": "真实产品罐身在画面中央特写，演员拿起并开罐饮用。",
            },
            "claims": [],
        }
    )
    return values


def _assert_import_rejected_without_persistence(
    project: Path, candidate_path: Path, expected_error: str
) -> None:
    protected = [
        project / CURRENT_CANDIDATE_REL,
        project / CANDIDATE_IMPORT_RECEIPT_REL,
        project / CREATIVE_DIRECTIONS_REL,
        project / OPTION_MATRIX_REL,
    ]
    before = {
        path: path.read_bytes() if path.is_file() else None
        for path in protected
    }
    versions_before = sorted(
        path.name
        for path in (project / CREATIVE_ROOT / "candidates").glob("candidate_v*.json")
    )
    try:
        import_creative_candidate(project, candidate_path)
    except ValueError as exc:
        assert expected_error in str(exc), str(exc)
    else:
        raise AssertionError(f"creative import must fail: {expected_error}")
    after = {
        path: path.read_bytes() if path.is_file() else None
        for path in protected
    }
    versions_after = sorted(
        path.name
        for path in (project / CREATIVE_ROOT / "candidates").glob("candidate_v*.json")
    )
    assert after == before
    assert versions_after == versions_before


def test_brief_generates_contracts_not_directions() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-brief-") as raw:
        project = Path(raw)
        snapshot_sha, _ = _prepare(project)
        assert (project / BRIEF_SNAPSHOT_REL).is_file()
        assert (project / BRIEF_CONTRACT_REL).is_file()
        assert (project / CANDIDATE_SCHEMA_REL).is_file()
        assert not (project / CURRENT_CANDIDATE_REL).exists()
        payload = render_creative_proposal(project)
        assert payload["directions_generated"] == 0
        assert payload["deprecated_alias"] == "creative-brief"
        assert "ART-AUTO-CREATIVE-DIRECTIONS" not in payload["artifact_ids"]
        snapshot = json.loads((project / BRIEF_SNAPSHOT_REL).read_text(encoding="utf-8"))
        assert snapshot["brief_snapshot_sha256"] == snapshot_sha


def test_candidate_requires_evidence_and_distinct_mechanisms() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-candidate-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare(project)
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [_direction(1, evidence_ref), _direction(2, evidence_ref)],
        }
        candidate_path = project / "candidate.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
        imported = import_creative_candidate(project, candidate_path)
        assert imported.direction_count == 2
        review = review_creative_candidate(project, independent_critic_required=True)
        assert review.status == "PARTIAL_PASS"
        assert review.receipt["independent_critic_required"] is True
        assert review.receipt["creative_quality"] == "NOT_APPROVED_BY_DETERMINISTIC_LINT"
        for direction_id in ["DIR-01", "DIR-02"]:
            assert review.receipt["evidence_traceability"][direction_id]["status"] == (
                "PROVENANCE_ONLY"
            )
            assert "semantic claim support is not verified" in review.receipt[
                "evidence_traceability"
            ][direction_id]["reason"]
            assert review.receipt["brief_adherence"][direction_id]["status"] == (
                "NOT_APPLICABLE"
            )
        for field in [
            "brief_adherence",
            "insight_quality",
            "brand_ownership",
            "mechanism_difference",
            "key_visual_clarity",
            "shootability",
            "production_risk",
            "brand_replacement_test",
            "verdict",
        ]:
            assert field in review.receipt

        review.receipt_path.unlink()
        content_review = review_creative_candidate(
            project,
            independent_critic_required=False,
        )
        assert content_review.status == "PARTIAL_PASS"
        assert content_review.receipt_path is None
        assert not review.receipt_path.exists()
        assert content_review.receipt["independent_critic_required"] is False
        assert content_review.receipt["verdict"] == (
            "STRUCTURE_PASS_HUMAN_JUDGMENT_REQUIRED"
        )

        duplicate = copy.deepcopy(candidate)
        duplicate["directions"][1]["creative_mechanism"] = duplicate["directions"][0][
            "creative_mechanism"
        ]
        duplicate_path = project / "duplicate.json"
        duplicate_path.write_text(json.dumps(duplicate, ensure_ascii=False), encoding="utf-8")
        try:
            import_creative_candidate(project, duplicate_path)
        except ValueError as exc:
            assert "duplicate creative mechanism" in str(exc)
        else:
            raise AssertionError("duplicate creative mechanisms must fail")

        unbound = copy.deepcopy(candidate)
        unbound["directions"][0]["evidence_refs"] = ["EVC-NOT-REAL"]
        unbound_path = project / "unbound.json"
        unbound_path.write_text(json.dumps(unbound, ensure_ascii=False), encoding="utf-8")
        try:
            import_creative_candidate(project, unbound_path)
        except ValueError as exc:
            assert "evidence_refs" in str(exc)
        else:
            raise AssertionError("unbound creative evidence must fail")


def test_hard_constraints_are_semantically_checked_and_fail_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-hard-constraints-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare_hard_constraints(project)
        contract = json.loads((project / BRIEF_CONTRACT_REL).read_text(encoding="utf-8"))
        assert contract["contract_version"] == "1.1"
        assert {item["kind"] for item in contract["hard_constraints"]} == {
            "runtime_max_seconds",
            "cast_max",
            "location_allowlist",
            "product_exposure_required",
            "prohibited_claims",
        }
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [
                _hard_constraint_direction(1, evidence_ref),
                _hard_constraint_direction(2, evidence_ref),
            ],
        }
        candidate_path = project / "hard-constraint-candidate.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
        import_creative_candidate(project, candidate_path)
        review = review_creative_candidate(project)
        assert review.status == "PARTIAL_PASS", review.receipt
        assert not review.blocking_issues
        for direction_id in ["DIR-01", "DIR-02"]:
            assert review.receipt["brief_adherence"][direction_id]["status"] == "PASS"
            checks = review.receipt["brief_constraint_checks"][direction_id]
            assert {item["status"] for item in checks.values()} == {"PASS"}

        timeline = copy.deepcopy(candidate)
        timeline["directions"][0]["story_or_behavior"] = (
            "前2秒，两位演员在便利店门口拿起真实产品；随后一人特写，"
            "再回到公寓客厅完成聊天和开罐动作。"
        )
        timeline["directions"][0]["channel_execution"] = (
            "总时长为18秒的竖屏视频；0–2s 建立关系，3秒特写产品。"
        )
        timeline_path = project / "timeline-and-single-shot.json"
        timeline_path.write_text(
            json.dumps(timeline, ensure_ascii=False), encoding="utf-8"
        )
        import_creative_candidate(project, timeline_path)
        timeline_review = review_creative_candidate(project)
        assert timeline_review.receipt["brief_adherence"]["DIR-01"]["status"] == (
            "PASS"
        ), timeline_review.receipt

        explicit_runtime_conflict = copy.deepcopy(candidate)
        explicit_runtime_conflict["directions"][0]["channel_execution"] = (
            "总时长为19秒的竖屏视频，保留产品特写。"
        )
        explicit_runtime_path = project / "explicit-runtime-conflict.json"
        explicit_runtime_path.write_text(
            json.dumps(explicit_runtime_conflict, ensure_ascii=False),
            encoding="utf-8",
        )
        _assert_import_rejected_without_persistence(
            project, explicit_runtime_path, "runtime_max_seconds"
        )

        explicit_cast_conflict = copy.deepcopy(candidate)
        explicit_cast_conflict["directions"][0]["story_or_behavior"] = (
            "全片共三位演员，先在便利店门口拿起真实产品，随后回到公寓客厅。"
        )
        explicit_cast_path = project / "explicit-cast-conflict.json"
        explicit_cast_path.write_text(
            json.dumps(explicit_cast_conflict, ensure_ascii=False),
            encoding="utf-8",
        )
        _assert_import_rejected_without_persistence(
            project, explicit_cast_path, "cast_max"
        )

        cases = [
            (
                "runtime_max_seconds",
                "channel_execution",
                "抖音和小红书使用25秒竖屏视频，保留产品特写。",
                "FAIL",
                {"runtime_seconds": 25},
            ),
            (
                "cast_max",
                "story_or_behavior",
                "三位演员在便利店门口拿起真实产品，随后回到公寓客厅开罐饮用。",
                "FAIL",
                {"cast_count": 3},
            ),
            (
                "location_allowlist",
                "story_or_behavior",
                "两位演员从便利店冷柜拿起真实产品，随后回到公寓客厅开罐饮用。",
                "FAIL",
                {"locations": ["便利店冷柜", "公寓客厅"]},
            ),
            (
                "product_exposure_required",
                "key_visual",
                "便利店门口的两位人物交换眼神，画面转入公寓客厅。",
                "FAIL",
                {
                    "product_exposure": {
                        "physical_product_visible": False,
                        "description": "产品不出镜，演员喝白水。",
                    }
                },
            ),
            (
                "prohibited_claims",
                "single_minded_proposition",
                "帮助睡眠，让明天更轻松。",
                "FAIL",
                {"claims": ["帮助睡眠"]},
            ),
        ]
        for kind, field, replacement, _expected, structured_updates in cases:
            broken = copy.deepcopy(candidate)
            broken["directions"][0][field] = replacement
            broken["directions"][0].update(structured_updates)
            if kind == "product_exposure_required":
                broken["directions"][0]["story_or_behavior"] = (
                    "两位演员从便利店门口走到公寓客厅，完成一次简短会面。"
                )
                broken["directions"][0]["channel_execution"] = "抖音和小红书使用18秒竖屏视频。"
            broken_path = project / f"broken-{kind}.json"
            broken_path.write_text(
                json.dumps(broken, ensure_ascii=False), encoding="utf-8"
            )
            _assert_import_rejected_without_persistence(project, broken_path, kind)

        hostile_cases = [
            (
                "unknown museum prose location",
                {"story_or_behavior": "两位演员先在公寓客厅，随后转场到美术馆。"},
                "location_allowlist",
            ),
            (
                "unknown school entrance prose location",
                {"story_or_behavior": "两位演员先在学校门口，随后回到公寓客厅。"},
                "location_allowlist",
            ),
            (
                "interior fixture relabeled as entrance",
                {"story_or_behavior": "两位演员在便利店门口打开冰柜门，取出真实产品。"},
                "location_allowlist",
            ),
            (
                "unlisted kitchen action relabeled as living room",
                {"story_or_behavior": "两位演员在公寓客厅打开冰箱取出真实产品。"},
                "location_allowlist",
            ),
            (
                "unknown bathroom prose location",
                {"story_or_behavior": "两位演员先在卫生间整理造型，随后回到公寓客厅。"},
                "location_allowlist",
            ),
            (
                "unknown warehouse prose location",
                {"story_or_behavior": "两位演员先在仓库取货，随后到便利店门口会面。"},
                "location_allowlist",
            ),
            (
                "negated product exposure",
                {
                    "story_or_behavior": "产品不出镜，演员喝白水。",
                    "product_exposure": {
                        "physical_product_visible": True,
                        "description": "产品不出镜，演员喝白水。",
                    },
                },
                "product_exposure_required",
            ),
            (
                "sleep synonym",
                {"single_minded_proposition": "一夜好眠，让明天更轻松。"},
                "prohibited_claims",
            ),
            (
                "clear headed socializing synonym",
                {"single_minded_proposition": "A clear-headed socializing choice for tonight."},
                "prohibited_claims",
            ),
            (
                "sober socializing synonym",
                {"single_minded_proposition": "Own sober socializing without compromise."},
                "prohibited_claims",
            ),
            (
                "chinese clear socializing synonym",
                {"single_minded_proposition": "把清醒社交变成今晚的新选择。"},
                "prohibited_claims",
            ),
            (
                "low burden socializing synonym",
                {"single_minded_proposition": "Low-burden socializing for modern nights."},
                "prohibited_claims",
            ),
            (
                "chinese low burden synonym",
                {"single_minded_proposition": "主打低负担社交的新生活方式。"},
                "prohibited_claims",
            ),
            (
                "wellness choice synonym",
                {"single_minded_proposition": "The wellness choice for every gathering."},
                "prohibited_claims",
            ),
            (
                "no substring inside innovation",
                {"single_minded_proposition": "Innovation sleep benefit for tomorrow."},
                "prohibited_claims",
            ),
        ]
        for label, updates, failed_kind in hostile_cases:
            broken = copy.deepcopy(candidate)
            broken["directions"][0].update(updates)
            broken_path = project / (label.replace(" ", "-") + ".json")
            broken_path.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
            _assert_import_rejected_without_persistence(
                project, broken_path, failed_kind
            )

        product_language_only = copy.deepcopy(candidate)
        product_language_only["directions"][0].update(
            {
                "key_visual": "纯色字幕卡与人物眼神切换，没有实物画面。",
                "story_or_behavior": "We can open on a title card and can show a mood transition.",
                "channel_execution": "The director can hold the beat for an 18-second vertical cut.",
                "product_exposure": {
                    "physical_product_visible": True,
                    "description": "We can open softly, can show the mood, and can hold the final beat.",
                },
            }
        )
        product_language_path = project / "generic-can-verbs-are-not-product.json"
        product_language_path.write_text(
            json.dumps(product_language_only, ensure_ascii=False), encoding="utf-8"
        )
        _assert_import_rejected_without_persistence(
            project, product_language_path, "product_exposure_required"
        )

        conceptual_product = copy.deepcopy(product_language_only)
        conceptual_product["directions"][0]["story_or_behavior"] = (
            "产品策略可以展示年轻人的聚会情绪，但镜头只有人物剪影。"
        )
        conceptual_product["directions"][0]["product_exposure"]["description"] = (
            "产品概念展示在文案策略中，画面只保留人物剪影。"
        )
        conceptual_product_path = project / "product-strategy-is-not-exposure.json"
        conceptual_product_path.write_text(
            json.dumps(conceptual_product, ensure_ascii=False), encoding="utf-8"
        )
        _assert_import_rejected_without_persistence(
            project, conceptual_product_path, "product_exposure_required"
        )

        for negated_statement in (
            "本方向不出现睡眠结果，只讲产品口味。",
            "本方向没有睡眠宣称，只讲产品口味。",
            "This direction does not claim sleep benefits; it only shows taste.",
            "本方向不宣称清醒社交或低负担社交，只讲产品口味。",
            "This is not a wellness choice and does not claim sober socializing; it only shows taste.",
        ):
            negated = copy.deepcopy(candidate)
            negated["directions"][0]["single_minded_proposition"] = negated_statement
            negated_path = project / "negated-claim.json"
            negated_path.write_text(json.dumps(negated, ensure_ascii=False), encoding="utf-8")
            import_creative_candidate(project, negated_path)
            negated_review = review_creative_candidate(project)
            claim_check = negated_review.receipt["brief_constraint_checks"]["DIR-01"]
            constraint_id = next(key for key in claim_check if key.endswith(":prohibited_claims"))
            assert claim_check[constraint_id]["status"] == "PASS", (
                negated_statement,
                claim_check,
            )


def test_unconfirmed_and_unsupported_hard_requirements_block_before_write() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-unconfirmed-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare_hard_constraints(
            project, confirm=False
        )
        contract = json.loads((project / BRIEF_CONTRACT_REL).read_text(encoding="utf-8"))
        assert contract["hard_constraints"]
        assert all(
            item["authority"]["authoritative"] is False
            for item in contract["hard_constraints"]
        )
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [_hard_constraint_direction(1, evidence_ref)],
        }
        candidate_path = project / "unconfirmed.json"
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False), encoding="utf-8"
        )
        _assert_import_rejected_without_persistence(
            project, candidate_path, "unconfirmed requirement authority"
        )

    with tempfile.TemporaryDirectory(prefix="adco-creative-manual-hard-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "manual-hard.md"
        source.write_text(
            "必须一天拍完。\n禁止任何虚构数据。",
            encoding="utf-8",
        )
        intake = run_evidence_intake(
            project,
            [
                {
                    "source_event_id": "SRC-MANUAL-001",
                    "file_paths": source.name,
                    "declared_semantics": "manual hard constraint fixture",
                }
            ],
        )
        _confirm_requirements(project)
        brief = create_creative_brief(project)
        contract = json.loads((project / BRIEF_CONTRACT_REL).read_text(encoding="utf-8"))
        assert {item["kind"] for item in contract["hard_constraints"]} == {
            "manual_review"
        }
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": brief.snapshot_sha256,
            "directions": [_direction(1, intake.ingestion.chunks[0].chunk_id)],
        }
        candidate_path = project / "manual-review-required.json"
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False), encoding="utf-8"
        )
        _assert_import_rejected_without_persistence(
            project, candidate_path, "no deterministic checker"
        )


def test_product_exposure_negation_is_not_reversed() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-no-product-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "no-product.md"
        source.write_text("必须避免产品露出。", encoding="utf-8")
        intake = run_evidence_intake(
            project,
            [
                {
                    "source_event_id": "SRC-NO-PRODUCT-001",
                    "file_paths": source.name,
                    "declared_semantics": "product exposure prohibition fixture",
                }
            ],
        )
        _confirm_requirements(project)
        brief = create_creative_brief(project)
        contract = json.loads((project / BRIEF_CONTRACT_REL).read_text(encoding="utf-8"))
        constraint = next(
            item
            for item in contract["hard_constraints"]
            if item["kind"] == "product_exposure_required"
        )
        assert constraint["value"] is False

        direction = _direction(1, intake.ingestion.chunks[0].chunk_id)
        direction["key_visual"] = "雨滴沿玻璃流动，人物影子在背景中缓慢经过。"
        direction["story_or_behavior"] = "人物只通过环境和动作表达选择，镜头保持克制。"
        direction["channel_execution"] = "15秒竖屏氛围短片。"
        direction["product_exposure"] = {
            "physical_product_visible": False,
            "description": "画面仅包含环境与人物动作。",
        }
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": brief.snapshot_sha256,
            "directions": [direction],
        }
        candidate_path = project / "no-product-candidate.json"
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False), encoding="utf-8"
        )
        import_creative_candidate(project, candidate_path)
        review = review_creative_candidate(project)
        assert review.receipt["brief_adherence"]["DIR-01"]["status"] == "PASS"

        violating = copy.deepcopy(candidate)
        violating["directions"][0]["product_exposure"] = {
            "physical_product_visible": True,
            "description": "真实产品包装出镜并展示。",
        }
        violating_path = project / "product-visible.json"
        violating_path.write_text(
            json.dumps(violating, ensure_ascii=False), encoding="utf-8"
        )
        _assert_import_rejected_without_persistence(
            project, violating_path, "product_exposure_required"
        )


def test_direction_count_matches_request_without_forced_critic() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-count-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "one-direction-brief.md"
        source.write_text("本轮只要1个创意方向，不需要独立 Critic。", encoding="utf-8")
        intake = run_evidence_intake(
            project,
            [{"source_event_id": "SRC-COUNT-001", "file_paths": source.name, "declared_semantics": "count fixture"}],
        )
        brief = create_creative_brief(project)
        contract = json.loads((project / BRIEF_CONTRACT_REL).read_text(encoding="utf-8"))
        schema = json.loads((project / CANDIDATE_SCHEMA_REL).read_text(encoding="utf-8"))
        assert contract["candidate_contract"]["requested_direction_count"] == 1
        assert contract["candidate_contract"]["critic_required_by_brief"] is False
        assert schema["properties"]["directions"]["minItems"] == 1
        assert schema["properties"]["directions"]["maxItems"] == 1
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": brief.snapshot_sha256,
            "directions": [_direction(1, intake.ingestion.chunks[0].chunk_id)],
        }
        candidate_path = project / "one-direction.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
        imported = import_creative_candidate(project, candidate_path)
        assert imported.direction_count == 1
        review = review_creative_candidate(project)
        assert review.receipt_path is None
        assert review.receipt["independent_critic_required"] is False


def test_common_english_prohibited_claim_phrase_is_extracted() -> None:
    assert _prohibited_claims(
        "Must not make sleep, sobering, weight-loss, health, or medical claims."
    ) == ["sleep", "sobering", "weight-loss", "health", "medical"]


def test_candidate_receipt_never_reuses_a_version_with_different_bytes() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-version-binding-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare(project)
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [_direction(1, evidence_ref), _direction(2, evidence_ref)],
        }
        candidate_path = project / "candidate.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
        first = import_creative_candidate(project, candidate_path)
        first_payload_digest = payload_sha256(candidate)
        first.candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=4) + "\n\n",
            encoding="utf-8",
        )
        assert json.loads(first.candidate_path.read_text(encoding="utf-8")) == candidate
        assert payload_sha256(
            json.loads(first.candidate_path.read_text(encoding="utf-8"))
        ) == first_payload_digest
        second = import_creative_candidate(project, candidate_path)
        assert second.candidate_path != first.candidate_path
        assert second.candidate_path.name == "candidate_v002.json"
        persisted = json.loads(second.candidate_path.read_text(encoding="utf-8"))
        assert persisted == candidate
        receipt = json.loads(second.receipt_path.read_text(encoding="utf-8"))
        assert receipt["candidate_path"].endswith("candidate_v002.json")
        assert receipt["candidate_sha256"] == second.candidate_sha256
        assert receipt["candidate_sha256"] == file_sha256(second.candidate_path)
        assert receipt["candidate_payload_sha256"] == first_payload_digest
        assert receipt["candidate_byte_length"] == len(second.candidate_path.read_bytes())


def test_brief_manifest_self_hash_and_current_truth_are_fail_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-brief-integrity-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare(project)
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [_direction(1, evidence_ref)],
        }
        candidate_path = project / "candidate.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")

        snapshot_path = project / BRIEF_SNAPSHOT_REL
        manifest_path = project / BRIEF_MANIFEST_REL
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["brief_snapshot_sha256"] = "0" * 64
        snapshot_bytes = (
            json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        snapshot_path.write_bytes(snapshot_bytes)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["brief_snapshot_sha256"] = "0" * 64
        manifest["artifacts"][BRIEF_SNAPSHOT_REL.as_posix()] = {
            "sha256": __import__("hashlib").sha256(snapshot_bytes).hexdigest(),
            "byte_length": len(snapshot_bytes),
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _assert_import_rejected_without_persistence(
            project,
            candidate_path,
            "snapshot self-hash mismatch",
        )

    with tempfile.TemporaryDirectory(prefix="adco-creative-brief-stale-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare(project)
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [_direction(1, evidence_ref)],
        }
        candidate_path = project / "candidate.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
        requirements_path = project / "AD-creative/orchestrator/requirements.csv"
        requirements_path.write_text(
            requirements_path.read_text(encoding="utf-8").replace(
                "可编辑广告提案", "可编辑广告提案并补一张KV"
            ),
            encoding="utf-8",
        )
        _assert_import_rejected_without_persistence(
            project,
            candidate_path,
            "creative brief is stale against current",
        )


def test_review_requires_exact_current_version_and_import_receipt_chain() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-review-binding-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare(project)
        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [_direction(1, evidence_ref), _direction(2, evidence_ref)],
        }
        candidate_path = project / "candidate.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
        imported = import_creative_candidate(project, candidate_path)
        assert review_creative_candidate(project).status == "PARTIAL_PASS"

        receipt_path = project / CANDIDATE_IMPORT_RECEIPT_REL
        receipt_bytes = receipt_path.read_bytes()
        receipt = json.loads(receipt_bytes)
        receipt["candidate_sha256"] = "f" * 64
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
        try:
            review_creative_candidate(project)
        except ValueError as exc:
            assert "version hash does not match" in str(exc), str(exc)
        else:
            raise AssertionError("review must reject a tampered import receipt")
        receipt_path.write_bytes(receipt_bytes)

        version_bytes = imported.candidate_path.read_bytes()
        imported.candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )
        try:
            review_creative_candidate(project)
        except ValueError as exc:
            assert "current creative candidate bytes do not match receipt version" in str(exc)
        else:
            raise AssertionError("review must reject semantically equal but byte-different version")
        imported.candidate_path.write_bytes(version_bytes)
        assert review_creative_candidate(project).status == "PARTIAL_PASS"


def test_human_requirement_confirmation_and_manual_constraint_resolution() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-human-resolution-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "manual-hard.md"
        source.write_text("必须一天拍完。", encoding="utf-8")
        intake = run_evidence_intake(
            project,
            [
                {
                    "source_event_id": "SRC-MANUAL-RESOLVE-001",
                    "file_paths": source.name,
                    "declared_semantics": "manual constraint resolution fixture",
                }
            ],
        )

        # A hand-edited status has no matching receipt and remains non-authoritative.
        requirements_path = project / "AD-creative/orchestrator/requirements.csv"
        with requirements_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = list(reader.fieldnames or [])
            rows = [dict(row) for row in reader]
        rows[0]["status"] = "confirmed"
        rows[0]["confirmed_by"] = "Fixture Human Reviewer"
        rows[0]["confirmed_at"] = "2026-07-22T00:00:00+08:00"
        with requirements_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        untrusted_brief = create_creative_brief(project)
        untrusted_contract = json.loads(
            (project / BRIEF_CONTRACT_REL).read_text(encoding="utf-8")
        )
        assert untrusted_contract["hard_constraints"][0]["authority"]["authoritative"] is False

        try:
            confirm_creative_requirement(
                project,
                rows[0]["requirement_id"],
                confirmation_ref="Fixture Human Reviewer",
            )
        except ValueError as exc:
            assert "confirmation_ref must be" in str(exc)
        else:
            raise AssertionError("a free-text reviewer name must never confer authority")

        requirement_confirmation_ref = _append_confirmation_event(
            project,
            event_id="CONFIRM-MANUAL-REQ-001",
            authority_class="client",
            semantics="creative_requirement_confirmation",
            affects_requirements={rows[0]["requirement_id"]},
        )
        confirmation = confirm_creative_requirement(
            project,
            rows[0]["requirement_id"],
            confirmation_ref=requirement_confirmation_ref,
        )
        assert confirmation.receipt["evidence_ref"] == intake.ingestion.chunks[0].chunk_id
        brief = create_creative_brief(project)
        assert brief.snapshot_sha256 != untrusted_brief.snapshot_sha256
        contract = json.loads((project / BRIEF_CONTRACT_REL).read_text(encoding="utf-8"))
        constraint = contract["hard_constraints"][0]
        assert constraint["kind"] == "manual_review"
        assert constraint["authority"]["authoritative"] is True

        candidate = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": brief.snapshot_sha256,
            "directions": [_direction(1, intake.ingestion.chunks[0].chunk_id)],
        }
        candidate_path = project / "manual-candidate.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
        _assert_import_rejected_without_persistence(
            project,
            candidate_path,
            "no deterministic checker",
        )
        constraint_confirmation_ref = _append_confirmation_event(
            project,
            event_id="CONFIRM-MANUAL-CONSTRAINT-001",
            authority_class="user",
            semantics="creative_constraint_approval",
            affects_requirements={constraint["requirement_id"]},
            affects_artifacts={
                f"candidate_payload_sha256:{payload_sha256(candidate)}",
                f"brief_snapshot_sha256:{candidate['brief_snapshot_sha256']}",
                "direction_id:DIR-01",
                f"constraint_id:{constraint['constraint_id']}",
            },
        )
        with (
            project / "AD-creative/orchestrator/source_events.csv"
        ).open(newline="", encoding="utf-8") as handle:
            control_event = next(
                row
                for row in csv.DictReader(handle)
                if row["source_event_id"] == "CONFIRM-MANUAL-CONSTRAINT-001"
            )
        control_intake = _run_evidence_intake_impl(project, [control_event])
        assert control_intake.ingestion.chunks == []
        resolution = resolve_creative_constraint(
            project,
            candidate_path,
            direction_id="DIR-01",
            constraint_id=constraint["constraint_id"],
            confirmation_ref=constraint_confirmation_ref,
            decision="approved",
            note="Production plan and call sheet were reviewed; the direction fits one shoot day.",
        )
        assert resolution.resolution["decision"] == "approved"
        import_creative_candidate(project, candidate_path)
        assert review_creative_candidate(project).receipt["brief_adherence"]["DIR-01"]["status"] == "PASS"

        changed = copy.deepcopy(candidate)
        changed["directions"][0]["production_risk"] += " 已变更。"
        changed_path = project / "changed-manual-candidate.json"
        changed_path.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
        _assert_import_rejected_without_persistence(
            project,
            changed_path,
            "no deterministic checker",
        )

        constraint_evidence = (
            project / "confirmations/CONFIRM-MANUAL-CONSTRAINT-001.md"
        )
        constraint_evidence.write_text("tampered confirmation\n", encoding="utf-8")
        stale_review = review_creative_candidate(project)
        assert stale_review.blocking_issues
        assert (
            stale_review.receipt["brief_adherence"]["DIR-01"]["status"]
            == "REVIEW_REQUIRED"
        )


def test_typed_confirmation_rejects_wrong_authority_and_binding() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-confirmation-authority-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "authority-brief.md"
        source.write_text("视频时长必须控制在20秒以内。", encoding="utf-8")
        run_evidence_intake(
            project,
            [
                {
                    "source_event_id": "SRC-AUTHORITY-001",
                    "file_paths": source.name,
                    "declared_semantics": "authority fixture",
                }
            ],
        )
        requirements_path = project / "AD-creative/orchestrator/requirements.csv"
        with requirements_path.open(newline="", encoding="utf-8") as handle:
            requirement = next(csv.DictReader(handle))
        confirmation_ref = _append_confirmation_event(
            project,
            event_id="CONFIRM-AUTHORITY-001",
            authority_class="user",
            semantics="creative_requirement_confirmation",
            affects_requirements={requirement["requirement_id"]},
        )
        source_events_path = project / "AD-creative/orchestrator/source_events.csv"
        with source_events_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = list(reader.fieldnames or [])
            rows = [dict(row) for row in reader]
        confirmation_row = next(
            row for row in rows if row["source_event_id"] == "CONFIRM-AUTHORITY-001"
        )

        for field, forged_value, expected_error in (
            ("source_owner", "Fixture Human Reviewer", "source_owner must be user"),
            ("source_type", "file", "source_type must be user_confirmation"),
            ("trust_level", "human_reviewed", "trust_level must be user_confirmed"),
            ("affects_requirements", "REQ-NOT-TARGET", "must exactly bind"),
        ):
            original = confirmation_row[field]
            confirmation_row[field] = forged_value
            with source_events_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            try:
                confirm_creative_requirement(
                    project,
                    requirement["requirement_id"],
                    confirmation_ref=confirmation_ref,
                )
            except ValueError as exc:
                assert expected_error in str(exc), str(exc)
            else:
                raise AssertionError(f"forged confirmation field must fail: {field}")
            confirmation_row[field] = original


def test_anchored_project_io_resists_symlink_swap_races() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-safe-write-race-") as raw:
        root = Path(raw)
        project = root / "project"
        target_parent = project / "AD-creative/race"
        outside = root / "outside"
        target_parent.mkdir(parents=True)
        outside.mkdir()
        target = target_parent / "truth.json"
        secret = outside / "secret.json"
        target.write_bytes(b"SAFE")
        target.chmod(0o644)
        secret.write_bytes(b"EXTERNAL_SECRET")
        stop = threading.Event()
        attacker_errors: list[BaseException] = []

        def swap_target() -> None:
            try:
                while not stop.is_set():
                    try:
                        target.unlink()
                    except FileNotFoundError:
                        pass
                    try:
                        os.symlink(secret, target)
                    except FileExistsError:
                        pass
                    try:
                        target.unlink()
                    except FileNotFoundError:
                        pass
                    try:
                        descriptor = os.open(
                            target,
                            os.O_WRONLY
                            | os.O_CREAT
                            | os.O_EXCL
                            | getattr(os, "O_NOFOLLOW", 0),
                            0o644,
                        )
                    except FileExistsError:
                        continue
                    try:
                        os.write(descriptor, b"SAFE")
                    finally:
                        os.close(descriptor)
            except BaseException as exc:  # pragma: no cover - surfaced below
                attacker_errors.append(exc)

        attacker = threading.Thread(target=swap_target, daemon=True)
        attacker.start()
        try:
            for index in range(800):
                try:
                    observed = read_project_bytes(project, target)
                except (OSError, ValueError):
                    pass
                else:
                    assert observed != b"EXTERNAL_SECRET"
                try:
                    atomic_write_text(project, target, f"SAFE-{index}")
                except (OSError, ValueError):
                    pass
        finally:
            stop.set()
            attacker.join(timeout=5)
        assert not attacker.is_alive()
        assert not attacker_errors, attacker_errors
        assert secret.read_bytes() == b"EXTERNAL_SECRET"

        if target.is_symlink():
            target.unlink()
        atomic_write_text(project, target, "mode-preserved")
        target.chmod(0o644)
        atomic_write_text(project, target, "mode-still-preserved")
        assert target.stat().st_mode & 0o777 == 0o644


def test_anchored_project_read_resists_parent_directory_swap() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-safe-parent-race-") as raw:
        root = Path(raw)
        project = root / "project"
        stable_parent = project / "AD-creative/parent-race"
        parked_parent = project / "AD-creative/parent-race-parked"
        outside_parent = root / "outside-parent"
        stable_parent.mkdir(parents=True)
        outside_parent.mkdir()
        (stable_parent / "truth.txt").write_bytes(b"SAFE_PARENT")
        (outside_parent / "truth.txt").write_bytes(b"EXTERNAL_SECRET")
        stop = threading.Event()
        attacker_errors: list[BaseException] = []

        def swap_parent() -> None:
            try:
                while not stop.is_set():
                    try:
                        os.rename(stable_parent, parked_parent)
                    except OSError:
                        continue
                    try:
                        os.symlink(outside_parent, stable_parent)
                        stable_parent.unlink()
                    finally:
                        try:
                            os.rename(parked_parent, stable_parent)
                        except OSError:
                            pass
            except BaseException as exc:  # pragma: no cover - surfaced below
                attacker_errors.append(exc)

        attacker = threading.Thread(target=swap_parent, daemon=True)
        attacker.start()
        try:
            for _ in range(1600):
                try:
                    observed = read_project_bytes(
                        project, stable_parent / "truth.txt"
                    )
                except (OSError, ValueError):
                    continue
                assert observed == b"SAFE_PARENT"
        finally:
            stop.set()
            attacker.join(timeout=5)
        assert not attacker.is_alive()
        assert not attacker_errors, attacker_errors
        assert (outside_parent / "truth.txt").read_bytes() == b"EXTERNAL_SECRET"


def test_conflicting_direction_counts_and_atomic_pointer_switch_fail_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-count-conflict-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "count-conflict.md"
        source.write_text(
            "本轮只要1个创意方向。\n同时要求提供2个创意方向。",
            encoding="utf-8",
        )
        run_evidence_intake(
            project,
            [
                {
                    "source_event_id": "SRC-COUNT-CONFLICT-001",
                    "file_paths": source.name,
                    "declared_semantics": "conflicting direction count fixture",
                }
            ],
        )
        try:
            create_creative_brief(project)
        except ValueError as exc:
            assert "conflicting explicit creative direction counts" in str(exc)
        else:
            raise AssertionError("conflicting explicit direction counts must fail closed")
        assert not (project / BRIEF_MANIFEST_REL).exists()

    with tempfile.TemporaryDirectory(prefix="adco-creative-atomic-current-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare(project)
        first = {
            "candidate_version": "1.1",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [_direction(1, evidence_ref), _direction(2, evidence_ref)],
        }
        first_path = project / "first.json"
        first_path.write_text(json.dumps(first, ensure_ascii=False), encoding="utf-8")
        import_creative_candidate(project, first_path)
        current_path = project / CURRENT_CANDIDATE_REL
        old_current = current_path.read_bytes()

        second = copy.deepcopy(first)
        second["directions"][0]["name"] = "雨线显形升级"
        second["directions"][0]["creative_mechanism"] = "雨滴路径分层显形"
        second_path = project / "second.json"
        second_path.write_text(json.dumps(second, ensure_ascii=False), encoding="utf-8")

        def fail_current(project_arg: Path, path: Path, data: bytes) -> Path:
            if Path(path) == current_path:
                raise OSError("injected current pointer failure")
            return real_atomic_write_bytes(project_arg, path, data)

        with patch("adco_core.creative_contract.atomic_write_bytes", side_effect=fail_current):
            try:
                import_creative_candidate(project, second_path)
            except OSError as exc:
                assert "injected current pointer failure" in str(exc)
            else:
                raise AssertionError("fault injection must interrupt current pointer switch")
        assert current_path.read_bytes() == old_current
        try:
            review_creative_candidate(project)
        except ValueError as exc:
            assert "current creative candidate" in str(exc) and "receipt" in str(exc)
        else:
            raise AssertionError("mixed receipt/current state must fail closed")
        import_creative_candidate(project, second_path)
        assert review_creative_candidate(project).status == "PARTIAL_PASS"


def test_project_artifact_writer_rejects_nested_symlink() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-symlink-") as raw:
        project = Path(raw) / "project"
        outside = Path(raw) / "outside"
        ensure_project(project)
        outside.mkdir()
        linked = project / "AD-creative/linked-outside"
        linked.symlink_to(outside, target_is_directory=True)
        try:
            atomic_write_text(project, linked / "escaped.json", "do not write")
        except ValueError as exc:
            assert "must not be a symlink" in str(exc)
        else:
            raise AssertionError("nested symlink writes must be rejected")
        assert not (outside / "escaped.json").exists()


def main() -> int:
    test_brief_generates_contracts_not_directions()
    test_candidate_requires_evidence_and_distinct_mechanisms()
    test_hard_constraints_are_semantically_checked_and_fail_closed()
    test_unconfirmed_and_unsupported_hard_requirements_block_before_write()
    test_product_exposure_negation_is_not_reversed()
    test_direction_count_matches_request_without_forced_critic()
    test_common_english_prohibited_claim_phrase_is_extracted()
    test_candidate_receipt_never_reuses_a_version_with_different_bytes()
    test_brief_manifest_self_hash_and_current_truth_are_fail_closed()
    test_review_requires_exact_current_version_and_import_receipt_chain()
    test_human_requirement_confirmation_and_manual_constraint_resolution()
    test_typed_confirmation_rejects_wrong_authority_and_binding()
    test_conflicting_direction_counts_and_atomic_pointer_switch_fail_closed()
    test_project_artifact_writer_rejects_nested_symlink()
    test_anchored_project_io_resists_symlink_swap_races()
    test_anchored_project_read_resists_parent_directory_swap()
    print("TEST_CREATIVE_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
